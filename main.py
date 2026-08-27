# test_tnr_playwright.py

import re
import traceback
from pathlib import Path
from contextlib import contextmanager

from playwright.sync_api import sync_playwright, Page, expect


# =============================================================================
# CONFIGURATION
# =============================================================================

TEST_CASE_KEY = "TNR-AUTO-01"

BASE_URL = "https://demo.playwright.dev/todomvc/"

HEADLESS = False

VIEWPORT = {
    "width": 1920,
    "height": 1080,
}

DEFAULT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 30_000

ARTIFACTS_DIR = Path("artifacts")
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
TRACES_DIR = ARTIFACTS_DIR / "traces"

SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
TRACES_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# EXPORT ZEPHYR
# =============================================================================

def exporter_resultat_etape(
    test_key: str,
    step_id: str,
    step_name: str,
    status: str,
    log: str = "",
    screenshot_bytes: bytes | None = None,
):
    """
    Envoie le résultat d'une étape vers Zephyr.

    Cette fonction est volontairement indépendante de Playwright :
    une erreur d'export Zephyr ne doit pas transformer un test PASS en FAIL.
    """

    print(
        f"\n[ZEPHYR] "
        f"Test={test_key} | "
        f"Step={step_id} | "
        f"Nom='{step_name}' | "
        f"Statut={status}"
    )

    if log:
        print(f"[ZEPHYR] Log :\n{log}")

    if screenshot_bytes:
        print(
            f"[ZEPHYR] Screenshot joint "
            f"({len(screenshot_bytes)} octets)"
        )

    # -------------------------------------------------------------------------
    # EXEMPLE IMPLEMENTATION ZEPHYR
    # -------------------------------------------------------------------------
    #
    # requests.post(
    #     url,
    #     json={
    #         "testKey": test_key,
    #         "stepId": step_id,
    #         "status": status,
    #         "comment": log,
    #     },
    #     headers=headers,
    # )
    #
    # Puis upload éventuel du screenshot.
    # -------------------------------------------------------------------------


# =============================================================================
# OUTILS
# =============================================================================

def safe_filename(value: str) -> str:
    """
    Transforme une chaîne en nom de fichier sûr.
    """

    return re.sub(
        r"[^a-zA-Z0-9_.-]",
        "_",
        value,
    )


def exporter_zephyr_sans_interrompre(**kwargs):
    """
    Encapsule l'export Zephyr.

    Une panne de Zephyr ne doit jamais être interprétée comme
    une régression fonctionnelle de l'application.
    """

    try:
        exporter_resultat_etape(**kwargs)

    except Exception:
        print(
            "\n[ERREUR REPORTING]"
            "\nImpossible d'envoyer le résultat vers Zephyr."
            "\nLe résultat Playwright reste inchangé."
        )

        print(traceback.format_exc())


# =============================================================================
# STEP RUNNER
# =============================================================================

@contextmanager
def step(
    page: Page,
    test_key: str,
    step_id: str,
    step_name: str,
):
    """
    Exécute une étape métier.

    Comportement :
    - aucune exception -> PASS
    - exception Playwright/assertion -> FAIL
    - screenshot automatique en cas de FAIL
    - traceback complet envoyé à Zephyr
    - l'exception est relancée pour stopper le scénario
    """

    print(
        f"\n{'=' * 80}"
        f"\n[STEP {step_id}] {step_name}"
        f"\n{'=' * 80}"
    )

    try:
        yield

    except Exception:

        # ---------------------------------------------------------------------
        # TRACEBACK
        # ---------------------------------------------------------------------

        error_log = traceback.format_exc()

        print(
            f"\n[FAIL] Étape {step_id} : {step_name}"
        )

        print(error_log)

        # ---------------------------------------------------------------------
        # SCREENSHOT
        # ---------------------------------------------------------------------

        screenshot_bytes = None

        try:
            screenshot_bytes = page.screenshot(
                full_page=True
            )

            screenshot_name = (
                f"{safe_filename(test_key)}_"
                f"{safe_filename(step_id)}_"
                f"{safe_filename(step_name)}.png"
            )

            screenshot_path = (
                SCREENSHOTS_DIR
                / screenshot_name
            )

            screenshot_path.write_bytes(
                screenshot_bytes
            )

            print(
                f"[SCREENSHOT] {screenshot_path}"
            )

        except Exception:
            print(
                "[SCREENSHOT] Impossible de capturer la page."
            )

        # ---------------------------------------------------------------------
        # ZEPHYR FAIL
        # ---------------------------------------------------------------------

        exporter_zephyr_sans_interrompre(
            test_key=test_key,
            step_id=step_id,
            step_name=step_name,
            status="FAIL",
            log=error_log,
            screenshot_bytes=screenshot_bytes,
        )

        # Conserve le traceback original
        raise

    else:

        # ---------------------------------------------------------------------
        # ZEPHYR PASS
        # ---------------------------------------------------------------------

        exporter_zephyr_sans_interrompre(
            test_key=test_key,
            step_id=step_id,
            step_name=step_name,
            status="PASS",
        )

        print(
            f"[PASS] Étape {step_id} : {step_name}"
        )


