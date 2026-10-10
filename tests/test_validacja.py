import sys
from pathlib import Path
from datetime import date

# Dodaj katalog główny do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import waliduj_dane


def test_umorzenie_egzekucji_bez_wszczenia():
    """Umorzenie egzekucji bez daty wszczęcia -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=date(2023, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=date(2024, 1, 1),
        data_czynu=None,
        wszczecie_k=None,
        umorzenie_k=None,
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert any("Umorzenie egzekucji wymaga daty wszczęcia" in b for b in bledy)


def test_wykonanie_kary_bez_wyroku():
    """Wykonanie kary bez daty wyroku -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=None,
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_czynu=None,
        wszczecie_k=None,
        umorzenie_k=None,
        wyrok_k=None,
        data_wykonania_kary=date(2024, 1, 1)
    )
    assert any("Data wykonania kary wymaga daty wyroku" in b for b in bledy)


def test_umorzenie_postepowania_bez_wszczenia():
    """Umorzenie postępowania karnego bez wszczęcia -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=None,
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_czynu=date(2023, 1, 1),
        wszczecie_k=None,
        umorzenie_k=date(2024, 1, 1),
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert any("Umorzenie postępowania karnego wymaga daty wszczęcia" in b for b in bledy)


def test_kolejnosc_dat_egzekucja_przed_baza():
    """Egzekucja przed datą bazową -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=date(2023, 6, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=date(2023, 1, 1),
        data_umor_egzekucji=None,
        data_czynu=None,
        wszczecie_k=None,
        umorzenie_k=None,
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert any("Egzekucja nie może być wszczęta przed datą wymagalności" in b for b in bledy)


def test_kolejnosc_dat_wyrok_przed_baza():
    """Wyrok cywilny przed datą bazową -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=date(2023, 6, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=date(2023, 1, 1),
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_czynu=None,
        wszczecie_k=None,
        umorzenie_k=None,
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert any("Wyrok cywilny nie może być wcześniejszy" in b for b in bledy)


def test_kolejnosc_dat_wplata_przed_baza():
    """Wpłata przed datą bazową -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=date(2023, 6, 1),
        ostatnia_wplata=date(2023, 1, 1),
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_czynu=None,
        wszczecie_k=None,
        umorzenie_k=None,
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert any("Data wpłaty nie może być wcześniejsza" in b for b in bledy)


def test_kolejnosc_dat_wszczenie_karne_przed_czynem():
    """Wszczęcie postępowania karnego przed datą czynu -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=None,
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_czynu=date(2023, 6, 1),
        wszczecie_k=date(2023, 1, 1),
        umorzenie_k=None,
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert any("Wszczęcie postępowania karnego nie może nastąpić przed datą czynu" in b for b in bledy)


def test_kolejnosc_dat_umorzenie_karne_przed_wszczeniem():
    """Umorzenie postępowania karnego przed wszczęciem -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=None,
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_czynu=date(2023, 1, 1),
        wszczecie_k=date(2023, 6, 1),
        umorzenie_k=date(2023, 1, 1),
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert any("Umorzenie postępowania karnego nie może nastąpić przed jego wszczęciem" in b for b in bledy)


def test_kolejnosc_dat_wykonanie_kary_przed_wyrokiem():
    """Wykonanie kary przed wyrokiem -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=None,
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_czynu=None,
        wszczecie_k=None,
        umorzenie_k=None,
        wyrok_k=date(2023, 6, 1),
        data_wykonania_kary=date(2023, 1, 1)
    )
    assert any("Data wykonania kary nie może być wcześniejsza niż data wyroku" in b for b in bledy)


def test_umorzenie_egzekucji_przed_wszczeniem():
    """Umorzenie egzekucji przed wszczęciem -> błąd."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=date(2023, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=date(2023, 6, 1),
        data_umor_egzekucji=date(2023, 1, 1),
        data_czynu=None,
        wszczecie_k=None,
        umorzenie_k=None,
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert any("Umorzenie egzekucji nie może nastąpić przed jej wszczęciem" in b for b in bledy)


def test_poprawne_dane_cywilne_bez_karnych():
    """Tylko dane cywilne, bez karnych -> brak błędów."""
    bledy, ostrzezenia = waliduj_dane(
        data_bazowa_cywilna=date(2023, 1, 1),
        ostatnia_wplata=date(2023, 6, 1),
        data_wyroku_cywilnego=date(2024, 1, 1),
        data_wszcz_egzekucji=date(2024, 6, 1),
        data_umor_egzekucji=date(2025, 1, 1),
        data_czynu=None,
        wszczecie_k=None,
        umorzenie_k=None,
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert len(bledy) == 0


def test_poprawne_dane_karne_bez_cywilnych():
    """Tylko dane karne, bez cywilnych -> brak błędów."""
    bledy, ostrzezenia = waliduj_dane(
        data_bazowa_cywilna=None,
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_czynu=date(2023, 1, 1),
        wszczecie_k=date(2023, 6, 1),
        umorzenie_k=None,
        wyrok_k=date(2024, 1, 1),
        data_wykonania_kary=date(2025, 1, 1)
    )
    assert len(bledy) == 0


def test_ostrzezenie_czyn_pozniej_niz_baza_cywilna():
    """Ostrzeżenie: data czynu późniejsza niż baza cywilna."""
    bledy, ostrzezenia = waliduj_dane(
        data_bazowa_cywilna=date(2023, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_czynu=date(2024, 1, 1),
        wszczecie_k=None,
        umorzenie_k=None,
        wyrok_k=None,
        data_wykonania_kary=None
    )
    assert len(bledy) == 0
    assert any("Data czynu jest późniejsza niż cywilna data bazowa" in o for o in ostrzezenia)


def test_wszystkie_bledy_naraz():
    """Wszystkie błędy zgłoszone naraz."""
    bledy, _ = waliduj_dane(
        data_bazowa_cywilna=date(2023, 6, 1),
        ostatnia_wplata=date(2023, 1, 1),  # wpłata przed bazą
        data_wyroku_cywilnego=date(2023, 1, 1),  # wyrok przed bazą
        data_wszcz_egzekucji=date(2023, 1, 1),  # egzekucja przed bazą
        data_umor_egzekucji=date(2022, 1, 1),  # umorzenie PRZED wszczęciem
        data_czynu=date(2023, 6, 1),
        wszczecie_k=date(2023, 1, 1),  # wszczęcie przed czynem
        umorzenie_k=date(2022, 1, 1),  # umorzenie PRZED wszczęciem
        wyrok_k=date(2023, 6, 1),
        data_wykonania_kary=date(2023, 1, 1)  # wykonanie przed wyrokiem
    )
    # Oczekujemy 7 błędów (2x umorzenie przed wszczęciem + 5 innych)
    assert len(bledy) == 7


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])