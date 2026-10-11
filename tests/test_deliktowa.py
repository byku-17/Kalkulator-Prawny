from datetime import date

from obliczenia import (
    analiza_deliktowa,
    TypOdpowiedzialnosci,
)


def _wywolaj(
    data_zdarzenia,
    data_dowiedzenia,
    czy_przestepstwo=False,
    czy_umyslne=False,
    typ=TypOdpowiedzialnosci.DELIKTOWA,
    wpłaty=None,
    data_wyroku_cywilnego=None,
    data_wszcz_egzekucji=None,
    data_umor_egzekucji=None,
    data_oceny=date(2025, 1, 1),
):
    return analiza_deliktowa(
        data_zdarzenia=data_zdarzenia,
        data_dowiedzenia_o_szkodzie=data_dowiedzenia,
        czy_przestepstwo=czy_przestepstwo,
        czy_umyslne=czy_umyslne,
        typ_odpowiedzialnosci=typ,
        wpłaty=wpłaty or [],
        data_wyroku_cywilnego=data_wyroku_cywilnego,
        data_wszcz_egzekucji=data_wszcz_egzekucji,
        data_umor_egzekucji=data_umor_egzekucji,
        data_oceny=data_oceny,
    )


# ─────────────────────────────────────────────
# Delikt bez kwalifikacji karnej (art. 442¹ § 1 k.c.)
# ─────────────────────────────────────────────
def test_delikt_3_lata_od_dowiedzenia():
    """3 lata od dowiedzenia się, granica 10 lat nieaktywna."""
    w = _wywolaj(date(2023, 1, 1), date(2023, 6, 1), data_oceny=date(2025, 1, 1))
    assert len(w.wyniki) == 1
    r = w.wyniki[0]
    assert r.status == "OK"
    # 3 lata od 2023-06-01 = 2026-06-01 (bez końca roku)
    assert r.termin == date(2026, 6, 1)
    assert "442" in r.podstawa_prawna


def test_delikt_przedawniony():
    """Termin w przeszłości -> przedawnione."""
    w = _wywolaj(date(2018, 1, 1), date(2018, 6, 1), data_oceny=date(2025, 1, 1))
    r = w.wyniki[0]
    assert r.status == "PRZEDAWNIONE"
    assert r.termin == date(2021, 6, 1)


def test_delikt_granica_10_lat_od_zdarzenia():
    """Dowiedzenie > 7 lat po zdarzeniu -> granica 10 lat od zdarzenia."""
    # Zdarzenie 2010, dowiedzenie 2019 -> 3 lata od dowiedzenia = 2022,
    # ale 10 lat od zdarzenia = 2020 -> wygrywa 2020
    w = _wywolaj(date(2010, 1, 1), date(2019, 1, 1), data_oceny=date(2025, 1, 1))
    r = w.wyniki[0]
    assert r.termin == date(2020, 1, 1)
    assert any("10 lat" in z for z in r.zalozenia)


def test_delikt_brak_konca_roku():
    """Delikt nie stosuje reguły końca roku."""
    w = _wywolaj(date(2020, 3, 15), date(2020, 3, 15), data_oceny=date(2025, 1, 1))
    r = w.wyniki[0]
    assert r.termin == date(2023, 3, 15)  # dokładnie 3 lata, nie 31.12
    assert any("bez reguły końca roku" in o for o in r.ostrzezenia)


def test_delikt_brak_daty_zdarzenia():
    """Brak daty zdarzenia -> błąd."""
    w = _wywolaj(None, date(2023, 1, 1))
    assert len(w.bledy) == 1
    assert "Brak daty zdarzenia" in w.bledy[0]


def test_delikt_brak_daty_dowiedzenia_bez_przestepstwa():
    """Brak daty dowiedzenia przy szkodzie niekarnej -> błąd."""
    w = _wywolaj(date(2023, 1, 1), None, czy_przestepstwo=False)
    assert len(w.bledy) == 1
    assert "Brak daty dowiedzenia się" in w.bledy[0]


