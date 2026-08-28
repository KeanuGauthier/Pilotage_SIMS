"""Playwright and Zephyr Squad foundation for non-regression tests.

The module exposes ``RegressionTest`` to test scripts and acts as the command-line
orchestrator that creates a Zephyr cycle and runs one or all scripts. Configuration
is loaded from the ``.env`` file located next to this file. Python 3.9 is supported.
"""

import argparse
import contextlib
import logging
import mimetypes
import os
import re
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

import requests
from dotenv import load_dotenv
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
LOGGER = logging.getLogger("nrt")

# Compatibility constants for existing scripts.
PROJECT_ID = os.getenv("ZEPHYR_PROJECT_ID", os.getenv("PROJECT_ID", "80302"))
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
CYCLE_ID_FILE = os.getenv("CYCLE_ID_FILE", "cycle_id.txt")

STATUS_PASS = "1"
STATUS_FAIL = "2"
STATUS_IN_PROGRESS = "3"


class ConfigurationError(RuntimeError):
    """The project configuration is missing or invalid."""


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError("{} must be true or false.".format(name))


def _env_int(name: str, default: int, minimum: int = 0) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ConfigurationError("{} must be an integer.".format(name)) from exc
    if parsed < minimum:
        raise ConfigurationError(
            "{} must be at least {}.".format(name, minimum)
        )
    return parsed


