from datetime import date

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
# Nowa sygnatura: data_zawarcia_umowy, data_wymagalnosci, wpłaty, ...
# ─────────────────────────────────────────────
def test_cywilna_umowna_brak_przedawienia():
    """Umowa zawarta 2023-01-01, wymagalność 2023-01-01, ocena 2025 - brak przedawnienia (koniec roku)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2023, 1, 1),
        data_wymagalnosci=date(2023, 1, 1),
        wpłaty=[],
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
    # Umowa po 2018 -> koniec roku
    assert w.termin == date(2026, 12, 31)
    assert "Art. 118" in w.podstawa_prawna
    assert any("końca roku" in z for z in w.zalozenia + w.ostrzezenia)


def test_cywilna_umowna_przedawiona():
    """Umowa 2020-01-01, wymagalność 2020-01-01, ocena 2024 - przedawniona (koniec roku)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[],
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
    # Umowa po 2018 -> koniec roku
    assert w.termin == date(2023, 12, 31)


def test_cywilna_z_wyrokiem_6_lat():
    """Umowa 2020, wymagalność 2020, wyrok 2023-01-01 -> 6 lat od wyroku (koniec roku)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[],
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
    # Wyrok po 2018-07-09 -> koniec roku (ale dla wyroku nie ma końca roku - 6 lat od wyroku)
    assert w.termin == date(2029, 1, 1)


def test_cywilna_regula_konca_roku_po_2018():
    """Umowa zawarta po 2018-07-09 -> koniec roku."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 6, 15),
        data_wymagalnosci=date(2020, 6, 15),
        wpłaty=[],
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # 3 lata od 2020-06-15 = 2023-06-15 -> koniec roku 2023
    assert w.termin == date(2023, 12, 31)
    assert any("nowe" in z.lower() or "koniec roku" in z.lower() for z in w.zalozenia)


def test_cywilna_bez_reguly_konca_roku_przed_2018():
    """Umowa zawarta przed 2018-07-09 -> bez końca roku."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2018, 1, 1),
        data_wymagalnosci=date(2018, 1, 1),
        wpłaty=[],
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # 3 lata od 2018-01-01 = 2021-01-01 (bez końca roku)
    assert w.termin == date(2021, 1, 1)
    assert any("stare" in z.lower() or "bez końca roku" in z.lower() for z in w.zalozenia)


def test_cywilna_delikt_bez_reguly_konca_roku():
    """Szkoda deliktowa (art. 442¹) -> bez reguły końca roku."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=None,
        data_wymagalnosci=date(2020, 6, 15),
        wpłaty=[],
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 442¹ § 1 k.c. (szkoda deliktowa)",
        czy_delikt=True,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # Delikty: bez końca roku, dokładnie 3 lata
    assert w.termin == date(2023, 6, 15)
    assert any("bez końca roku" in z.lower() or "delikt" in z.lower() for z in w.zalozenia + w.ostrzezenia)


def test_cywilna_wplata_przesuwa_start():
    """Wpłata po dacie wymagalności przesuwa start (koniec roku dla umowy po 2018)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[date(2022, 1, 1)],
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
    assert any("uznanie" in z.lower() or "wpłata" in z.lower() for z in w.zalozenia)


def test_cywilna_wplata_po_wyroku_nie_przesuwa():
    """Wpłata PO wyroku nie resetuje przedawnienia (reżim 6 lat od wyroku)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[date(2024, 1, 1)],
        data_wyroku_cywilnego=date(2023, 1, 1),
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # Wyrok 2023 + 6 lat = 2029-01-01 (bez końca roku)
    assert w.termin == date(2029, 1, 1)
    assert any("po wyroku" in o.lower() for o in w.ostrzezenia)


def test_cywilna_umorzenie_egzekucji_przesuwa_start():
    """Umorzenie egzekucji przed wyrokiem przesuwa start (koniec roku)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[],
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
    assert any("umorzenie" in z.lower() for z in w.zalozenia)


def test_cywilna_umorzenie_po_wyroku_nie_przesuwa():
    """Umorzenie egzekucji PO wyroku nie resetuje (trwa 6 lat od wyroku)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[],
        data_wyroku_cywilnego=date(2023, 1, 1),
        data_wszcz_egzekucji=date(2024, 1, 1),
        data_umor_egzekucji=date(2025, 1, 1),
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2026, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2029, 1, 1)  # 6 lat od wyroku 2023


def test_cywilna_egzekucja_w_toku():
    """Egzekucja wszczęta, nie umorzona -> status W_TOKU (zawieszenie)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[],
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


def test_cywilna_brak_daty_wymagalnosci():
    """Brak daty wymagalności -> błąd."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=None,
        wpłaty=[],
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.bledy) == 1
    assert "Brak daty wymagalności" in wynik.bledy[0]


# ─────────────────────────────────────────────
# TESTY: analiza_karna (bez zmian)
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
        data_wszcz_k=date(2025, 1, 1),
        data_umor_k=None,
        data_oceny=date(2026, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2040, 1, 1)
    assert any("przedłużona o 10 lat" in z.lower() for z in w.zalozenia)


