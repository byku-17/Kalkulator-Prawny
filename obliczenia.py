from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from dateutil.relativedelta import relativedelta


@dataclass
class WynikObliczenia:
    """Pojedynczy wynik obliczenia przedawnienia/zatarcia."""
    nazwa: str
    termin: date
    status: str  # "OK" | "PRZEDAWNIONE" | "TRWA" | "WYGASŁE" | "BRAK_DANYCH"
    podstawa_prawna: str
    zalozenia: list[str] = field(default_factory=list)
    ostrzezenia: list[str] = field(default_factory=list)
    orientacyjny: bool = False

    def __lt__(self, other):
        return self.termin < other.termin


@dataclass
class WynikAnalizyCywilnej:
    """Wynik kompletnej analizy cywilnej."""
    wyniki: list[WynikObliczenia] = field(default_factory=list)
    bledy: list[str] = field(default_factory=list)
    ostrzezenia: list[str] = field(default_factory=list)
    zalozenia: list[str] = field(default_factory=list)


@dataclass
class WynikAnalizyKarne:
    """Wynik kompletnej analizy karnej."""
    wyniki: list[WynikObliczenia] = field(default_factory=list)
    bledy: list[str] = field(default_factory=list)
    ostrzezenia: list[str] = field(default_factory=list)
    zalozenia: list[str] = field(default_factory=list)


@dataclass
class WynikAnalizyZatarcia:
    """Wynik kompletnej analizy zatarcia."""
    wyniki: list[WynikObliczenia] = field(default_factory=list)
    bledy: list[str] = field(default_factory=list)
    ostrzezenia: list[str] = field(default_factory=list)
    zalozenia: list[str] = field(default_factory=list)


def dodaj_lata(d: Optional[date], lata: int) -> Optional[date]:
    """Dodaje lata do daty, obsługuje None."""
    if d is None:
        return None
    return d + relativedelta(years=lata)


def _format_data(d: Optional[date]) -> str:
    if d is None:
        return "brak daty"
    return d.strftime("%d.%m.%Y")