def _resolve_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _safe_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return sanitized.strip("._") or "unnamed"


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded once from environment variables."""

    jira_base_url: str
    jira_token: str
    project_id: int
    version_id: str
    cycle_id_file: Path
    verify_tls: bool
    request_timeout_seconds: int
    step_results_timeout_seconds: int
    browser_channel: str
    headless: bool
    viewport_width: int
    viewport_height: int
    default_timeout_ms: int
    navigation_timeout_ms: int
    slow_mo_ms: int
    artifacts_dir: Path
    trace_mode: str
    attach_trace_on_failure: bool
    comment_limit: int
    zephyr_ui_fallback_enabled: bool
    zephyr_test_summary_url: str
    zephyr_ui_timeout_ms: int

    @classmethod
    def from_env(cls) -> "Settings":
        trace_mode = os.getenv("TRACE_MODE", "retain-on-failure").strip().lower()
        if trace_mode not in {"off", "on", "retain-on-failure"}:
            raise ConfigurationError(
                "TRACE_MODE must be off, on, or retain-on-failure."
            )

        project_id_value = os.getenv(
            "ZEPHYR_PROJECT_ID", os.getenv("PROJECT_ID", "80302")
        )
        try:
            project_id = int(project_id_value)
        except ValueError as exc:
            raise ConfigurationError("ZEPHYR_PROJECT_ID must be an integer.") from exc

        return cls(
            jira_base_url=os.getenv("JIRA_BASE_URL", "").strip().rstrip("/"),
            jira_token=os.getenv("JIRA_TOKEN", "").strip(),
            project_id=project_id,
            version_id=os.getenv("ZEPHYR_VERSION_ID", "-1").strip() or "-1",
            cycle_id_file=_resolve_path(os.getenv("CYCLE_ID_FILE", "cycle_id.txt")),
            verify_tls=_env_bool("VERIFY_TLS", True),
            request_timeout_seconds=_env_int("REQUEST_TIMEOUT_SECONDS", 30, 1),
            step_results_timeout_seconds=_env_int(
                "STEP_RESULTS_TIMEOUT_SECONDS", 10, 1
            ),
            browser_channel=os.getenv("BROWSER_CHANNEL", "msedge").strip() or "msedge",
            headless=_env_bool("HEADLESS", False),
            viewport_width=_env_int("VIEWPORT_WIDTH", 1920, 320),
            viewport_height=_env_int("VIEWPORT_HEIGHT", 1080, 240),
            default_timeout_ms=_env_int("DEFAULT_TIMEOUT_MS", 15_000, 1),
            navigation_timeout_ms=_env_int("NAVIGATION_TIMEOUT_MS", 30_000, 1),
            slow_mo_ms=_env_int("SLOW_MO_MS", 0, 0),
            artifacts_dir=_resolve_path(os.getenv("ARTIFACTS_DIR", "artifacts")),
            trace_mode=trace_mode,
            attach_trace_on_failure=_env_bool("ATTACH_TRACE_ON_FAILURE", True),
            comment_limit=_env_int("ZEPHYR_COMMENT_LIMIT", 4_000, 100),
            zephyr_ui_fallback_enabled=_env_bool(
                "ZEPHYR_UI_FALLBACK_ENABLED", False
            ),
            zephyr_test_summary_url=os.getenv(
                "ZEPHYR_TEST_SUMMARY_URL", ""
            ).strip(),
            zephyr_ui_timeout_ms=_env_int("ZEPHYR_UI_TIMEOUT_MS", 15_000, 1),
        )

    def validate_zephyr(self) -> None:
        missing = []
        if not self.jira_base_url:
            missing.append("JIRA_BASE_URL")
        if not self.jira_token:
            missing.append("JIRA_TOKEN")
        if missing:
            raise ConfigurationError(
                "Missing setting(s): {}. Update .env.".format(", ".join(missing))
            )
        if self.zephyr_ui_fallback_enabled and not self.zephyr_test_summary_url:
            raise ConfigurationError(
                "ZEPHYR_TEST_SUMMARY_URL is required when "
                "ZEPHYR_UI_FALLBACK_ENABLED=true."
            )


def read_text(file_path: Any) -> str:
    """Read a UTF-8 text file and strip surrounding whitespace."""

    return Path(file_path).read_text(encoding="utf-8").strip()


def save_cycle_id(cycle_id: Any, file_name: Any = CYCLE_ID_FILE) -> None:
    """Persist the current cycle ID for scripts launched directly."""

    path = _resolve_path(str(file_name))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(cycle_id), encoding="utf-8")


def write_error_to_file(error_message: str, base_path: Any = "") -> Path:
    """Write an error report (compatibility helper for existing tests)."""

    root = _resolve_path(str(base_path)) if base_path else PROJECT_ROOT
    error_dir = root / "errors"
    error_dir.mkdir(parents=True, exist_ok=True)
    error_path = error_dir / "error_{}.txt".format(_timestamp())
    error_path.write_text(error_message, encoding="utf-8")
    return error_path


def capture_screenshot(page: Page, name: str, base_path: Any = "") -> Path:
    """Capture a full Playwright page (compatibility helper)."""

    root = _resolve_path(str(base_path)) if base_path else PROJECT_ROOT
    screenshot_dir = root / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = screenshot_dir / "{}_{}.png".format(_safe_name(name), _timestamp())
    page.screenshot(path=str(path), full_page=True)
    return path


def extract_step_result_ids(
    stepresults_json: Sequence[Mapping[str, Any]],
) -> List[int]:
    """Return Zephyr step-result IDs in their business-step order."""

    sorted_results = sorted(stepresults_json, key=lambda item: item.get("orderId", 0))
    result_ids = []
    for result in sorted_results:
        step_result_id = result.get("id")
        if step_result_id is None:
            raise ValueError("Missing 'id' in step result: {!r}".format(result))
        result_ids.append(int(step_result_id))
    return result_ids


def _response_json(response: requests.Response) -> Any:
    if not response.content:
        return {}
    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Zephyr returned non-JSON content: {!r}".format(response.text[:500])
        ) from exc


def _find_id(payload: Any) -> Optional[int]:
    """Find an execution ID in the response shapes used by ZAPI Server/DC."""

    if isinstance(payload, dict):
        if "id" in payload and str(payload["id"]).isdigit():
            return int(payload["id"])
        for value in payload.values():
            result = _find_id(value)
            if result is not None:
                return result
    elif isinstance(payload, list):
        for value in payload:
            result = _find_id(value)
            if result is not None:
                return result
    return None


class ZephyrZapiClient:
    """Small, defensive client for Zephyr Squad Server/Data Center ZAPI."""

    def __init__(
        self,
        jira_base_url: str,
        token: str,
        timeout: int = 30,
        verify_tls: bool = True,
    ) -> None:
        if not jira_base_url or not token:
            raise ConfigurationError("The Jira URL and token are required.")
        self.jira_base_url = jira_base_url.rstrip("/")
        self.zapi_base_url = "{}/rest/zapi/latest".format(self.jira_base_url)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = verify_tls
        self.session.headers.update(
            {"Accept": "application/json", "Authorization": "Bearer {}".format(token)}
        )
        self.error_counter = 0

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "ZephyrZapiClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.request(method, url, **kwargs)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise requests.HTTPError(
                "{} {} failed with HTTP {}: {}".format(
                    method.upper(), url, response.status_code, response.text[:1_000]
                ),
                response=response,
            ) from exc
        return _response_json(response)

    def get_issue_id(self, issue_key: str) -> int:
        url = "{}/rest/api/2/issue/{}".format(self.jira_base_url, issue_key)
        data = self._request("GET", url, params={"fields": "id"})
        if not isinstance(data, dict) or data.get("id") is None:
            raise ValueError("Unexpected Jira response for {}.".format(issue_key))
        return int(data["id"])

    def create_cycle(
        self, project_id: Any, version_id: Any, name: str
    ) -> Dict[str, Any]:
        data = self._request(
            "POST",
            "{}/cycle".format(self.zapi_base_url),
            json={
                "name": name,
                "description": "Automatically created by the Playwright NRT runner",
                "projectId": str(project_id),
                "versionId": str(version_id),
            },
        )
        if not isinstance(data, dict):
            raise ValueError("Unexpected Zephyr cycle response.")
        return data

    def create_execution(
        self, issue_id: int, cycle_id: Any, project_id: int, version_id: Any = -1
    ) -> int:
        data = self._request(
            "POST",
            "{}/execution/".format(self.zapi_base_url),
            json={
                "issueId": issue_id,
                "versionId": int(version_id),
                "cycleId": int(cycle_id),
                "projectId": project_id,
            },
        )
        execution_id = _find_id(data)
        if execution_id is None:
            raise ValueError("Execution ID absent from response: {!r}".format(data))
        return execution_id

    def initialize_step_results(self, execution_id: int) -> Any:
        """Materialize step-result IDs without opening the Zephyr UI."""

        url = "{}/execution/{}".format(self.zapi_base_url, execution_id)
        return self._request("GET", url, params={"expand": "checksteps"})

    def set_global_test_state(self, execution_id: int, status: Any) -> Any:
        url = "{}/execution/{}/execute".format(self.zapi_base_url, execution_id)
        return self._request(
            "PUT", url, json={"status": str(status), "changeAssignee": False}
        )

    def list_stepresults(self, execution_id: int) -> List[Dict[str, Any]]:
        data = self._request(
            "GET",
            "{}/stepResult".format(self.zapi_base_url),
            params={"executionId": execution_id},
        )
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("stepResults", "stepresults", "results"):
                if isinstance(data.get(key), list):
                    return data[key]
        raise ValueError("Unexpected step-result response: {!r}".format(data))

    def update_step_result_fail(self, step_result_id: int, comment: str = "") -> Any:
        result = self._request(
            "PUT",
            "{}/stepResult/{}".format(self.zapi_base_url, step_result_id),
            json={"status": int(STATUS_FAIL), "comment": comment},
        )
        self.error_counter += 1
        return result

    def update_step_result_pass(self, step_result_id: int) -> Any:
        return self._request(
            "PUT",
            "{}/stepResult/{}".format(self.zapi_base_url, step_result_id),
            json={"status": int(STATUS_PASS), "comment": "SUCCESS"},
        )

    def add_issue_to_cycle(
        self, issue_key: str, cycle_id: Any, project_id: int, version_id: Any = -1
    ) -> Any:
        """Compatibility helper for scripts still using the bulk endpoint."""

        return self._request(
            "POST",
            "{}/execution/addTestsToCycle/".format(self.zapi_base_url),
            json={
                "method": 1,
                "issues": [issue_key],
                "versionId": int(version_id),
                "cycleId": int(cycle_id),
                "projectId": project_id,
            },
        )

    def add_attachment(
        self,
        entity_id: int,
        entity_type: str,
        filename: str,
        content_bytes: bytes,
        content_type: Optional[str] = None,
    ) -> Any:
        mime_type = content_type or mimetypes.guess_type(filename)[0]
        return self._request(
            "POST",
            "{}/attachment".format(self.zapi_base_url),
            params={"entityId": entity_id, "entityType": entity_type},
            headers={"X-Atlassian-Token": "no-check"},
            files={
                "file": (
                    filename,
                    content_bytes,
                    mime_type or "application/octet-stream",
                )
            },
        )


def add_attachment(
    entity_id: int,
    entity_type: str,
    filename: str,
    content_bytes: bytes,
    token: str,
) -> Any:
    """Compatibility attachment helper backed by the configured client."""

    settings = Settings.from_env()
    settings.validate_zephyr()
    with ZephyrZapiClient(
        settings.jira_base_url,
        token,
        settings.request_timeout_seconds,
        settings.verify_tls,
    ) as client:
        return client.add_attachment(
            entity_id, entity_type, filename, content_bytes
        )


def _new_browser_context(browser: Browser, settings: Settings) -> BrowserContext:
    return browser.new_context(
        viewport={"width": settings.viewport_width, "height": settings.viewport_height},
        accept_downloads=True,
    )


def force_test_execution(
    execution_id: int, cycle_id: Any, settings: Optional[Settings] = None
) -> None:
    """Initialize steps through Zephyr's UI as an opt-in compatibility fallback."""

    current = settings or Settings.from_env()
    if not current.zephyr_test_summary_url:
        raise ConfigurationError(
            "ZEPHYR_TEST_SUMMARY_URL is required for the Zephyr UI fallback."
        )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel=current.browser_channel,
            headless=current.headless,
            slow_mo=current.slow_mo_ms,
        )
        context = _new_browser_context(browser, current)
        page = context.new_page()
        page.set_default_timeout(current.zephyr_ui_timeout_ms)
        try:
            page.goto(
                current.zephyr_test_summary_url.format(
                    execution_id=execution_id, cycle_id=cycle_id
                ),
                wait_until="domcontentloaded",
            )
            with contextlib.suppress(Exception):
                page.locator('img[src="assets/asl/images/france.png"]').click(
                    timeout=2_000
                )
            page.locator("#aui-test-cycles-tab").click()
            page.locator("#version--1 .jstree-icon.jstree-ocl").click()
            page.locator("#version--1-cycle-{}".format(cycle_id)).click()
            page.locator(
                '[data-executionid="{}"] [title="Execute"]'.format(execution_id)
            ).click()
            page.wait_for_timeout(1_000)
        finally:
            context.close()
            browser.close()