def test_karna_wszczenie_po_uplywie():
    """Wszczęcie po upływie -> brak przedłużenia, ostrzeżenie."""
    wynik = analiza_karna(
        data_czynu=date(2020, 1, 1),
        lata_karne=5,
        data_wszcz_k=date(2030, 1, 1),
        data_umor_k=None,
        data_oceny=date(2031, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.termin == date(2025, 1, 1)
    assert any("po upływie" in o for o in w.ostrzezenia)


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


def test_karna_oskarzenie_prywatne_nieobslugiwane():
    """Oskarżenie prywatne -> zgłoszony przypadek nieobsługiwany."""
    wynik = analiza_karna(
        data_czynu=date(2020, 1, 1),
        lata_karne=5,
        data_wszcz_k=None,
        data_umor_k=None,
        data_oceny=date(2025, 1, 1),
        czy_oskarzenie_prywatne=True
    )
    assert any("oskarżenia prywatnego" in n for n in wynik.nieobslugiwane)


def test_karna_brak_wszczecia_ostrzezenie():
    """Brak daty wszczęcia -> ostrzeżenie o niepełnym wyniku."""
    wynik = analiza_karna(
        data_czynu=date(2020, 1, 1),
        lata_karne=10,
        data_wszcz_k=None,
        data_umor_k=None,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert any("Brak daty wszczęcia" in o for o in w.ostrzezenia)


# ─────────────────────────────────────────────
# TESTY: analiza_zatarcia (art. 107 k.k.)
# ─────────────────────────────────────────────
def test_zatarcie_z_wykonaniem():
    """Wyrok 2020, wykonanie 2023, 5 lat -> 2028 (automatyczne)."""
    wynik = analiza_zatarcia(
        data_wyroku_k=date(2020, 1, 1),
        data_wykonania=date(2023, 1, 1),
        lata_zatarcia=5,
        data_oceny=date(2025, 1, 1)
    )
    # Bez opcji wyjątku -> 1 wynik
    assert len(wynik.wyniki) == 1
    w = wynik.wyniki[0]
    assert w.termin == date(2028, 1, 1)
    assert "107 § 1" in w.podstawa_prawna
    assert w.status == "W_KRK"


def test_zatarcie_bez_wykonania_brak_danych():
    """Brak daty wykonania -> BRAK_DANYCH (bez substytucji daty wyroku)."""
    wynik = analiza_zatarcia(
        data_wyroku_k=date(2020, 1, 1),
        data_wykonania=None,
        lata_zatarcia=5,
        data_oceny=date(2025, 1, 1)
    )
    assert len(wynik.wyniki) == 1
    w = wynik.wyniki[0]
    assert w.status == "BRAK_DANYCH"
    assert any("Brak daty wykonania" in o for o in w.ostrzezenia)


def test_zatarcie_zatarte():
    """Termin w przeszłości -> ZATARTE."""
    wynik = analiza_zatarcia(
        data_wyroku_k=date(2010, 1, 1),
        data_wykonania=date(2012, 1, 1),
        lata_zatarcia=5,
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
        lata_zatarcia=10,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    assert w.status == "W_KRK"
    assert w.termin == date(2033, 1, 1)


def test_zatarcie_wyjatek_wczesniej():
    """Zatarcie w drodze wyjątku (5 lat) wcześniejsze niż automatyczne (10)."""
    wynik = analiza_zatarcia(
        data_wyroku_k=date(2020, 1, 1),
        data_wykonania=date(2023, 1, 1),
        lata_zatarcia=10,
        data_oceny=date(2025, 1, 1),
        lata_zatarcia_wyjatek=5,
        rodzaj_kary="Pozbawienie wolności powyżej 3 lat"
    )
    # 2 wyniki: automatyczny (2033) i wyjątek (2028)
    assert len(wynik.wyniki) == 2
    terminy = {w.termin for w in wynik.wyniki}
    assert date(2033, 1, 1) in terminy
    assert date(2028, 1, 1) in terminy
    wyj = [w for w in wynik.wyniki if "107 § 4" in w.podstawa_prawna][0]
    assert wyj.status == "MOZLIWE_WCZEŚNIEJ"


def test_zatarcie_brak_wyroku():
    """Brak wyroku -> pusty wynik (nie błąd)."""
    wynik = analiza_zatarcia(
        data_wyroku_k=None,
        data_wykonania=None,
        lata_zatarcia=5,
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
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[date(2022, 6, 1)],
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


def test_scenariusz_wyrok_egzekucja_umorzenie():
    """Umowa 2019, wymagalność 2019, wyrok 2021, egzekucja 2022, umorzenie 2024."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2019, 1, 1),
        data_wymagalnosci=date(2019, 1, 1),
        wpłaty=[],
        data_wyroku_cywilnego=date(2021, 1, 1),
        data_wszcz_egzekucji=date(2022, 1, 1),
        data_umor_egzekucji=date(2024, 1, 1),
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # Wyrok 2021 -> 6 lat od wyroku = 2027-01-01 (bez końca roku)
    assert w.termin == date(2027, 1, 1)
    assert "Art. 125" in w.podstawa_prawna


def test_scenariusz_egzekucja_umorzenie_bez_wyroku():
    """Umowa 2020, egzekucja 2022, umorzenie 2024 (bez wyroku)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[],
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=date(2022, 1, 1),
        data_umor_egzekucji=date(2024, 1, 1),
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # Umorzenie 2024 + 3 lata = 2027 -> koniec roku 2027
    assert w.termin == date(2027, 12, 31)


def test_scenariusz_wielokrotne_wplaty():
    """Wiele wpłat - każda resetuje bieg (ostatnia wygrywa)."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[date(2021, 1, 1), date(2022, 1, 1), date(2023, 1, 1)],
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=3,
        podstawa_prawna="Art. 118 k.c.",
        czy_delikt=False,
        data_oceny=date(2025, 1, 1)
    )
    w = wynik.wyniki[0]
    # Ostatnia wpłata 2023-01-01 + 3 lata = 2026 -> koniec roku 2026
    assert w.termin == date(2026, 12, 31)


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
    assert w.termin == date(2038, 1, 1)
    assert w.status == "TRWA"
    assert any("Umorzenie" in z for z in w.zalozenia)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])