def analiza_cywilna(
    data_bazowa: Optional[date],
    ostatnia_wplata: Optional[date],
    data_wyroku_cywilnego: Optional[date],
    data_wszcz_egzekucji: Optional[date],
    data_umor_egzekucji: Optional[date],
    lata_baza: int,
    podstawa_prawna: str,
    czy_delikt: bool,
    data_oceny: date
) -> WynikAnalizyCywilnej:
    """
    Analiza przedawnienia cywilnego.
    Zwraca uporządkowany wynik z terminami, statusami i podstawami.
    """
    wynik = WynikAnalizyCywilnej()

    if data_bazowa is None:
        wynik.bledy.append("Brak daty bazowej – analiza cywilna niemożliwa.")
        return wynik

    # Określ początek biegu i podstawę
    if data_wyroku_cywilnego:
        lata_cywil = 6
        aktualna_podstawa = "Art. 125 § 1 k.c. (wyrok)"
        start_cywil = data_wyroku_cywilnego
        wynik.zalozenia.append(f"Początek biegu od wyroku: {_format_data(start_cywil)}")
    else:
        lata_cywil = lata_baza
        aktualna_podstawa = podstawa_prawna
        start_cywil = data_bazowa
        wynik.zalozenia.append(f"Początek biegu od daty bazowej: {_format_data(start_cywil)}")

    # Wpłata / uznanie długu
    if ostatnia_wplata:
        if data_wyroku_cywilnego and ostatnia_wplata > data_wyroku_cywilnego:
            ostrz = ("Wpłata po dacie prawomocnego wyroku. "
                     "Może mieć znaczenie dla oceny uznania roszczenia, "
                     "ale nie przesądza automatycznie o skutkach przedawnieniowych.")
            wynik.ostrzezenia.append(ostrz)
            start_cywil = ostatnia_wplata
            wynik.zalozenia.append(f"Przesunięcie startu na datę wpłaty: {_format_data(start_cywil)}")
        elif not data_wyroku_cywilnego and ostatnia_wplata > start_cywil:
            ostrz = ("Zarejestrowano wpłatę / uznanie długu. "
                     "Może to stanowić uznanie roszczenia i przerwać bieg przedawnienia, "
                     "ale skutek zależy od okoliczności sprawy.")
            wynik.ostrzezenia.append(ostrz)
            start_cywil = ostatnia_wplata
            wynik.zalozenia.append(f"Przesunięcie startu na datę wpłaty: {_format_data(start_cywil)}")

    # Umorzenie egzekucji
    if data_umor_egzekucji and data_umor_egzekucji > start_cywil:
        start_cywil = data_umor_egzekucji
        wynik.zalozenia.append(f"Po umorzeniu egzekucji bieg od nowa: {_format_data(start_cywil)}")
        wynik.ostrzezenia.append("Po prawomocnym umorzeniu egzekucji bieg przedawnienia biegnie na nowo od tej daty.")

    # Egzekucja w toku
    if data_wszcz_egzekucji is not None and data_umor_egzekucji is None:
        wynik.wyniki.append(WynikObliczenia(
            nazwa="Egzekucja w toku",
            termin=data_oceny,  # symbolicznie
            status="W_TOKU",
            podstawa_prawna="Art. 124 § 2 k.c.",
            zalozenia=[f"Wszczęcie egzekucji: {_format_data(data_wszcz_egzekucji)}"],
            ostrzezenia=["Przedawnienie nie biegnie na nowo, dopóki postępowanie nie zostanie prawomocnie zakończone."],
            orientacyjny=True
        ))
        return wynik

    # Oblicz termin
    termin_podstawowy = dodaj_lata(start_cywil, lata_cywil)
    if termin_podstawowy is None:
        wynik.bledy.append("Nie udało się obliczyć terminu.")
        return wynik

    po_nowelizacji = start_cywil >= date(2018, 7, 9)
    to_czysty_delikt = czy_delikt and not data_wyroku_cywilnego

    if po_nowelizacji and not to_czysty_delikt:
        termin_ostateczny = date(termin_podstawowy.year, 12, 31)
        adnotacja = " (przesunięto na koniec roku - art. 118 k.c.)"
        wynik.zalozenia.append("Zastosowano regułę końca roku (nowelizacja 2018).")
    else:
        termin_ostateczny = termin_podstawowy
        adnotacja = " (bez reguły na koniec roku)"

    if termin_ostateczny >= data_oceny:
        status = "OK"
        komunikacja = f"Brak przedawnienia – roszczenie ważne do {_format_data(termin_ostateczny)}{adnotacja}."
    else:
        status = "PRZEDAWNIONE"
        komunikacja = f"Przedawnienie – termin upłynął {_format_data(termin_ostateczny)}{adnotacja}."

    wynik.wyniki.append(WynikObliczenia(
        nazwa=f"Przedawnienie cywilne [{aktualna_podstawa}]",
        termin=termin_ostateczny,
        status=status,
        podstawa_prawna=aktualna_podstawa,
        zalozenia=wynik.zalozenia.copy(),
        ostrzezenia=wynik.ostrzezenia.copy(),
        orientacyjny=False
    ))
    # Dodaj komunikat do pierwszego wyniku
    if wynik.wyniki:
        wynik.wyniki[0].ostrzezenia.insert(0, komunikacja)

    return wynik


