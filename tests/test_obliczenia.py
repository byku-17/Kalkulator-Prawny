import sys
from pathlib import Path
from datetime import date

# Dodaj katalog główny do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent))

from obliczenia import (
    dodaj_lata,
    analiza_cywilna,
    analiza_karna,
    analiza_zatarcia,
    WynikAnalizyCywilnej,
    WynikAnalizyKarne,
    WynikAnalizyZatarcia,
)


# ─────────────────────────────────────────────
# TESTY: dodaj_lata
# ─────────────────────────────────────────────
def test_dodaj_lata_basic():
    assert dodaj_lata(date(2023, 1, 15), 3) == date(2026, 1, 15)


def test_dodaj_lata_przestepny():
    assert dodaj_lata(date(2020, 2, 29), 1) == date(2021, 2, 28)


def test_dodaj_lata_none():
    assert dodaj_lata(None, 5) is None


# ─────────────────────────────────────────────
# TESTY: analiza_cywilna - umowna (3 lata)
# ─────────────────────────────────────────────
def test_cywilna_umowna_brak_przedawienia():
    """Umowa 2023-01-01, ocena 2025 - brak przedawnienia (koniec roku)."""
    wynik = analiza_cywilna(
        data_bazowa=date(2023, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c. (działalność gospodarcza)",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.wyniki) == 1
    w = wynik.wyniki[0]
    assert w.status == "OK"
    # Po nowelizacji 2018 -> koniec roku
    assert w.termin == date(2026, 12, 31)
    assert "Art. 118" in w.podstawa_prawna
    assert any("końca roku" in z for z in w.zalozenia)


def test_cywilna_umowna_przedawiona():
    """Umowa 2020-01-01, ocena 2024 - przedawniona (koniec roku)."""
    wynik = analiza_cywilna(
        data_bazowa=date(2020, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c. (działalność gospodarcza)",
        czy_delikt=False,
        data_oceny=date(2024, 1, 1)
    )
    assert len(wynik.wyniki) == 1
    w = wynik.wyniki[0]
    assert w.status == "PRZEDAWNIONE"
    # Po nowelizacji 2018 -> koniec roku
    assert w.termin == date(2023, 12, 31)


def test_cywilna_z_wyrokiem_6_lat():
    """Prawomocny wyrok 2023-01-01 -> 6 lat (koniec roku po nowelizacji)."""
    wynik = analiza_cywilna(
        data_bazowa=date(2020, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=date(2023, 1, 1),
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.wyniki) == 1
    w = wynik.wyniki[0]
    assert "Art. 125" in w.podstawa_prawna
    # Wyrok po 2018-07-09 -> koniec roku
    assert w.termin == date(2029, 12, 31)


def test_cywilna_regula_konca_roku_po_2018():
    """Start po 2018-07-09 -> koniec roku."""
    wynik = analiza_cywilna(
        data_bazowa=date(2020, 6, 15),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2023, 12, 31)  # koniec roku 2023


def test_cywilna_bez_reguly_konca_roku_przed_2018():
    """Start przed 2018-07-09 -> bez końca roku."""
    wynik = analiza_cywilna(
        data_bazowa=date(2018, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2021, 1, 1)  # dokładnie 3 lata


def test_cywilna_delikt_bez_reguly_konca_roku():
    """Szkoda deliktowa (art. 442¹) -> bez reguły końca roku."""
    wynik = analiza_cywilna(
        data_bazowa=date(2020, 6, 15),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 442¹ § 1 k.c. (szkoda deliktowa)",
        czy_delikt=True,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2023, 6, 15)  # dokładnie 3 lata, bez końca roku


def test_cywilna_wplata_przesuwa_start():
    """Wpłata po dacie bazowej przesuwa start (koniec roku)."""
    wynik = analiza_cywilna(
        data_bazowa=date(2020, 1, 1),
        ostatnia_wplata=date(2022, 1, 1),
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # Wpłata 2022-01-01 + 3 lata = 2025-01-01 -> koniec roku 2025
    assert w.termin == date(2025, 12, 31)
    assert any("wpłat" in o.lower() for o in w.ostrzezenia)


def test_cywilna_umorzenie_egzekucji_przesuwa_start():
    """Umorzenie egzekucji przesuwa start (koniec roku)."""
    wynik = analiza_cywilna(
        data_bazowa=date(2020, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=date(2021, 1, 1),
        data_umor_egzekucji=date(2023, 1, 1),
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # Umorzenie 2023-01-01 + 3 lata = 2026-01-01 -> koniec roku 2026
    assert w.termin == date(2026, 12, 31)


def test_cywilna_egzekucja_w_toku():
    """Egzekucja wszczęta, nie umorzona -> status W_TOKU."""
    wynik = analiza_cywilna(
        data_bazowa=date(2020, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=date(2023, 1, 1),
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.wyniki) == 1
    w = wynik.wyniki[0]
    assert w.status == "W_TOKU"
    assert "Art. 124" in w.podstawa_prawna


def test_cywilna_brak_daty_bazowej():
    """Brak daty bazowej -> błąd."""
    wynik = analiza_cywilna(
        data_bazowa=None,
        ostatnia_wplata=None,
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.bledy) == 1
    assert "Brak daty bazowej" in wynik.bledy[0]


# ─────────────────────────────────────────────
# TESTY: analiza_karna
# ─────────────────────────────────────────────
def test_karna_podstawowa_trwa():
    """Czyn 2020, 10 lat, ocena 2025 -> trwa."""
    wynik = analiza_karna(
        data_czynu=date(2020, 1, 1),
        lata_karne=10,
        data_wszcz_k=None,
        data_umor_k=None,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.wyniki) == 1
    w = wynik.wyniki[0]
    assert w.status == "TRWA"
    assert w.termin == date(2030, 1, 1)
    assert any("Brak daty wszczęcia" in o for o in w.ostrzezenia)


def test_karna_wszczenie_przed_uplywem_przedluza_o_10_lat():
    """Wszczęcie przed upływem -> +10 lat."""
    wynik = analiza_karna(
        data_czynu=date(2020, 1, 1),
        lata_karne=10,
        data_wszcz_k=date(2025, 1, 1),  # przed upływem (2030)
        data_umor_k=None,
        data_oceny=date(2026, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2040, 1, 1)  # 2030 + 10
    assert any("Przedłużono o 10 lat" in z for z in w.zalozenia)


def test_karna_wszczenie_po_uplywie():
    """Wszczęcie po upływie -> brak przedłużenia, ostrzeżenie."""
    wynik = analiza_karna(
        data_czynu=date(2020, 1, 1),
        lata_karne=5,
        data_wszcz_k=date(2030, 1, 1),  # po upływie (2025)
        data_umor_k=None,
        data_oceny=date(2031, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2025, 1, 1)  # bez przedłużenia
    assert any("po pierwotnym upływie" in o for o in w.ostrzezenia)


def test_karna_wygasla():
    """Termin w przeszłości -> WYGASŁE."""
    wynik = analiza_karna(
        data_czynu=date(2010, 1, 1),
        lata_karne=10,
        data_wszcz_k=None,
        data_umor_k=None,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.status == "WYGASŁE"
    assert w.termin == date(2020, 1, 1)


def test_karna_brak_daty_czynu():
    """Brak daty czynu -> błąd."""
    wynik = analiza_karna(
        data_czynu=None,
        lata_karne=10,
        data_wszcz_k=None,
        data_umor_k=None,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.bledy) == 1
    assert "Brak daty czynu" in wynik.bledy[0]


# ─────────────────────────────────────────────
# TESTY: analiza_zatarcia
# ─────────────────────────────────────────────
def test_zatarcie_z_wykonaniem():
    """Wyrok 2020, wykonanie 2023, 5 lat -> 2028."""
    wynik = analiza_zatarcia(
        data_wyroku_k=date(2020, 1, 1),
        data_wykonania=date(2023, 1, 1),
        lata_zat=5,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.wyniki) == 1
    w = wynik.wyniki[0]
    assert w.termin == date(2028, 1, 1)
    assert any("wykonania" in z for z in w.zalozenia)
    assert not any("OSTRZEŻENIE" in o for o in w.ostrzezenia)


def test_zatarcie_bez_wykonania_orientacyjnie():
    """Wyrok 2020, brak wykonania, 5 lat -> orientacyjnie od wyroku."""
    wynik = analiza_zatarcia(
        data_wyroku_k=date(2020, 1, 1),
        data_wykonania=None,
        lata_zat=5,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2025, 1, 1)
    assert any("OSTRZEŻENIE" in o for o in w.ostrzezenia)


def test_zatarcie_zatarte():
    """Termin w przeszłości -> ZATARTE."""
    wynik = analiza_zatarcia(
        data_wyroku_k=date(2010, 1, 1),
        data_wykonania=date(2012, 1, 1),
        lata_zat=5,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.status == "ZATARTE"
    assert w.termin == date(2017, 1, 1)


def test_zatarcie_w_krk():
    """Termin w przyszłości -> W_KRK."""
    wynik = analiza_zatarcia(
        data_wyroku_k=date(2020, 1, 1),
        data_wykonania=date(2023, 1, 1),
        lata_zat=10,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.status == "W_KRK"
    assert w.termin == date(2033, 1, 1)


def test_zatarcie_brak_wyroku():
    """Brak wyroku -> pusty wynik (nie błąd)."""
    wynik = analiza_zatarcia(
        data_wyroku_k=None,
        data_wykonania=None,
        lata_zat=5,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.wyniki) == 0
    assert len(wynik.bledy) == 0


# ─────────────────────────────────────────────
# TESTY INTEGRACYJNE - scenariusze z życia
# ─────────────────────────────────────────────
def test_scenariusz_pozyczka_z_wplata():
    """Pożyczka 2020, wpłata 2022, ocena 2024 (koniec roku)."""
    wynik = analiza_cywilna(
        data_bazowa=date(2020, 1, 1),
        ostatnia_wplata=date(2022, 6, 1),
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2024, 1, 1)
    )
    w = wynik.wyniki[0]
    # Wpłata 2022-06-01 + 3 lata = 2025-06-01 -> koniec roku 2025
    assert w.termin == date(2025, 12, 31)
    assert w.status == "OK"


def test_scenariusz_wyrok_egzekucja_umorzenie():
    """Wyrok 2021, egzekucja 2022, umorzenie 2024 (koniec roku)."""
    wynik = analiza_cywilna(
        data_bazowa=date(2019, 1, 1),
        ostatnia_wplata=None,
        data_wyroku_cywilnego=date(2021, 1, 1),
        data_wszcz_egzekucji=date(2022, 1, 1),
        data_umor_egzekucji=date(2024, 1, 1),
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # Umorzenie 2024-01-01 + 6 lat = 2030-01-01 -> koniec roku 2030
    assert w.termin == date(2030, 12, 31)


def test_scenariusz_karna_z_wszczeniem_i_umorzeniem():
    """Czyn 2018, wszczęcie 2020, umorzenie 2023."""
    wynik = analiza_karna(
        data_czynu=date(2018, 1, 1),
        lata_karne=10,
        data_wszcz_k=date(2020, 1, 1),
        data_umor_k=date(2023, 1, 1),
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2038, 1, 1)  # 2028 + 10
    assert w.status == "TRWA"
    assert any("Umorzenie" in z for z in w.zalozenia)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])