@dataclass
class BrowserDiagnostics:
    console_errors: List[str] = field(default_factory=list)
    page_errors: List[str] = field(default_factory=list)
    failed_requests: List[str] = field(default_factory=list)

    def offsets(self) -> Tuple[int, int, int]:
        return (
            len(self.console_errors),
            len(self.page_errors),
            len(self.failed_requests),
        )

    def format_since(self, offsets: Tuple[int, int, int]) -> str:
        console_offset, page_offset, request_offset = offsets
        sections = []
        if self.console_errors[console_offset:]:
            sections.append(
                "Browser console errors:\n- "
                + "\n- ".join(self.console_errors[console_offset:])
            )
        if self.page_errors[page_offset:]:
            sections.append(
                "Unhandled page errors:\n- "
                + "\n- ".join(self.page_errors[page_offset:])
            )
        if self.failed_requests[request_offset:]:
            sections.append(
                "Failed network requests:\n- "
                + "\n- ".join(self.failed_requests[request_offset:])
            )
        return "\n\n".join(sections)


@dataclass
class StepOutcome:
    number: int
    name: str
    passed: bool
    zephyr_step_result_id: Optional[int]
    error_file: Optional[Path] = None
    screenshot_file: Optional[Path] = None


class RegressionTest:
    """Manage one browser, one Zephyr execution, and independent test steps.

    An exception raised inside ``with test.step(...)`` is recorded and swallowed so
    later business steps still run. An exception outside a step remains fatal.
    """

    def __init__(
        self,
        issue_key: str,
        test_name: str = "",
        settings: Optional[Settings] = None,
    ) -> None:
        self.issue_key = issue_key.strip()
        self.test_name = test_name.strip() or self.issue_key
        self.settings = settings or Settings.from_env()
        self.settings.validate_zephyr()
        if not self.issue_key:
            raise ConfigurationError("issue_key cannot be empty.")

        self.client: Optional[ZephyrZapiClient] = None
        self.execution_id: Optional[int] = None
        self.step_result_ids: List[int] = []
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.diagnostics = BrowserDiagnostics()
        self.outcomes: List[StepOutcome] = []
        self.reporting_errors: List[str] = []
        self.trace_path: Optional[Path] = None
        self._entered = False
        self._ui_fallback_used = False

        run_id = os.getenv(
            "NRT_RUN_ID", datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        )
        self.artifact_dir = (
            self.settings.artifacts_dir
            / _safe_name(run_id)
            / _safe_name(self.issue_key)
        )
        self.screenshot_dir = self.artifact_dir / "screenshots"
        self.error_dir = self.artifact_dir / "errors"
        self.trace_dir = self.artifact_dir / "traces"

    @property
    def success(self) -> bool:
        return (
            self._entered
            and bool(self.outcomes)
            and not any(not outcome.passed for outcome in self.outcomes)
            and not self.reporting_errors
        )

    @property
    def failed_step_count(self) -> int:
        return sum(not outcome.passed for outcome in self.outcomes)

    def __enter__(self) -> "RegressionTest":
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.client = ZephyrZapiClient(
            self.settings.jira_base_url,
            self.settings.jira_token,
            self.settings.request_timeout_seconds,
            self.settings.verify_tls,
        )
        try:
            cycle_id = self._resolve_cycle_id()
            issue_id = self.client.get_issue_id(self.issue_key)
            self.execution_id = self.client.create_execution(
                issue_id,
                cycle_id,
                self.settings.project_id,
                self.settings.version_id,
            )
            self.client.set_global_test_state(
                self.execution_id, STATUS_IN_PROGRESS
            )
            self._initialize_step_results(cycle_id)
            try:
                self.step_result_ids = self._wait_for_step_results()
            except RuntimeError:
                if (
                    not self.settings.zephyr_ui_fallback_enabled
                    or self._ui_fallback_used
                ):
                    raise
                LOGGER.warning(
                    "Zephyr created no step IDs; using the configured UI fallback."
                )
                force_test_execution(self.execution_id, cycle_id, self.settings)
                self._ui_fallback_used = True
                self.step_result_ids = self._wait_for_step_results()
            self._start_browser()
            self._entered = True
            LOGGER.info(
                "Started %s (%s) with %d Zephyr step(s).",
                self.test_name,
                self.issue_key,
                len(self.step_result_ids),
            )
            return self
        except Exception:
            self._mark_setup_failure()
            self._close_resources()
            raise

    def _resolve_cycle_id(self) -> str:
        cycle_from_runner = os.getenv("NRT_CYCLE_ID", "").strip()
        if cycle_from_runner:
            return cycle_from_runner
        if self.settings.cycle_id_file.is_file():
            return read_text(self.settings.cycle_id_file)
        if self.client is None:
            raise RuntimeError("Zephyr client is not initialized.")

        name = "Manual Playwright run {}".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        cycle = self.client.create_cycle(
            self.settings.project_id, self.settings.version_id, name
        )
        cycle_id = cycle.get("id")
        if cycle_id is None:
            raise ValueError("Zephyr did not return a cycle ID: {!r}".format(cycle))
        save_cycle_id(cycle_id, self.settings.cycle_id_file)
        return str(cycle_id)

    def _initialize_step_results(self, cycle_id: str) -> None:
        if self.client is None or self.execution_id is None:
            raise RuntimeError("Zephyr execution is not initialized.")
        try:
            self.client.initialize_step_results(self.execution_id)
        except Exception:
            if not self.settings.zephyr_ui_fallback_enabled:
                raise
            LOGGER.warning(
                "The Zephyr checksteps API failed; using the UI fallback."
            )
            LOGGER.debug("checksteps failure:\n%s", traceback.format_exc())
            force_test_execution(self.execution_id, cycle_id, self.settings)
            self._ui_fallback_used = True

    def _wait_for_step_results(self) -> List[int]:
        if self.client is None or self.execution_id is None:
            raise RuntimeError("Zephyr execution is not initialized.")
        deadline = time.monotonic() + self.settings.step_results_timeout_seconds
        last_error = None
        while time.monotonic() < deadline:
            try:
                result_ids = extract_step_result_ids(
                    self.client.list_stepresults(self.execution_id)
                )
                if result_ids:
                    return result_ids
            except Exception as exception:
                last_error = exception
            time.sleep(0.5)
        message = "Zephyr returned no test-step results for {} after {} seconds.".format(
            self.issue_key, self.settings.step_results_timeout_seconds
        )
        if last_error is not None:
            raise RuntimeError(message) from last_error
        raise RuntimeError(message)

    def _start_browser(self) -> None:
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            channel=self.settings.browser_channel,
            headless=self.settings.headless,
            slow_mo=self.settings.slow_mo_ms,
        )
        self.context = _new_browser_context(self.browser, self.settings)
        self.page = self.context.new_page()
        self._instrument_page(self.page)
        if self.settings.trace_mode != "off":
            self.context.tracing.start(
                screenshots=True, snapshots=True, sources=True
            )

    def _on_console(self, message: Any) -> None:
        if message.type == "error":
            self.diagnostics.console_errors.append(message.text)

    def _on_request_failed(self, request: Any) -> None:
        self.diagnostics.failed_requests.append(
            "{} {}: {}".format(
                request.method,
                request.url,
                request.failure or "Unknown network failure",
            )
        )

    def _instrument_page(self, page: Page) -> None:
        page.set_default_timeout(self.settings.default_timeout_ms)
        page.set_default_navigation_timeout(self.settings.navigation_timeout_ms)
        page.on("console", self._on_console)
        page.on(
            "pageerror", lambda error: self.diagnostics.page_errors.append(str(error))
        )
        page.on("requestfailed", self._on_request_failed)

    def use_page(self, page: Page) -> Page:
        """Use a newly opened tab as the current page for diagnostics."""

        self.page = page
        self._instrument_page(self.page)
        return page

    def _validate_step_coverage(self) -> None:
        expected = list(range(1, len(self.step_result_ids) + 1))
        actual = [outcome.number for outcome in self.outcomes]
        if actual == expected:
            return
        message = (
            "Zephyr step coverage mismatch for {}. Expected {}, executed {}."
        ).format(self.issue_key, expected, actual)
        if message not in self.reporting_errors:
            self.reporting_errors.append(message)
        LOGGER.error(message)

    def _step_result_id(self, step_number: int) -> Optional[int]:
        index = step_number - 1
        if index < 0 or index >= len(self.step_result_ids):
            message = (
                "Step {} does not exist in Zephyr test {} ({} available)."
            ).format(step_number, self.issue_key, len(self.step_result_ids))
            self.reporting_errors.append(message)
            LOGGER.error(message)
            return None
        return self.step_result_ids[index]

    @contextlib.contextmanager
    def step(self, number: int, name: str) -> Iterator[None]:
        """Run one business step and continue the scenario if it fails."""

        if not self._entered or self.page is None or self.client is None:
            raise RuntimeError("RegressionTest must be entered before running steps.")
        if not isinstance(number, int) or number < 1:
            raise ValueError("A step number must be a positive integer.")

        step_result_id = self._step_result_id(number)
        offsets = self.diagnostics.offsets()
        LOGGER.info("STEP %d - %s", number, name)
        try:
            yield
        except Exception as exception:
            self.outcomes.append(
                self._record_failed_step(
                    number, name, step_result_id, exception, offsets
                )
            )
            # Deliberate: independent following steps must still execute.
        else:
            reporting_ok = self._record_passed_step(number, name, step_result_id)
            self.outcomes.append(
                StepOutcome(number, name, reporting_ok, step_result_id)
            )

    def _record_passed_step(
        self, number: int, name: str, step_result_id: Optional[int]
    ) -> bool:
        if step_result_id is None or self.client is None:
            return False
        try:
            self.client.update_step_result_pass(step_result_id)
        except Exception:
            self._record_reporting_error(
                "Could not report PASS for step {} ({})".format(number, name)
            )
            return False
        LOGGER.info("PASS - Step %d: %s", number, name)
        return True

    def _record_failed_step(
        self,
        number: int,
        name: str,
        step_result_id: Optional[int],
        exception: Exception,
        diagnostic_offsets: Tuple[int, int, int],
    ) -> StepOutcome:
        error_text = self._build_error_report(
            number, name, exception, diagnostic_offsets
        )
        LOGGER.error("FAIL - Step %d: %s\n%s", number, name, error_text)
        screenshot_path = self._capture_failure_screenshot(number, name)
        error_path = self._write_step_error(number, name, error_text)

        if step_result_id is not None and self.client is not None:
            comment = "{}: {}\n{}".format(
                type(exception).__name__, exception, error_text
            )[: self.settings.comment_limit]
            try:
                self.client.update_step_result_fail(step_result_id, comment)
            except Exception:
                self._record_reporting_error(
                    "Could not report FAIL for step {} ({})".format(number, name)
                )
            self._attach_file(step_result_id, screenshot_path)
            self._attach_file(step_result_id, error_path)

        return StepOutcome(
            number,
            name,
            False,
            step_result_id,
            error_file=error_path,
            screenshot_file=screenshot_path,
        )

    def _build_error_report(
        self,
        number: int,
        name: str,
        exception: Exception,
        diagnostic_offsets: Tuple[int, int, int],
    ) -> str:
        current_url = "Unavailable"
        if self.page is not None:
            with contextlib.suppress(Exception):
                current_url = self.page.url
        parts = [
            "Test: {} ({})".format(self.test_name, self.issue_key),
            "Step: {} - {}".format(number, name),
            "URL: {}".format(current_url),
            "Timestamp: {}".format(datetime.now().isoformat(timespec="seconds")),
            "Exception: {}: {}".format(type(exception).__name__, exception),
            "Traceback:\n{}".format(traceback.format_exc()),
        ]
        diagnostics = self.diagnostics.format_since(diagnostic_offsets)
        if diagnostics:
            parts.append(diagnostics)
        return "\n\n".join(parts)

    def _capture_failure_screenshot(
        self, number: int, name: str
    ) -> Optional[Path]:
        if self.page is None:
            return None
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        path = self.screenshot_dir / "step_{:02d}_{}_{}.png".format(
            number, _safe_name(name), _timestamp()
        )
        try:
            self.page.screenshot(path=str(path), full_page=True)
            return path
        except Exception:
            LOGGER.warning(
                "Could not capture the screenshot.\n%s", traceback.format_exc()
            )
            return None

    def _write_step_error(self, number: int, name: str, content: str) -> Path:
        self.error_dir.mkdir(parents=True, exist_ok=True)
        path = self.error_dir / "step_{:02d}_{}_{}.txt".format(
            number, _safe_name(name), _timestamp()
        )
        path.write_text(content, encoding="utf-8")
        return path

    def _attach_file(self, step_result_id: int, path: Optional[Path]) -> None:
        if path is None or self.client is None:
            return
        try:
            self.client.add_attachment(
                step_result_id,
                "TestStepResult",
                path.name,
                path.read_bytes(),
            )
        except Exception:
            self._record_reporting_error(
                "Could not attach {} to Zephyr step result {}".format(
                    path.name, step_result_id
                )
            )

    def _record_reporting_error(self, message: str) -> None:
        detail = "{}\n{}".format(message, traceback.format_exc())
        self.reporting_errors.append(detail)
        LOGGER.error("REPORTING ERROR - %s\n%s", message, traceback.format_exc())

    def _stop_trace(self) -> None:
        if self.context is None or self.settings.trace_mode == "off":
            return
        keep = (
            self.settings.trace_mode == "on"
            or self.failed_step_count > 0
            or bool(self.reporting_errors)
        )
        try:
            if keep:
                self.trace_dir.mkdir(parents=True, exist_ok=True)
                self.trace_path = self.trace_dir / "{}_trace.zip".format(
                    _safe_name(self.issue_key)
                )
                self.context.tracing.stop(path=str(self.trace_path))
            else:
                self.context.tracing.stop()
        except Exception:
            LOGGER.warning(
                "Could not finalize the Playwright trace.\n%s",
                traceback.format_exc(),
            )

    def _attach_trace(self) -> None:
        if (
            not self.settings.attach_trace_on_failure
            or self.trace_path is None
            or not self.trace_path.is_file()
        ):
            return
        failed = [outcome for outcome in self.outcomes if not outcome.passed]
        if failed and failed[0].zephyr_step_result_id is not None:
            self._attach_file(failed[0].zephyr_step_result_id, self.trace_path)

    def _mark_setup_failure(self) -> None:
        if self.client is not None and self.execution_id is not None:
            with contextlib.suppress(Exception):
                self.client.set_global_test_state(self.execution_id, STATUS_FAIL)

    def _close_resources(self) -> None:
        if self.context is not None:
            with contextlib.suppress(Exception):
                self.context.close()
        if self.browser is not None:
            with contextlib.suppress(Exception):
                self.browser.close()
        if self.playwright is not None:
            with contextlib.suppress(Exception):
                self.playwright.stop()
        if self.client is not None:
            with contextlib.suppress(Exception):
                self.client.close()

    def __exit__(
        self, exception_type: Any, exception: Any, exception_traceback: Any
    ) -> bool:
        fatal_exception = exception is not None
        if fatal_exception:
            LOGGER.error(
                "Unhandled error outside a test.step block:\n%s",
                "".join(
                    traceback.format_exception(
                        exception_type, exception, exception_traceback
                    )
                ),
            )
        try:
            if self._entered:
                self._validate_step_coverage()
            self._stop_trace()
            self._attach_trace()
            failed = fatal_exception or not self.success
            if self.client is not None and self.execution_id is not None:
                try:
                    self.client.set_global_test_state(
                        self.execution_id, STATUS_FAIL if failed else STATUS_PASS
                    )
                except Exception:
                    self._record_reporting_error(
                        "Could not update global Zephyr execution status"
                    )
            LOGGER.info(
                "Finished %s: %d passed, %d failed, %d reporting error(s).",
                self.issue_key,
                sum(outcome.passed for outcome in self.outcomes),
                self.failed_step_count,
                len(self.reporting_errors),
            )
        finally:
            self._close_resources()
        return False