# =============================================================================
# SCENARIO DE TEST
# =============================================================================

def run_test_scenario():

    with sync_playwright() as p:

        # =====================================================================
        # NAVIGATEUR
        # =====================================================================

        browser = p.chromium.launch(
            channel="msedge",
            headless=HEADLESS,
        )

        context = browser.new_context(
            viewport=VIEWPORT,
        )

        # =====================================================================
        # TRACE PLAYWRIGHT
        # =====================================================================

        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True,
        )

        page = context.new_page()

        # =====================================================================
        # TIMEOUTS
        # =====================================================================

        page.set_default_timeout(
            DEFAULT_TIMEOUT
        )

        page.set_default_navigation_timeout(
            NAVIGATION_TIMEOUT
        )

        # =====================================================================
        # LOGS NAVIGATEUR
        # =====================================================================

        console_errors = []
        page_errors = []

        def handle_console(message):
            if message.type == "error":
                console_errors.append(
                    message.text
                )

        def handle_page_error(error):
            page_errors.append(
                str(error)
            )

        page.on(
            "console",
            handle_console,
        )

        page.on(
            "pageerror",
            handle_page_error,
        )

        test_failed = False

        try:

            # =================================================================
            # STEP 1
            # =================================================================

            with step(
                page,
                TEST_CASE_KEY,
                step_id="1",
                step_name="Connexion à la page d'accueil",
            ):

                # -------------------------------------------------------------
                # CODEGEN
                # Copier / coller ici le code généré par Playwright Codegen
                # -------------------------------------------------------------

                page.goto(BASE_URL)

                expect(
                    page.locator("h1")
                ).to_have_text("todos")


            # =================================================================
            # STEP 2
            # =================================================================

            with step(
                page,
                TEST_CASE_KEY,
                step_id="2",
                step_name="Ajout de plusieurs éléments",
            ):

                # -------------------------------------------------------------
                # CODEGEN
                # -------------------------------------------------------------

                input_field = page.get_by_placeholder(
                    "What needs to be done?"
                )

                input_field.fill(
                    "Vérifier le module TNR"
                )

                input_field.press(
                    "Enter"
                )

                input_field.fill(
                    "Vérifier l'export API"
                )

                input_field.press(
                    "Enter"
                )

                expect(
                    page.get_by_test_id("todo-title")
                ).to_have_count(2)


            # =================================================================
            # STEP 3
            # =================================================================

            with step(
                page,
                TEST_CASE_KEY,
                step_id="3",
                step_name="Clôture d'un élément",
            ):

                # -------------------------------------------------------------
                # CODEGEN
                # -------------------------------------------------------------

                first_todo = (
                    page
                    .get_by_test_id("todo-item")
                    .first
                )

                checkbox = first_todo.get_by_role(
                    "checkbox"
                )

                checkbox.check()

                # Assertion fonctionnelle plutôt qu'une vérification
                # directe de classe CSS.
                expect(
                    checkbox
                ).to_be_checked()

                expect(
                    page.locator(".todo-count")
                ).to_have_text(
                    "1 item left"
                )


            # =================================================================
            # STEP 4
            # =================================================================

            with step(
                page,
                TEST_CASE_KEY,
                step_id="4",
                step_name="Filtrage des éléments actifs",
            ):

                # -------------------------------------------------------------
                # CODEGEN
                # -------------------------------------------------------------

                page.get_by_role(
                    "link",
                    name="Active",
                ).click()

                expect(
                    page.get_by_test_id("todo-title")
                ).to_have_text(
                    [
                        "Vérifier l'export API"
                    ]
                )


            # =================================================================
            # FIN DU TEST
            # =================================================================

            print(
                "\n"
                + "=" * 80
                + "\n[OK] SCENARIO TNR VALIDE"
                + "\nToutes les étapes ont été exécutées avec succès."
                + "\n"
                + "=" * 80
            )

        except Exception:

            test_failed = True

            raise

        finally:

            # =================================================================
            # LOGS NAVIGATEUR
            # =================================================================

            if console_errors:

                print(
                    "\n[CONSOLE ERRORS]"
                )

                for error in console_errors:
                    print(
                        f"- {error}"
                    )

            if page_errors:

                print(
                    "\n[PAGE ERRORS]"
                )

                for error in page_errors:
                    print(
                        f"- {error}"
                    )

            # =================================================================
            # TRACE PLAYWRIGHT
            # =================================================================

            trace_path = (
                TRACES_DIR
                / f"{safe_filename(TEST_CASE_KEY)}.zip"
            )

            try:

                context.tracing.stop(
                    path=trace_path
                )

                print(
                    f"\n[TRACE] {trace_path}"
                )

            except Exception:

                print(
                    "\n[TRACE] Impossible de sauvegarder la trace."
                )

            # =================================================================
            # NETTOYAGE
            # =================================================================

            context.close()
            browser.close()


# =============================================================================
# EXECUTION
# =============================================================================

if __name__ == "__main__":
    run_test_scenario()
