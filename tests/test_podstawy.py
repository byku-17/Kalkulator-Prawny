from datetime import date

from obliczenia import (
    LATA_UMOWNE,
    PODSTAWA_DELIKTOWA,
    PODSTAWA_PRACOWNICZA,
    PODSTAWA_PRZESTEPSTWO,
    PODSTAWA_UMOWNA,
    PODSTAWA_WYROK,
    TypOdpowiedzialnosci,
    analiza_cywilna,
    analiza_deliktowa,
)


def _delikt(typ, czy_przestepstwo=False):
    return analiza_deliktowa(
        data_zdarzenia=date(2020, 1, 1),
        data_dowiedzenia_o_szkodzie=date(2020, 1, 1),
        czy_przestepstwo=czy_przestepstwo,
        czy_umyslne=False,
        typ_odpowiedzialnosci=typ,
        wpłaty=[],
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        data_oceny=date(2025, 1, 1),
    )


def test_umowna_uzywa_stalej_podstawy():
    """Roszczenie umowne korzysta ze wspólnej stałej PODSTAWA_UMOWNA."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[],
        data_wyroku_cywilnego=None,
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=LATA_UMOWNE,
        podstawa_prawna=PODSTAWA_UMOWNA,
        data_oceny=date(2025, 1, 1),
    )
    assert wynik.wyniki[0].podstawa_prawna == PODSTAWA_UMOWNA


def test_umowna_wyrok_uzywa_stalej_podstawy():
    """Po wyroku podstawa zmienia się na wspólną stałą PODSTAWA_WYROK."""
    wynik = analiza_cywilna(
        data_zawarcia_umowy=date(2020, 1, 1),
        data_wymagalnosci=date(2020, 1, 1),
        wpłaty=[],
        data_wyroku_cywilnego=date(2023, 1, 1),
        data_wszcz_egzekucji=None,
        data_umor_egzekucji=None,
        lata_baza=LATA_UMOWNE,
        podstawa_prawna=PODSTAWA_UMOWNA,
        data_oceny=date(2025, 1, 1),
    )
    assert wynik.wyniki[0].podstawa_prawna == PODSTAWA_WYROK


def test_delikt_uzywa_stalej_podstawy():
    assert _delikt(TypOdpowiedzialnosci.DELIKTOWA).wyniki[0].podstawa_prawna == PODSTAWA_DELIKTOWA


def test_pracownik_uzywa_stalej_podstawy():
    assert _delikt(TypOdpowiedzialnosci.PRACOWNICZA).wyniki[0].podstawa_prawna == PODSTAWA_PRACOWNICZA


def test_przestepstwo_uzywa_stalej_podstawy():
    wynik = _delikt(TypOdpowiedzialnosci.DELIKTOWA, czy_przestepstwo=True)
    assert wynik.wyniki[0].podstawa_prawna == PODSTAWA_PRZESTEPSTWO