@dataclass(frozen=True)
class ScriptResult:
    path: Path
    return_code: int
    duration_seconds: float


def _configured_test_directories() -> List[Path]:
    configured = os.getenv("TEST_DIRECTORIES", "").strip()
    raw_directories = []
    if configured:
        raw_directories.extend(configured.split(os.pathsep))
    else:
        # Preserve the previous CONFLUENCE_DIR/JIRA_DIR configuration.
        raw_directories.extend(
            value
            for value in (os.getenv("CONFLUENCE_DIR"), os.getenv("JIRA_DIR"))
            if value
        )
    if not raw_directories:
        raw_directories.append(str(PROJECT_ROOT))
    return [_resolve_path(value.strip()) for value in raw_directories if value.strip()]


def discover_test_scripts() -> List[Path]:
    """Discover test scripts without importing and executing them."""

    pattern = os.getenv("TEST_FILE_PATTERN", "*Ztest.py").strip() or "*Ztest.py"
    excluded = {Path(__file__).name, "generalBoilerplate.py"}
    scripts = []
    for directory in _configured_test_directories():
        if directory.is_file() and directory.suffix.lower() == ".py":
            candidates = [directory]
        elif directory.is_dir():
            candidates = list(directory.rglob(pattern))
        else:
            LOGGER.warning("Test directory does not exist: %s", directory)
            continue
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.name not in excluded and resolved not in scripts:
                scripts.append(resolved)
    return sorted(scripts, key=lambda path: str(path).lower())


