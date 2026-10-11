"""
Test dymny (smoke test) interfejsu Streamlit.

Uruchamia aplikację przez AppTest, loguje się hasłem testowym i sprawdza,
że interfejs renderuje się oraz że kliknięcie "Sprawdź sprawę" nie powoduje
wyjątków – zarówno przy braku danych, jak i przy poprawnych danych.

Test samodzielnie tworzy tymczasowy plik .streamlit/secrets.toml (i przywraca
poprzedni stan po zakończeniu).
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
    # Po zalogowaniu widoczny jest wybór typu sprawy oraz pola dat.
    assert len(at.radio) > 0
    assert len(at.date_input) > 0


def test_analiza_bez_danych_nie_koliduje(app_klient):
    at = app_klient
    at.button[0].click().run()
    assert not at.exception


def test_analiza_umowna_poprawne_dane(app_klient):
    at = app_klient
    # Domyślny typ sprawy to Klient – umowa pożyczki (pola dat na początku).
    at.date_input[0].set_value(date(2023, 1, 1)).run()   # data zawarcia umowy
    at.date_input[1].set_value(date(2023, 1, 1)).run()   # data wymagalności
    at.button[0].click().run()
    assert not at.exception


def test_analiza_karna_poprawne_dane(app_klient):
    at = app_klient
    # Zaznacz "Postępowanie karne" (checkbox nr 4) i podaj datę czynu.
    at.checkbox[3].set_value(True).run()
    at.date_input[2].set_value(date(2022, 5, 1)).run()   # data popełnienia czynu
    at.button[0].click().run()
    assert not at.exception
