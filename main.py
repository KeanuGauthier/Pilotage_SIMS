# test_tnr_playwright.py
import sys
import traceback
from contextlib import contextmanager
from playwright.sync_api import sync_playwright, Page, expect

# ---------------------------------------------------------------------------
# 1. FONCTION D'EXPORT VERS L'API (FICTIVE)
# ---------------------------------------------------------------------------
def exporter_resultat_etape(test_key: str, step_name: str, status: str, log: str = "", screenshot_bytes: bytes = None):
    """
    Simule l'envoi du résultat d'une étape à une API externe (ex. Zephyr Scale/Squad, Jira, Xray).
    """
    print(f"\n[API EXPORT] >>> Test: {test_key} | Étape: '{step_name}' | Statut: {status}")
    
    if status == "FAIL":
        print(f"[API EXPORT] [!] Erreur remontée :\n{log}")
        if screenshot_bytes:
            print(f"[API EXPORT] [i] Capture d'écran jointe ({len(screenshot_bytes)} octets).")
            # En situation réelle : requests.post(url, data=..., files={'screenshot': screenshot_bytes})
    
    # En situation réelle : requests.post(url, json={"status": status, "comment": log}, headers=headers)


# ---------------------------------------------------------------------------
# 2. GESTIONNAIRE D'ÉTAPE (STEP RUNNER ROBUSTE)
# ---------------------------------------------------------------------------
@contextmanager
def step(page: Page, test_key: str, step_name: str):
    """
    Gestionnaire de contexte permettant :
    - D'isoler l'étape métier
    - De valider le statut 'PASS'
    - D'intercepter tout échec ('FAIL'), de prendre une capture plein écran et de remonter la trace à l'API
    """
    try:
        yield
        # Si aucune exception n'a été levée dans le bloc 'with'
        exporter_resultat_etape(
            test_key=test_key,
            step_name=step_name,
            status="PASS"
        )
    except Exception as e:
        # En cas d'erreur ou d'assertion non vérifiée
        error_log = traceback.format_exc()
        
        # Capture d'écran d'urgence au format binaire (pour export direct sans dépendre du disque)
        try:
            screenshot_bytes = page.screenshot(full_page=True)
            # Sauvegarde locale de secours
            page.screenshot(path=f"fail_{step_name.replace(' ', '_')}.png", full_page=True)
        except Exception:
            screenshot_bytes = None

        # Export vers l'API
        exporter_resultat_etape(
            test_key=test_key,
            step_name=step_name,
            status="FAIL",
            log=error_log,
            screenshot_bytes=screenshot_bytes
        )
        
        # On relance l'exception pour interrompre le test de non-régression
        raise e


# ---------------------------------------------------------------------------
# 3. SCÉNARIO DE TEST DE NON-RÉGRESSION
# ---------------------------------------------------------------------------
def run_test_scenario():
    TEST_CASE_KEY = "TNR-AUTO-01"
    
    with sync_playwright() as p:
        # Lancement de Edge en mode plein écran
        browser = p.chromium.launch(
            channel="msedge",
            headless=False,
            args=["--start-maximized"]  # Ouvre la fenêtre Windows au maximum
        )
        
        # no_viewport=True permet au contenu d'épouser la taille réelle de l'écran (évite le 1280x720 par défaut)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        try:
            # -------------------------------------------------------------------
            # ÉTAPE 1 : Accès à l'application et vérification du titre
            # -------------------------------------------------------------------
            with step(page, TEST_CASE_KEY, "01_Connexion_Page_Accueil"):
                page.goto("https://demo.playwright.dev/todomvc/")
                
                # Assertion auto-waiting recommandée par codegen
                expect(page.locator("h1")).to_have_text("todos")

            # -------------------------------------------------------------------
            # ÉTAPE 2 : Ajout de plusieurs éléments
            # -------------------------------------------------------------------
            with step(page, TEST_CASE_KEY, "02_Ajout_Elements"):
                # Bon réflexe codegen : utilisation des rôles et placeholders plutôt que des XPath
                input_field = page.get_by_placeholder("What needs to be done?")
                
                input_field.fill("Vérifier le module TNR")
                input_field.press("Enter")
                
                input_field.fill("Vérifier l'export API")
                input_field.press("Enter")
                
                # Vérification que 2 éléments sont présents dans la liste
                expect(page.get_by_test_id("todo-title")).to_have_count(2)

            # -------------------------------------------------------------------
            # ÉTAPE 3 : Validation et complétion d'un élément
            # -------------------------------------------------------------------
            with step(page, TEST_CASE_KEY, "03_Cloture_Element"):
                # On cible la checkbox du premier élément
                first_todo = page.get_by_test_id("todo-item").first
                first_todo.get_by_role("checkbox").check()
                
                # Assertion sur la classe CSS appliquée par l'application
                expect(first_todo).to_have_class("completed")
                
                # Vérification du compteur de tâches restantes
                expect(page.locator(".todo-count")).to_have_text("1 item left")

            # -------------------------------------------------------------------
            # ÉTAPE 4 : Filtrage des éléments actifs
            # -------------------------------------------------------------------
            with step(page, TEST_CASE_KEY, "04_Filtrage_Actifs"):
                page.get_by_role("link", name="Active").click()
                
                # Vérification : seul l'élément non coché doit apparaître
                expect(page.get_by_test_id("todo-title")).to_have_text(["Vérifier l'export API"])

            print("\n[OK] Scénario de non-régression validé avec succès sur toutes les étapes.")

        finally:
            # Nettoyage et fermeture propre de la session Edge
            context.close()
            browser.close()


if __name__ == "__main__":
    run_test_scenario()