def select_test_script(scripts: Sequence[Path], selection: str) -> Path:
    requested = Path(selection)
    if requested.is_file():
        resolved = requested.resolve()
        if resolved not in scripts:
            raise ConfigurationError(
                "{} is not part of the configured test set.".format(resolved)
            )
        return resolved

    normalized = selection.lower()
    matches = [
        script
        for script in scripts
        if script.name.lower() == normalized
        or script.stem.lower() == normalized
        or normalized in script.stem.lower()
    ]
    if not matches:
        raise ConfigurationError("No test matches {!r}.".format(selection))
    if len(matches) > 1:
        raise ConfigurationError(
            "Test selection {!r} is ambiguous: {}".format(
                selection, ", ".join(path.name for path in matches)
            )
        )
    return matches[0]


def execute_program(
    program_name: Any,
    cycle_id: Optional[Any] = None,
    run_id: Optional[str] = None,
    headless_override: Optional[bool] = None,
) -> ScriptResult:
    """Execute one test using the current Python interpreter."""

    path = Path(program_name).resolve()
    if not path.is_file():
        raise FileNotFoundError("The test script does not exist: {}".format(path))

    environment = os.environ.copy()
    if cycle_id is not None:
        environment["NRT_CYCLE_ID"] = str(cycle_id)
    if run_id:
        environment["NRT_RUN_ID"] = run_id
    if headless_override is not None:
        environment["HEADLESS"] = "true" if headless_override else "false"

    python_paths = [str(PROJECT_ROOT)]
    existing_pythonpath = environment.get("PYTHONPATH", "")
    if existing_pythonpath:
        python_paths.append(existing_pythonpath)
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)

    started = time.monotonic()
    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(PROJECT_ROOT),
        env=environment,
        check=False,
    )
    return ScriptResult(path, completed.returncode, time.monotonic() - started)


