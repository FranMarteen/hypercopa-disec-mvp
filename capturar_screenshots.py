"""Captura screenshots do Predfy (Streamlit) via Playwright em headless.

Pré-requisitos:
- pip install playwright
- python -m playwright install chromium
- App rodando em http://localhost:8501 com Modo demonstração ativo

Saída: docs/screenshots/*.png (mostrando as 7 etapas da jornada)
"""
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "docs" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8501"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,  # screenshots em alta resolução
        )
        page = context.new_page()

        print(f"Abrindo {URL}...")
        page.goto(URL, wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # ===== 1) Header + Stepper + (Modo demo OFF) — primeira impressão =====
        page.screenshot(path=OUT_DIR / "01_header_e_stepper.png", full_page=False)
        print("OK01_header_e_stepper.png")

        # ===== Ativar modo demo via sidebar =====
        # Tenta encontrar o toggle "Modo demonstração" e clica
        try:
            toggle = page.locator(
                "label", has_text="Modo demonstração da banca"
            ).first
            if toggle.count() > 0:
                toggle.click()
                time.sleep(2)
                print("OKModo demo ativado")
        except Exception as e:
            print(f"WARNNão conseguiu ativar modo demo: {e}")

        # ===== 2) Banner amarelo + stepper com modo demo ON =====
        page.screenshot(path=OUT_DIR / "02_modo_demo_ativo.png", full_page=False)
        print("OK02_modo_demo_ativo.png")

        # ===== 3) Etapa 0 — Universo de dados sintéticos (clique no expander) =====
        try:
            expander = page.locator(
                "summary, [data-testid='stExpander']"
            ).filter(has_text="Etapa 0").first
            if expander.count() > 0:
                expander.click()
                time.sleep(2)
        except Exception as e:
            print(f"WARNEtapa 0 expander: {e}")
        page.screenshot(path=OUT_DIR / "03_etapa0_dados_sinteticos.png", full_page=True)
        print("OK03_etapa0_dados_sinteticos.png")

        # Fecha expander e rola até a Etapa 1
        try:
            page.locator("summary").filter(has_text="Etapa 0").first.click()
            time.sleep(1)
        except Exception:
            pass

        # ===== 4) Etapa 1 — Conversa com agente (modo demo) =====
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.25)")
        time.sleep(1)
        page.screenshot(path=OUT_DIR / "04_etapa1_agente_predfy.png", full_page=False)
        print("OK04_etapa1_agente_predfy.png")

        # ===== 5) Avança alguns turnos do script demo =====
        for i in range(10):
            try:
                btn = page.locator("button", has_text="Próximo turno").first
                if btn.count() == 0:
                    break
                btn.click()
                time.sleep(1.5)
            except Exception:
                break

        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.3)")
        time.sleep(2)
        page.screenshot(path=OUT_DIR / "05_etapa1_apos_turnos.png", full_page=True)
        print("OK05_etapa1_apos_turnos.png")

        # ===== 6) Sidebar (zoom — opcional) =====
        try:
            sidebar = page.locator("[data-testid='stSidebar']")
            if sidebar.count() > 0:
                sidebar.screenshot(path=OUT_DIR / "06_sidebar.png")
                print("OK06_sidebar.png")
        except Exception as e:
            print(f"WARNSidebar: {e}")

        # ===== 7) Etapa 2 — H2O AutoML (rola até) =====
        try:
            page.locator("text=Etapa 2").first.scroll_into_view_if_needed()
            time.sleep(1.5)
        except Exception:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.5)")
            time.sleep(1)
        page.screenshot(path=OUT_DIR / "07_etapa2_h2o.png", full_page=False)
        print("OK07_etapa2_h2o.png")

        # ===== 8) Página inteira final =====
        page.screenshot(path=OUT_DIR / "08_full_page.png", full_page=True)
        print("OK08_full_page.png")

        browser.close()
        print(f"\nScreenshots salvos em: {OUT_DIR}")


if __name__ == "__main__":
    main()