def analiza_karna(
    data_czynu: Optional[date],
    lata_karne: int,
    data_wszcz_k: Optional[date],
    data_umor_k: Optional[date],
    data_oceny: date
) -> WynikAnalizyKarne:
    """
    Analiza przedawnienia karalności (art. 101, 102 k.k.).
    """
    wynik = WynikAnalizyKarne()

    if data_czynu is None:
        wynik.bledy.append("Brak daty czynu – nie można obliczyć przedawnienia karalności.")
        return wynik

    termin_karny = dodaj_lata(data_czynu, lata_karne)
    if termin_karny is None:
        wynik.bledy.append("Nie udało się obliczyć terminu karnego.")
        return wynik

    wynik.zalozenia.append(f"Data czynu: {_format_data(data_czynu)}")
    wynik.zalozenia.append(f"Ustawowe przedawnienie: {lata_karne} lat")
    wynik.zalozenia.append(f"Pierwotny termin: {_format_data(termin_karny)}")

    if data_wszcz_k:
        if data_wszcz_k <= termin_karny:
            termin_karny = dodaj_lata(termin_karny, 10)
            wynik.zalozenia.append(f"Wszczęcie postępowania: {_format_data(data_wszcz_k)} (przed upływem)")
            wynik.zalozenia.append("Przedłużono o 10 lat (art. 102 k.k.).")
            wynik.ostrzezenia.append("Art. 102 k.k.: Wszczęto postępowanie przed upływem przedawnienia. Karalność wydłużona o 10 lat.")
        else:
            wynik.ostrzezenia.append("Postępowanie karne wszczęto po pierwotnym upływie terminu przedawnienia karalności.")
    else:
        wynik.ostrzezenia.append("Brak daty wszczęcia. Wyliczenia nie uwzględniają ewentualnego przedłużenia o 10 lat.")

    if data_umor_k:
        wynik.zalozenia.append(f"Umorzenie postępowania: {_format_data(data_umor_k)}")
        wynik.ostrzezenia.append("Opcja podjęcia go na nowo zależy od podstaw prawnych umorzenia.")

    if termin_karny >= data_oceny:
        status = "TRWA"
        komunikacja = "Karalność trwa: zawiadomienie organów ścigania / kontynuowanie sprawy jest prawnie możliwe."
    else:
        status = "WYGASŁE"
        komunikacja = "Karalność wygasła: organy z urzędu odmówią wszczęcia lub umorzą postępowanie (przedawnienie)."

    wynik.wyniki.append(WynikObliczenia(
        nazwa="Orientacyjne ustanie karalności (Art. 101/102 k.k.)",
        termin=termin_karny,
        status=status,
        podstawa_prawna="Art. 101, 102 k.k.",
        zalozenia=wynik.zalozenia.copy(),
        ostrzezenia=[komunikacja] + wynik.ostrzezenia,
        orientacyjny=True
    ))

    return wynik


def analiza_zatarcia(
    data_wyroku_k: Optional[date],
    data_wykonania: Optional[date],
    lata_zat: int,
    data_oceny: date
) -> WynikAnalizyZatarcia:
    """
    Analiza zatarcia skazania (art. 107 k.k.).
    """
    wynik = WynikAnalizyZatarcia()

    if data_wyroku_k is None:
        # To nie jest błąd – po prostu pomijamy analizę
        return wynik

    if data_wykonania:
        termin_zatarcia = dodaj_lata(data_wykonania, lata_zat)
        baza = f"od wykonania/darowania kary ({_format_data(data_wykonania)})"
        wynik.zalozenia.append(f"Data wykonania kary: {_format_data(data_wykonania)}")
    else:
        termin_zatarcia = dodaj_lata(data_wyroku_k, lata_zat)
        baza = f"od wyroku – orientacyjnie ({_format_data(data_wyroku_k)})"
        wynik.ostrzezenia.append("OSTRZEŻENIE: Zatarcie wyliczono orientacyjnie od daty wyroku, brak daty wykonania kary.")
        wynik.zalozenia.append(f"Data wyroku (substytucja): {_format_data(data_wyroku_k)}")

    if termin_zatarcia is None:
        wynik.bledy.append("Nie udało się obliczyć terminu zatarcia.")
        return wynik

    wynik.zalozenia.append(f"Okres zatarcia: {lata_zat} lat")
    wynik.zalozenia.append(f"Baza obliczeń: {baza}")

    if termin_zatarcia < data_oceny:
        status = "ZATARTE"
        komunikacja = f"Zatarcie skazania: prawdopodobnie nastąpiło {_format_data(termin_zatarcia)} ({baza})."
    else:
        status = "W_KRK"
        komunikacja = f"Zatarcie skazania: skazanie prawdopodobnie nadal widnieje w KRK (orientacyjnie: {_format_data(termin_zatarcia)})."

    wynik.wyniki.append(WynikObliczenia(
        nazwa="Orientacyjne zatarcie skazania",
        termin=termin_zatarcia,
        status=status,
        podstawa_prawna="Art. 107 k.k.",
        zalozenia=wynik.zalozenia.copy(),
        ostrzezenia=[komunikacja] + wynik.ostrzezenia,
        orientacyjny=True
    ))

    return wynik