# ─────────────────────────────────────────────
# Szkoda z przestępstwa (art. 442¹ § 2 k.c.)
# ─────────────────────────────────────────────
def test_przestepstwo_20_lat_od_czynu():
    """Szkoda z przestępstwa -> 20 lat od zdarzenia."""
    w = _wywolaj(date(2020, 1, 1), date(2023, 1, 1), czy_przestepstwo=True, data_oceny=date(2025, 1, 1))
    r = w.wyniki[0]
    assert r.termin == date(2040, 1, 1)
    assert "442" in r.podstawa_prawna and "przestępstw" in r.podstawa_prawna
    assert r.status == "OK"


def test_przestepstwo_nie_wymaga_daty_dowiedzenia():
    """Dla przestępstwa data dowiedzenia nie jest wymagana."""
    w = _wywolaj(date(2020, 1, 1), None, czy_przestepstwo=True)
    assert len(w.bledy) == 0
    r = w.wyniki[0]
    assert r.termin == date(2040, 1, 1)


# ─────────────────────────────────────────────
# Odpowiedzialność pracownicza (art. 291 k.p.)
# ─────────────────────────────────────────────
def test_pracownik_1_rok_od_dowiedzenia():
    """Pracownik nieumyślny: 1 rok od powzięcia wiadomości (art. 291 § 2 k.p.)."""
    w = _wywolaj(
        date(2023, 1, 1), date(2023, 6, 1),
        typ=TypOdpowiedzialnosci.PRACOWNICZA, data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    assert "291" in r.podstawa_prawna
    # 1 rok od 2023-06-01 = 2024-06-01 (limit 3 lat od zdarzenia nieaktywny)
    assert r.termin == date(2024, 6, 1)


def test_pracownik_limit_3_lat_od_wyrzadzenia():
    """Pracownik nieumyślny: limit 3 lat od wyrządzenia wygrywa z 1 rokiem."""
    w = _wywolaj(
        date(2018, 1, 1), date(2020, 6, 1),
        typ=TypOdpowiedzialnosci.PRACOWNICZA, data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    # 1 rok od 2020-06-01 = 2021-06-01; 3 lata od 2018-01-01 = 2021-01-01 -> wygrywa 2021-01-01
    assert r.termin == date(2021, 1, 1)


def test_pracownik_umyslny_przepisy_kc():
    """Pracownik umyślny: przepisy k.c. (art. 291 § 3) – 3 lata od dowiedzenia."""
    w = _wywolaj(
        date(2020, 1, 1), date(2020, 6, 1),
        czy_umyslne=True, typ=TypOdpowiedzialnosci.PRACOWNICZA, data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    assert "291 § 3" in r.podstawa_prawna
    assert r.termin == date(2023, 6, 1)


def test_pracownik_umyslne_ostrzezenie():
    """Pracownik umyślny -> ostrzeżenie o pełnej odpowiedzialności."""
    w = _wywolaj(
        date(2023, 1, 1), date(2023, 6, 1),
        czy_umyslne=True, typ=TypOdpowiedzialnosci.PRACOWNICZA
    )
    r = w.wyniki[0]
    combined = r.zalozenia + r.ostrzezenia
    assert any("umyśln" in x.lower() for x in combined)


def test_pracownik_przestepstwo_20_lat():
    """Pracownik sprawca przestępstwa -> 20 lat (442¹ § 2 przeważa)."""
    w = _wywolaj(
        date(2020, 1, 1), date(2023, 1, 1),
        czy_przestepstwo=True, typ=TypOdpowiedzialnosci.PRACOWNICZA
    )
    r = w.wyniki[0]
    assert r.termin == date(2040, 1, 1)


# ─────────────────────────────────────────────
# Zdarzenia: wpłaty, wyrok, egzekucja
# ─────────────────────────────────────────────
def test_delikt_wplata_przesuwa():
    """Wpłata (uznanie) przed wyrokiem resetuje bieg."""
    w = _wywolaj(
        date(2020, 1, 1), date(2020, 1, 1),
        wpłaty=[date(2023, 1, 1)], data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    # 3 lata od wpłaty 2023 = 2026
    assert r.termin == date(2026, 1, 1)


def test_delikt_wplata_po_wyroku_nie_przesuwa():
    """Wpłata po wyroku nie resetuje."""
    w = _wywolaj(
        date(2020, 1, 1), date(2020, 1, 1),
        wpłaty=[date(2024, 1, 1)],
        data_wyroku_cywilnego=date(2023, 1, 1),
        data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    # 6 lat od wyroku 2023 = 2029
    assert r.termin == date(2029, 1, 1)
    assert any("po wyroku" in o.lower() for o in r.ostrzezenia)


def test_delikt_wyrok_6_lat():
    """Wyrok -> 6 lat od wyroku."""
    w = _wywolaj(
        date(2018, 1, 1), date(2018, 6, 1),
        data_wyroku_cywilnego=date(2022, 1, 1), data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    assert r.termin == date(2028, 1, 1)
    assert "125" in r.podstawa_prawna


def test_delikt_wyrok_przed_2018_10_lat():
    """Wyrok przed 09.07.2018 -> 10 lat (dawne art. 125 § 1 k.c.)."""
    w = _wywolaj(
        date(2015, 1, 1), date(2015, 1, 1),
        data_wyroku_cywilnego=date(2016, 1, 1), data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    # 10 lat od wyroku 2016-01-01 = 2026-01-01
    assert r.termin == date(2026, 1, 1)
    assert "125" in r.podstawa_prawna


def test_delikt_wplata_w_trakcie_egzekucji():
    """Wpłata w trakcie egzekucji nie resetuje (zawieszenie)."""
    w = _wywolaj(
        date(2020, 1, 1), date(2020, 1, 1),
        wpłaty=[date(2023, 1, 1)],
        data_wszcz_egzekucji=date(2022, 1, 1),
        data_umor_egzekucji=date(2024, 1, 1),
        data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    # Umorzenie 2024 + 3 lata = 2027
    assert r.termin == date(2027, 1, 1)


def test_delikt_egzekucja_w_toku():
    """Egzekucja w toku -> W_TOKU."""
    w = _wywolaj(
        date(2020, 1, 1), date(2020, 1, 1),
        data_wszcz_egzekucji=date(2023, 1, 1), data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    assert r.status == "W_TOKU"


def test_delikt_umorzenie_resetuje():
    """Umorzenie egzekucji przed wyrokiem -> bieg od nowa."""
    w = _wywolaj(
        date(2020, 1, 1), date(2020, 1, 1),
        data_wszcz_egzekucji=date(2022, 1, 1),
        data_umor_egzekucji=date(2024, 1, 1),
        data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    # 3 lata od umorzenia 2024 = 2027
    assert r.termin == date(2027, 1, 1)


def test_delikt_reset_nie_wydluza_cap_10_lat():
    """Reset wpłatą nie wydłuża bezwzględnych 10 lat od zdarzenia (fix 3a)."""
    w = _wywolaj(
        date(2010, 1, 1), date(2010, 1, 1),
        wpłaty=[date(2023, 1, 1)], data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    # Bez capa byłoby 2026-01-01 (OK); z capem 2020-01-01 (PRZEDAWNIONE).
    assert r.termin == date(2020, 1, 1)
    assert r.status == "PRZEDAWNIONE"


def test_przestepstwo_reset_wydluza_termin():
    """Reset (uznanie) wydłuża bieg – 20 lat od wpłaty (art. 442¹ § 2 w zw. z art. 123/124 k.c.)."""
    w = _wywolaj(
        date(2010, 1, 1), date(2010, 1, 1),
        czy_przestepstwo=True,
        wpłaty=[date(2023, 1, 1)], data_oceny=date(2025, 1, 1)
    )
    r = w.wyniki[0]
    # 20 lat od wpłaty 2023-01-01 = 2043-01-01 (art. 442¹ § 2 k.c. nie jest limitem nieprzerywalnym).
    assert r.termin == date(2043, 1, 1)
    assert any("na nowo" in o for o in r.ostrzezenia)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])