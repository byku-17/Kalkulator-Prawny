"""
Test dymny (smoke test) interfejsu Streamlit.

Uruchamia aplikację przez AppTest, loguje się hasłem testowym i sprawdza,
że nowy przepływ (2 kroki + karta decyzyjna) działa bez wyjątków.
"""
import contextlib
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
SECRETS = ROOT / ".streamlit" / "secrets.toml"
HASLO_TESTOWE = "test123"


@pytest.fixture(scope="module")
def app_klient():
    """Udostępnia zalogowany AppTest, zarządzając plikiem sekretów."""
    SECRETS.parent.mkdir(exist_ok=True)
    backup = SECRETS.read_text(encoding="utf-8") if SECRETS.exists() else None
    SECRETS.write_text(f'HASLO_DO_APLIKACJI = "{HASLO_TESTOWE}"\n', encoding="utf-8")

    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=60)
    at.run()
    at.text_input(key="password").set_value(HASLO_TESTOWE)
    at.run()

    yield at

    if backup is not None:
        SECRETS.write_text(backup, encoding="utf-8")
    else:
        with contextlib.suppress(FileNotFoundError):
            SECRETS.unlink()


def test_aplikacja_renderuje_po_zalogowaniu(app_klient):
    at = app_klient
    assert not at.exception
    # Po zalogowaniu widoczny radio typ_sprawy i checkboxy etapów
    assert len(at.radio) > 0
    assert len(at.checkbox) == 5


def test_analiza_umowna_poprawne_dane(app_klient):
    at = app_klient
    # Domyślny typ: Klient – umowa pożyczki (radio index 0)
    at.date_input(key="data_zawarcia_umowy").set_value(date(2023, 1, 1)).run()
    at.date_input(key="data_wymagalnosci").set_value(date(2023, 1, 1)).run()
    at.button(key="btn_sprawdz").click().run()
    assert not at.exception
    # Sprawdź, że jakiś wynik się pojawił (nie sprawdzamy dokładnego tekstu)
    assert len(at.success) > 0 or len(at.info) > 0 or len(at.warning) > 0


def test_analiza_karna_poprawne_dane(app_klient):
    at = app_klient
    # Zmień typ na "Deficyt – osoba trzecia" (radio index 3)
    at.radio(key="typ_sprawy").set_value("Deficyt – osoba trzecia").run()
    # Zaznacz "Postępowanie karne"
    at.checkbox(key="etap_karny").set_value(True).run()
    at.date_input(key="data_czynu").set_value(date(2022, 5, 1)).run()
    at.multiselect(key="kwalifikacje").set_value(["Oszustwo (art. 286 § 1 k.k.) – zagrożenie do 8 lat"]).run()
    at.button(key="btn_sprawdz").click().run()
    assert not at.exception
    # Sprawdź, że jakiś wynik się pojawił (niekoniecznie konkretny tekst)
    assert len(at.success) > 0 or len(at.info) > 0 or len(at.warning) > 0