def _create_cycle(settings: Settings, run_id: str) -> str:
    settings.validate_zephyr()
    with ZephyrZapiClient(
        settings.jira_base_url,
        settings.jira_token,
        settings.request_timeout_seconds,
        settings.verify_tls,
    ) as client:
        cycle = client.create_cycle(
            settings.project_id,
            settings.version_id,
            "Playwright NRT {}".format(run_id),
        )
    cycle_id = cycle.get("id")
    if cycle_id is None:
        raise ValueError("Zephyr did not return a cycle ID: {!r}".format(cycle))
    save_cycle_id(cycle_id, settings.cycle_id_file)
    return str(cycle_id)


def configure_logging(verbose: bool = False) -> None:
    """Configure consistent console logs for direct and orchestrated runs."""

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a Zephyr cycle and run Playwright non-regression tests."
    )
    parser.add_argument(
        "--test",
        metavar="NAME",
        help="run one test selected by filename or an unambiguous name fragment",
    )
    parser.add_argument(
        "--list", action="store_true", help="list discovered tests without running them"
    )
    browser_mode = parser.add_mutually_exclusive_group()
    browser_mode.add_argument(
        "--headless", action="store_true", help="override .env and hide Edge"
    )
    browser_mode.add_argument(
        "--headed", action="store_true", help="override .env and show Edge"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="show detailed diagnostic logs"
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    configure_logging(args.verbose)
    try:
        scripts = discover_test_scripts()
        if args.list:
            if not scripts:
                print("No test script found.")
            for script in scripts:
                print(script)
            return 0
        if not scripts:
            raise ConfigurationError(
                "No test script found. Check TEST_DIRECTORIES and TEST_FILE_PATTERN."
            )
        if args.test:
            scripts = [select_test_script(scripts, args.test)]

        settings = Settings.from_env()
        run_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cycle_id = _create_cycle(settings, run_id)
        LOGGER.info("Created Zephyr cycle %s for %d test(s).", cycle_id, len(scripts))

        headless_override = None
        if args.headless:
            headless_override = True
        elif args.headed:
            headless_override = False

        results = []
        for index, script in enumerate(scripts, start=1):
            LOGGER.info("Running test %d/%d: %s", index, len(scripts), script.name)
            try:
                result = execute_program(
                    script, cycle_id, run_id, headless_override
                )
            except Exception:
                LOGGER.exception("Could not start %s.", script)
                result = ScriptResult(script, 1, 0.0)
            results.append(result)

        print("\nExecution summary")
        print("-" * 72)
        for result in results:
            status = "PASS" if result.return_code == 0 else "FAIL"
            print(
                "{:<6} {:<50} {:>7.1f}s".format(
                    status, result.path.name[:50], result.duration_seconds
                )
            )
        failed_count = sum(result.return_code != 0 for result in results)
        print("-" * 72)
        print(
            "{} passed, {} failed, {} total | Zephyr cycle {}".format(
                len(results) - failed_count,
                failed_count,
                len(results),
                cycle_id,
            )
        )
        return 1 if failed_count else 0
    except (ConfigurationError, OSError, ValueError, requests.RequestException) as exc:
        LOGGER.error("%s", exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
