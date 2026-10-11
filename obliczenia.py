from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from dateutil.relativedelta import relativedelta
from enum import Enum


class TypZdarzenia(Enum):
    """Typ zdarzenia wpływającego na bieg przedawnienia."""
    START = "start"                    # początek biegu (wymagalność)
    WPLATA = "wplata"                  # wpłata / uznanie długu (art. 123 k.c.)
    WYSZCZ_EGZEKUCJI = "wyszcz_egzekucji"  # wszczęcie egzekucji (art. 124 k.c.)
    UMORZENIE_EGZEKUCJI = "umorzenie_egzekucji"  # umorzenie egzekucji (art. 124 § 2 k.c.)
    WYROK = "wyrok"                    # prawomocny wyrok (art. 125 k.c.)


class TypOdpowiedzialnosci(Enum):
    """Reżim odpowiedzialności wpływający na podstawę przedawnienia."""
    UMOWNA = "umowna"          # art. 118 k.c. (działalność gospodarcza)
    DELIKTOWA = "deliktowa"    # art. 442¹ k.c. (osoba trzecia)
    PRACOWNICZA = "pracownicza"  # art. 291 k.p. (pracownik)


# ─────────────────────────────────────────────
# Podstawy prawne (jedno źródło prawdy dla logiki i interfejsu)
# ─────────────────────────────────────────────
LATA_UMOWNE = 3
PODSTAWA_UMOWNA = "Art. 118 k.c. (działalność gospodarcza)"
PODSTAWA_PRACOWNICZA = "Art. 291 § 2 k.p. (odpowiedzialność pracownicza)"
PODSTAWA_PRACOWNICZA_UMYSLNA = "Art. 291 § 3 k.p. w zw. z art. 442¹ § 1 k.c. (szkoda umyślna pracownika)"
PODSTAWA_DELIKTOWA = "Art. 442¹ § 1 k.c. (szkoda deliktowa)"
PODSTAWA_PRZESTEPSTWO = "Art. 442¹ § 2 k.c. (szkoda z przestępstwa – 20 lat od czynu)"
PODSTAWA_WYROK = "Art. 125 § 1 k.c. (wyrok)"


@dataclass
class ZdarzeniePrzedawnienia:
    """Pojedyncze zdarzenie na osi czasu przedawnienia."""
    typ: TypZdarzenia
    data: date
    opis: str


@dataclass
class WynikObliczenia:
    """Pojedynczy wynik obliczenia przedawnienia/zatarcia."""
    nazwa: str
    termin: date
    status: str  # "OK" | "PRZEDAWNIONE" | "W_TOKU" | "TRWA" | "WYGASŁE" | "BRAK_DANYCH" | "ZATARTE" | "W_KRK" | "MOZLIWE_WCZEŚNIEJ"
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
    os_czasu: list[ZdarzeniePrzedawnienia] = field(default_factory=list)


@dataclass
class WynikAnalizyKarne:
    """Wynik kompletnej analizy karnej."""
    wyniki: list[WynikObliczenia] = field(default_factory=list)
    bledy: list[str] = field(default_factory=list)
    ostrzezenia: list[str] = field(default_factory=list)
    zalozenia: list[str] = field(default_factory=list)
    nieobslugiwane: list[str] = field(default_factory=list)


@dataclass
class WynikAnalizyZatarcia:
    """Wynik kompletnej analizy zatarcia."""
    wyniki: list[WynikObliczenia] = field(default_factory=list)
    bledy: list[str] = field(default_factory=list)
    ostrzezenia: list[str] = field(default_factory=list)
    zalozenia: list[str] = field(default_factory=list)
    nieobslugiwane: list[str] = field(default_factory=list)


def dodaj_lata(d: Optional[date], lata: int) -> Optional[date]:
    """Dodaje lata do daty, obsługuje None."""
    if d is None:
        return None
    return d + relativedelta(years=lata)


def _format_data(d: Optional[date]) -> str:
    if d is None:
        return "brak daty"
    return d.strftime("%d.%m.%Y")


def _czy_stara_przedawnienie(data_zawarcia: date) -> bool:
    """
    Sprawdza czy na umowę mają zastosowanie przepisy stare (przed nowelizacją 2018).
    Zgodnie z art. 118 k.c. w wersji przed 09.07.2018:
    - Umowy zawarte przed 09.07.2018: przepisy stare (brak końca roku)
    - Umowy zawarte po 09.07.2018: przepisy nowe (koniec roku)
    """
    return data_zawarcia < date(2018, 7, 9)


def _oblicz_termin_koncowy(start: date, lata: int, stosowac_koniec_roku: bool) -> date:
    """Oblicza termin końcowy przedawnienia z opcjonalną regułą końca roku."""
    termin = start + relativedelta(years=lata)
    if stosowac_koniec_roku:
        return date(termin.year, 12, 31)
    return termin


def analiza_cywilna(
    data_zawarcia_umowy: Optional[date],
    data_wymagalnosci: Optional[date],
    wpłaty: list[date],
    data_wyroku_cywilnego: Optional[date],
    data_wszcz_egzekucji: Optional[date],
    data_umor_egzekucji: Optional[date],
    lata_baza: int,
    podstawa_prawna: str,
    data_oceny: date
) -> WynikAnalizyCywilnej:
    """
    Analiza przedawnienia cywilnego umownego - przetwarzanie zdarzeń chronologicznie.
    Delikty/szkody obsługuje wyłącznie analiza_deliktowa.

    Zasady:
    - art. 118 k.c.: 3 lata od wymagalności (działalność gospodarcza)
    - art. 123 k.c.: uznanie długu (wpłata) -> bieg od nowa od daty uznania
    - art. 124 k.c.: wszczęcie egzekucji -> zawieszenie biegu do umorzenia
    - art. 124 § 2 k.c.: umorzenie egzekucji -> bieg od nowa od umorzenia
    - art. 125 k.c.: wyrok -> 6 lat od wyroku (reżim specjalny)
    - przepisy przejściowe 2018: umowy przed 09.07.2018 = bez końca roku
    """
    wynik = WynikAnalizyCywilnej()

    # Walidacja danych wejściowych
    if data_wymagalnosci is None:
        wynik.bledy.append("Brak daty wymagalności – analiza cywilna niemożliwa.")
        return wynik

    if data_zawarcia_umowy is None:
        # Jeśli brak daty zawarcia, zakładamy datę wymagalności (konwerwatywnie)
        data_zawarcia_umowy = data_wymagalnosci
        wynik.ostrzezenia.append("Brak daty zawarcia umowy – przyjmowano datę wymagalności jako datę zawarcia.")

    # Buduj oś czasu zdarzeń
    zdarzenia: list[ZdarzeniePrzedawnienia] = []

    # Reżim przedawnienia (stary/nowy) na podstawie daty ZAWARCIA umowy.
    stary_rezim = _czy_stara_przedawnienie(data_zawarcia_umowy)
    wynik.zalozenia.append(
        f"Data zawarcia umowy: {_format_data(data_zawarcia_umowy)} – "
        f"{'przepisy STARE (przed 09.07.2018, bez końca roku)' if stary_rezim else 'przepisy NOWE (po 09.07.2018, z końcem roku)'}"
    )
    wynik.zalozenia.append(f"Data wymagalności (początek biegu): {_format_data(data_wymagalnosci)}")

    # 1. Start biegu
    zdarzenia.append(ZdarzeniePrzedawnienia(
        typ=TypZdarzenia.START,
        data=data_wymagalnosci,
        opis="Początek biegu przedawnienia (wymagalność)"
    ))

    # 2. Wpłaty (tylko te po wymagalności)
    for w in sorted(wpłaty):
        if w >= data_wymagalnosci:
            zdarzenia.append(ZdarzeniePrzedawnienia(
                typ=TypZdarzenia.WPLATA,
                data=w,
                opis="Wpłata / uznanie długu (art. 123 k.c.)"
            ))

    # 3. Wyrok (jeśli jest)
    if data_wyroku_cywilnego:
        zdarzenia.append(ZdarzeniePrzedawnienia(
            typ=TypZdarzenia.WYROK,
            data=data_wyroku_cywilnego,
            opis="Prawomocny wyrok / nakaz zapłaty"
        ))

    # 4. Egzekucja
    if data_wszcz_egzekucji:
        zdarzenia.append(ZdarzeniePrzedawnienia(
            typ=TypZdarzenia.WYSZCZ_EGZEKUCJI,
            data=data_wszcz_egzekucji,
            opis="Wszczęcie egzekucji komorniczej"
        ))

    # 5. Umorzenie egzekucji
    if data_umor_egzekucji:
        zdarzenia.append(ZdarzeniePrzedawnienia(
            typ=TypZdarzenia.UMORZENIE_EGZEKUCJI,
            data=data_umor_egzekucji,
            opis="Prawomocne umorzenie egzekucji"
        ))

    # Sortuj chronologicznie
    zdarzenia.sort(key=lambda z: z.data)
    wynik.os_czasu = zdarzenia

    # Przetwarzaj zdarzenia sekwencyjnie
    aktualny_start = data_wymagalnosci
    aktualne_lata = lata_baza
    aktualna_podstawa = podstawa_prawna
    egzekucja_w_toku = False
    wyrok_uzyskany = False

    for i, zdarzenie in enumerate(zdarzenia):
        if zdarzenie.typ == TypZdarzenia.START:
            continue  # już obsłużone

        elif zdarzenie.typ == TypZdarzenia.WPLATA:
            if wyrok_uzyskany:
                # Po wyroku wpłata nie resetuje przedawnienia automatycznie
                wynik.ostrzezenia.append(
                    f"Wpłata {_format_data(zdarzenie.data)} PO wyroku: "
                    f"nie przesądza o przedawnieniu (art. 125 k.c. – reżim 6 lat od wyroku)."
                )
            elif egzekucja_w_toku:
                # W trakcie egzekucji wpłata nie ma wpływu na bieg (zawieszenie)
                wynik.zalozenia.append(
                    f"Wpłata {_format_data(zdarzenie.data)} w trakcie egzekucji: "
                    f"bieg przedawnienia zawieszony (art. 124 k.c.)."
                )
            else:
                # Uznanie długu przed wyrokiem i poza egzekucją -> nowy bieg (art. 123 k.c.)
                aktualny_start = zdarzenie.data
                aktualne_lata = lata_baza
                aktualna_podstawa = podstawa_prawna
                wynik.zalozenia.append(
                    f"Uznanie długu (wpłata) {_format_data(zdarzenie.data)}: "
                    f"nowy bieg przedawnienia od tej daty (art. 123 k.c.), "
                    f"{aktualne_lata} lat, podstawa: {aktualna_podstawa}"
                )

        elif zdarzenie.typ == TypZdarzenia.WYROK:
            # Wyrok zmienia reżim na 6 lat (art. 125 § 1 k.c.)
            wyrok_uzyskany = True
            aktualny_start = zdarzenie.data
            aktualne_lata = 6
            aktualna_podstawa = PODSTAWA_WYROK
            # Egzekucja kończy się wyrokiem (jeśli była)
            egzekucja_w_toku = False
            wynik.zalozenia.append(
                f"Wyrok {_format_data(zdarzenie.data)}: "
                f"reżim specjalny – 6 lat od wyroku (art. 125 § 1 k.c.)"
            )

        elif zdarzenie.typ == TypZdarzenia.WYSZCZ_EGZEKUCJI:
            if wyrok_uzyskany:
                # Egzekucja po wyroku – nie wpływa na przedawnienie cywilne (już 6 lat od wyroku)
                wynik.zalozenia.append(
                    f"Egzekucja {_format_data(zdarzenie.data)} po wyroku: "
                    f"nie wpływa na przedawnienie cywilne (reżim art. 125 k.c.)."
                )
            else:
                # Egzekucja przed wyrokiem – zawieszenie biegu (art. 124 k.c.)
                egzekucja_w_toku = True
                wynik.zalozenia.append(
                    f"Wszczęcie egzekucji {_format_data(zdarzenie.data)}: "
                    f"zawieszenie biegu przedawnienia (art. 124 § 1 k.c.)"
                )

        elif zdarzenie.typ == TypZdarzenia.UMORZENIE_EGZEKUCJI:
            if egzekucja_w_toku:
                # Umorzenie egzekucji przed wyrokiem -> bieg od nowa (art. 124 § 2 k.c.)
                egzekucja_w_toku = False
                aktualny_start = zdarzenie.data
                aktualne_lata = lata_baza
                aktualna_podstawa = podstawa_prawna
                wynik.zalozenia.append(
                    f"Umorzenie egzekucji {_format_data(zdarzenie.data)}: "
                    f"bieg przedawnienia od nowa (art. 124 § 2 k.c.), "
                    f"{aktualne_lata} lat od umorzenia, podstawa: {aktualna_podstawa}"
                )
            else:
                # Umorzenie bez egzekucji lub po wyroku
                if wyrok_uzyskany:
                    wynik.zalozenia.append(
                        f"Umorzenie egzekucji {_format_data(zdarzenie.data)} po wyroku: "
                        f"brak wpływu na przedawnienie (trwa 6 lat od wyroku)."
                    )
                else:
                    wynik.zalozenia.append(
                        f"Umorzenie egzekucji {_format_data(zdarzenie.data)} bez wcześniejszego wszczęcia: "
                        f"brak wpływu na przedawnienie."
                    )

    # Sprawdź czy egzekucja wciąż trwa
    if egzekucja_w_toku and data_umor_egzekucji is None:
        wynik.wyniki.append(WynikObliczenia(
            nazwa="Egzekucja w toku",
            termin=data_oceny,
            status="W_TOKU",
            podstawa_prawna="Art. 124 § 2 k.c.",
            zalozenia=[f"Wszczęcie egzekucji: {_format_data(data_wszcz_egzekucji)}", "Brak umorzenia – postępowanie trwa"],
            ostrzezenia=["Przedawnienie zawieszone do prawomocnego zakończenia egzekucji."],
            orientacyjny=True
        ))
        return wynik

    # Oblicz ostateczny termin
    stosowac_koniec_roku = (not stary_rezim) and (not wyrok_uzyskany)
    
    if wyrok_uzyskany:
        # Dla wyroku nie ma reguły końca roku (art. 125 k.c. – 6 lat od wyroku)
        stosowac_koniec_roku = False

    termin_ostateczny = _oblicz_termin_koncowy(aktualny_start, aktualne_lata, stosowac_koniec_roku)

    # Status
    if termin_ostateczny >= data_oceny:
        status = "OK"
        komunikacja = f"Brak przedawnienia – roszczenie ważne do {_format_data(termin_ostateczny)}."
    else:
        status = "PRZEDAWNIONE"
        komunikacja = f"Przedawnienie – termin upłynął {_format_data(termin_ostateczny)}."

    if stosowac_koniec_roku:
        komunikacja += " (zastosowano regułę końca roku – art. 118 k.c.)"
    else:
        komunikacja += " (bez reguły końca roku)"

    wynik.wyniki.append(WynikObliczenia(
        nazwa=f"Przedawnienie cywilne [{aktualna_podstawa}]",
        termin=termin_ostateczny,
        status=status,
        podstawa_prawna=aktualna_podstawa,
        zalozenia=wynik.zalozenia.copy(),
        ostrzezenia=[komunikacja] + wynik.ostrzezenia,
        orientacyjny=False
    ))

    return wynik


def _oblicz_termin_deliktowy(
    data_zdarzenia: date,
    data_dowiedzenia: date,
    czy_przestepstwo: bool,
    czy_umyslne: bool,
    typ_odpowiedzialnosci: TypOdpowiedzialnosci
) -> tuple[date, str, list[str], list[str], tuple[int, Optional[int], str]]:
    """
    Oblicza termin przedawnienia szkody (art. 442¹ k.c. / art. 291 k.p.).
    Zwraca: (termin, podstawa_prawna, zalozenia, ostrzezenia, parametry_resetu),
    gdzie parametry_resetu = (lata_od_resetu, lata_capu_od_zdarzenia, podstawa_capu).
    """
    zalozenia: list[str] = []
    ostrzezenia: list[str] = []

    if czy_przestepstwo:
        # Art. 442¹ § 2 k.c.: 20 lat od popełnienia przestępstwa
        termin = dodaj_lata(data_zdarzenia, 20)
        podstawa = PODSTAWA_PRZESTEPSTWO
        parametry_resetu = (20, None, "art. 442¹ § 2 k.c.")
        zalozenia.append(
            "Szkoda wynikła ze zbrodni lub występku: 20 lat od dnia popełnienia "
            "przestępstwa, bez względu na moment dowiedzenia się o szkodzie "
            "(art. 442¹ § 2 k.c.)."
        )
        if typ_odpowiedzialnosci == TypOdpowiedzialnosci.PRACOWNICZA:
            zalozenia.append(
                "Odpowiedzialność pracownicza przy szkodzie z przestępstwa: 20-letni "
                "termin z art. 442¹ § 2 k.c."
            )
        return termin, podstawa, zalozenia, ostrzezenia, parametry_resetu

    if typ_odpowiedzialnosci == TypOdpowiedzialnosci.PRACOWNICZA:
        if czy_umyslne:
            # Art. 291 § 3 k.p. -> przepisy k.c. (art. 442¹ § 1): 3 lata od dowiedzenia, max 10 lat
            termin_3_lata = dodaj_lata(data_dowiedzenia, 3)
            termin_10_lat = dodaj_lata(data_zdarzenia, 10)
            termin = min(termin_3_lata, termin_10_lat)
            podstawa = PODSTAWA_PRACOWNICZA_UMYSLNA
            parametry_resetu = (3, 10, "art. 442¹ § 1 k.c.")
            zalozenia.append(
                "Szkoda wyrządzona przez pracownika umyślnie: stosuje się przepisy "
                "Kodeksu cywilnego (art. 291 § 3 k.p.), tj. 3 lata od dowiedzenia się "
                "o szkodzie i osobie obowiązanej, nie dłużej niż 10 lat od zdarzenia "
                "(art. 442¹ § 1 k.c.)."
            )
            if termin_10_lat < termin_3_lata:
                zalozenia.append(
                    "Zastosowano granicę 10 lat od zdarzenia (art. 442¹ § 1 k.c.) – "
                    "jest krótsza niż 3 lata od dowiedzenia się."
                )
        else:
            # Art. 291 § 2 k.p.: 1 rok od powzięcia wiadomości, nie później niż 3 lata od wyrządzenia
            termin_1_rok = dodaj_lata(data_dowiedzenia, 1)
            termin_3_lata = dodaj_lata(data_zdarzenia, 3)
            termin = min(termin_1_rok, termin_3_lata)
            podstawa = PODSTAWA_PRACOWNICZA
            parametry_resetu = (1, 3, "art. 291 § 2 k.p.")
            zalozenia.append(
                "Odpowiedzialność pracownicza (nieumyślna): 1 rok od dnia, w którym "
                "pracodawca powziął wiadomość o wyrządzeniu szkody i o osobie obowiązanej "
                "do jej naprawienia, nie później niż 3 lata od jej wyrządzenia "
                "(art. 291 § 2 k.p.)."
            )
            if termin_3_lata < termin_1_rok:
                zalozenia.append(
                    "Zastosowano granicę 3 lat od wyrządzenia szkody (art. 291 § 2 k.p.) – "
                    "jest krótsza niż rok od powzięcia wiadomości."
                )
        return termin, podstawa, zalozenia, ostrzezenia, parametry_resetu

    # Art. 442¹ § 1 k.c.: 3 lata od dowiedzenia się, max 10 lat od zdarzenia
    termin_3_lata = dodaj_lata(data_dowiedzenia, 3)
    termin_10_lat = dodaj_lata(data_zdarzenia, 10)
    termin = min(termin_3_lata, termin_10_lat)
    podstawa = PODSTAWA_DELIKTOWA
    parametry_resetu = (3, 10, "art. 442¹ § 1 k.c.")
    zalozenia.append(
        "Czyn niedozwolony bez kwalifikacji karnej: 3 lata od dnia dowiedzenia się "
        "o szkodzie i o osobie obowiązanej do jej naprawienia (art. 442¹ § 1 k.c.)."
    )
    if termin_10_lat < termin_3_lata:
        zalozenia.append(
            "Zastosowano granicę 10 lat od zdarzenia wywołującego szkodę "
            "(art. 442¹ § 1 k.c.) – jest krótsza niż 3 lata od dowiedzenia się."
        )
        ostrzezenia.append(
            "Termin 3 lat od dowiedzenia się upłynąłby później, ale został ograniczony "
            "bezwzględnym terminem 10 lat od zdarzenia (art. 442¹ § 1 k.c.)."
        )
    else:
        zalozenia.append(
            f"Granica 10 lat od zdarzenia ({_format_data(termin_10_lat)}) nie została "
            f"przekroczona – obowiązuje termin 3 lat od dowiedzenia się."
        )

    return termin, podstawa, zalozenia, ostrzezenia, parametry_resetu


def analiza_deliktowa(
    data_zdarzenia: Optional[date],
    data_dowiedzenia_o_szkodzie: Optional[date],
    czy_przestepstwo: bool,
    czy_umyslne: bool,
    typ_odpowiedzialnosci: TypOdpowiedzialnosci,
    wpłaty: list[date],
    data_wyroku_cywilnego: Optional[date],
    data_wszcz_egzekucji: Optional[date],
    data_umor_egzekucji: Optional[date],
    data_oceny: date
) -> WynikAnalizyCywilnej:
    """
    Analiza przedawnienia szkody (delikt / odpowiedzialność pracownicza).

    Zasady:
    - art. 442¹ § 1 k.c.: 3 lata od dowiedzenia się o szkodzie i sprawcy,
      nie dłużej niż 10 lat od zdarzenia (szkoda bez kwalifikacji karnej)
    - art. 442¹ § 2 k.c.: 20 lat od popełnienia przestępstwa (szkoda z przestępstwa)
    - art. 291 § 2 k.p.: 1 rok od powzięcia wiadomości o szkodzie, nie później niż
      3 lata od jej wyrządzenia (odpowiedzialność pracownicza – nieumyślna)
    - art. 291 § 3 k.p.: szkoda umyślna pracownika – stosuje się przepisy k.c.
      (art. 442¹ § 1 k.c.: 3 lata od dowiedzenia się, max 10 lat)
    - brak reguły końca roku (art. 118 § 1 k.c. nie dotyczy 442¹ k.c.)
    - zdarzenia (wpłaty, wyrok, egzekucja) przetwarzane chronologicznie

    Osobne daty:
    - data_zdarzenia: moment wyrządzenia szkody
    - data_dowiedzenia_o_szkodzie: moment uzyskania wiedzy o szkodzie i sprawcy
    """
    wynik = WynikAnalizyCywilnej()

    if data_zdarzenia is None:
        wynik.bledy.append("Brak daty zdarzenia wywołującego szkodę – analiza niemożliwa.")
        return wynik

    if data_dowiedzenia_o_szkodzie is None and not czy_przestepstwo:
        wynik.bledy.append(
            "Brak daty dowiedzenia się o szkodzie i sprawcy – wymagana dla szkody "
            "bez kwalifikacji karnej (art. 442¹ § 1 k.c.)."
        )
        return wynik

    # Dla szkody z przestępstwa data dowiedzenia się nie determinuje terminu,
    # ale nadal przydaje się do opisu.
    if data_dowiedzenia_o_szkodzie is None:
        data_dowiedzenia_o_szkodzie = data_zdarzenia

    # Informacje o stronie zdarzenia
    wynik.zalozenia.append(f"Data zdarzenia wywołującego szkodę: {_format_data(data_zdarzenia)}")
    wynik.zalozenia.append(
        f"Data dowiedzenia się o szkodzie i sprawcy: {_format_data(data_dowiedzenia_o_szkodzie)}"
    )
    if typ_odpowiedzialnosci == TypOdpowiedzialnosci.PRACOWNICZA:
        wynik.zalozenia.append(
            f"Reżim: odpowiedzialność pracownicza "
            f"{'(umyślna – przepisy k.c.)' if czy_umyslne else '(nieumyślna)'}"
        )
    else:
        wynik.zalozenia.append("Reżim: odpowiedzialność deliktowa (osoba trzecia)")

    # Oblicz termin bazowy dla szkody
    termin_bazowy, podstawa, zal_delikt, ostrz_delikt, reset_params = _oblicz_termin_deliktowy(
        data_zdarzenia, data_dowiedzenia_o_szkodzie, czy_przestepstwo, czy_umyslne, typ_odpowiedzialnosci
    )
    wynik.zalozenia.extend(zal_delikt)

    # Buduj oś czasu zdarzeń
    zdarzenia: list[ZdarzeniePrzedawnienia] = []
    zdarzenia.append(ZdarzeniePrzedawnienia(
        typ=TypZdarzenia.START,
        data=data_dowiedzenia_o_szkodzie if not czy_przestepstwo else data_zdarzenia,
        opis="Początek biegu przedawnienia szkody"
    ))

    for w in sorted(wpłaty):
        if w >= data_zdarzenia:
            zdarzenia.append(ZdarzeniePrzedawnienia(
                typ=TypZdarzenia.WPLATA,
                data=w,
                opis="Wpłata / uznanie roszczenia odszkodowawczego (art. 123 k.c.)"
            ))

    if data_wyroku_cywilnego:
        zdarzenia.append(ZdarzeniePrzedawnienia(
            typ=TypZdarzenia.WYROK,
            data=data_wyroku_cywilnego,
            opis="Prawomocny wyrok / nakaz zapłaty"
        ))

    if data_wszcz_egzekucji:
        zdarzenia.append(ZdarzeniePrzedawnienia(
            typ=TypZdarzenia.WYSZCZ_EGZEKUCJI,
            data=data_wszcz_egzekucji,
            opis="Wszczęcie egzekucji komorniczej"
        ))

    if data_umor_egzekucji:
        zdarzenia.append(ZdarzeniePrzedawnienia(
            typ=TypZdarzenia.UMORZENIE_EGZEKUCJI,
            data=data_umor_egzekucji,
            opis="Prawomocne umorzenie egzekucji"
        ))

    zdarzenia.sort(key=lambda z: z.data)
    wynik.os_czasu = zdarzenia

    # Przetwarzaj zdarzenia sekwencyjnie
    aktualny_start = zdarzenia[0].data
    aktualna_podstawa = podstawa
    egzekucja_w_toku = False
    wyrok_uzyskany = False

    for zdarzenie in zdarzenia:
        if zdarzenie.typ == TypZdarzenia.START:
            continue

        elif zdarzenie.typ == TypZdarzenia.WPLATA:
            if wyrok_uzyskany:
                wynik.ostrzezenia.append(
                    f"Wpłata {_format_data(zdarzenie.data)} PO wyroku: "
                    f"nie przesądza o przedawnieniu (reżim art. 125 k.c.)."
                )
            elif egzekucja_w_toku:
                wynik.zalozenia.append(
                    f"Wpłata {_format_data(zdarzenie.data)} w trakcie egzekucji: "
                    f"bieg przedawnienia zawieszony (art. 124 k.c.)."
                )
            else:
                aktualny_start = zdarzenie.data
                aktualna_podstawa = podstawa
                wynik.zalozenia.append(
                    f"Uznanie roszczenia (wpłata) {_format_data(zdarzenie.data)}: "
                    f"nowy bieg przedawnienia od tej daty (art. 123 k.c. w zw. z art. 442¹ k.c.)."
                )

        elif zdarzenie.typ == TypZdarzenia.WYROK:
            wyrok_uzyskany = True
            aktualny_start = zdarzenie.data
            aktualna_podstawa = PODSTAWA_WYROK
            egzekucja_w_toku = False
            wynik.zalozenia.append(
                f"Wyrok {_format_data(zdarzenie.data)}: reżim 6 lat od wyroku (art. 125 § 1 k.c.)."
            )

        elif zdarzenie.typ == TypZdarzenia.WYSZCZ_EGZEKUCJI:
            if wyrok_uzyskany:
                wynik.zalozenia.append(
                    f"Egzekucja {_format_data(zdarzenie.data)} po wyroku: "
                    f"nie wpływa na przedawnienie (reżim art. 125 k.c.)."
                )
            else:
                egzekucja_w_toku = True
                wynik.zalozenia.append(
                    f"Wszczęcie egzekucji {_format_data(zdarzenie.data)}: "
                    f"zawieszenie biegu przedawnienia (art. 124 § 1 k.c.)."
                )

        elif zdarzenie.typ == TypZdarzenia.UMORZENIE_EGZEKUCJI:
            if egzekucja_w_toku:
                egzekucja_w_toku = False
                aktualny_start = zdarzenie.data
                aktualna_podstawa = podstawa
                wynik.zalozenia.append(
                    f"Umorzenie egzekucji {_format_data(zdarzenie.data)}: "
                    f"bieg przedawnienia od nowa (art. 124 § 2 k.c.)."
                )
            elif wyrok_uzyskany:
                wynik.zalozenia.append(
                    f"Umorzenie egzekucji {_format_data(zdarzenie.data)} po wyroku: "
                    f"brak wpływu na przedawnienie."
                )
            else:
                wynik.zalozenia.append(
                    f"Umorzenie egzekucji {_format_data(zdarzenie.data)} bez wcześniejszego "
                    f"wszczęcia: brak wpływu na przedawnienie."
                )

    # Egzekucja w toku
    if egzekucja_w_toku and data_umor_egzekucji is None:
        wynik.wyniki.append(WynikObliczenia(
            nazwa="Egzekucja w toku",
            termin=data_oceny,
            status="W_TOKU",
            podstawa_prawna="Art. 124 § 2 k.c.",
            zalozenia=[f"Wszczęcie egzekucji: {_format_data(data_wszcz_egzekucji)}", "Brak umorzenia – postępowanie trwa"],
            ostrzezenia=["Przedawnienie zawieszone do prawomocnego zakończenia egzekucji."],
            orientacyjny=True
        ))
        return wynik

    # Oblicz ostateczny termin
    if wyrok_uzyskany:
        termin_ostateczny = dodaj_lata(aktualny_start, 6)
    else:
        # Jeśli wpłaty/umorzenie przesunęły start, przelicz termin od nowego startu.
        # Dla reżimów z bezwzględną granicą od zdarzenia (art. 442¹ § 1 k.c.,
        # art. 291 § 2 k.p.) reset nie może jej wydłużyć; dla art. 442¹ § 2 k.c.
        # (20 lat) takiej granicy nie ma – po przerwaniu bieg rozpoczyna się na nowo.
        if aktualny_start != zdarzenia[0].data:
            lata_resetu, lata_cap, podstawa_cap = reset_params
            termin_od_resetu = dodaj_lata(aktualny_start, lata_resetu)
            if lata_cap is None:
                termin_ostateczny = termin_od_resetu
                wynik.ostrzezenia.append(
                    f"Uznanie/umorzenie {_format_data(aktualny_start)}: bieg przedawnienia "
                    f"rozpoczyna się na nowo (art. 124 § 1 k.c.). Termin 20 lat z "
                    f"art. 442¹ § 2 k.c. nie jest limitem nieprzerywalnym (stanowisko dominujące)."
                )
            else:
                termin_cap = dodaj_lata(data_zdarzenia, lata_cap)
                termin_ostateczny = min(termin_od_resetu, termin_cap)
                if termin_cap < termin_od_resetu:
                    wynik.zalozenia.append(
                        f"Reset biegu ({_format_data(aktualny_start)}) ograniczony bezwzględną "
                        f"granicą {lata_cap} lat od zdarzenia ({_format_data(termin_cap)}) "
                        f"({podstawa_cap})."
                    )
        else:
            termin_ostateczny = termin_bazowy

    # Status
    if termin_ostateczny >= data_oceny:
        status = "OK"
        komunikacja = f"Brak przedawnienia – roszczenie ważne do {_format_data(termin_ostateczny)}."
    else:
        status = "PRZEDAWNIONE"
        komunikacja = f"Przedawnienie – termin upłynął {_format_data(termin_ostateczny)}."

    komunikacja += " (bez reguły końca roku – art. 442¹ k.c.)"

    wynik.wyniki.append(WynikObliczenia(
        nazwa=f"Przedawnienie szkody [{aktualna_podstawa}]",
        termin=termin_ostateczny,
        status=status,
        podstawa_prawna=aktualna_podstawa,
        zalozenia=wynik.zalozenia.copy(),
        ostrzezenia=[komunikacja] + ostrz_delikt + wynik.ostrzezenia,
        orientacyjny=False
    ))

    return wynik


def analiza_karna(
    data_czynu: Optional[date],
    lata_karne: int,
    data_wszcz_k: Optional[date],
    data_umor_k: Optional[date],
    data_oceny: date,
    czy_oskarzenie_prywatne: bool = False,
    data_dowiedzenia_o_sprawcy: Optional[date] = None
) -> WynikAnalizyKarne:
    """
    Analiza przedawnienia karalności (art. 101, 102 k.k.).

    Obsługiwane:
    - art. 101 § 1 k.k.: ustawowy termin przedawnienia karalności zależny od
      kwalifikacji czynu (przekazywany jako lata_karne)
    - art. 101 § 2 k.k.: przestępstwa ścigane z oskarżenia prywatnego – 1 rok od
      dowiedzenia się przez pokrzywdzonego o osobie sprawcy, nie później niż
      3 lata od popełnienia czynu (wymaga data_dowiedzenia_o_sprawcy)
    - art. 102 k.k.: przedłużenie o 10 lat, jeżeli w okresie przedawnienia
      wszczęto postępowanie PRZECIWKO OSOBIE

    Nieobsługiwane (zgłaszane jawnie):
    - przepisy szczególne przewidujące inne terminy przedawnienia
    - wydłużenie karalności w trybie art. 102 wobec braku daty wszczęcia
      postępowania przeciwko osobie

    Uwaga: data_umor_k ma charakter wyłącznie ewidencyjny (nie zmienia terminu
    karalności) – skutek umorzenia zależy od podstawy prawnej i wymaga oceny
    indywidualnej.
    """
    wynik = WynikAnalizyKarne()

    if data_czynu is None:
        wynik.bledy.append("Brak daty czynu – nie można obliczyć przedawnienia karalności.")
        return wynik

    wynik.zalozenia.append(f"Data czynu: {_format_data(data_czynu)}")

    if czy_oskarzenie_prywatne:
        if data_dowiedzenia_o_sprawcy is None:
            wynik.wyniki.append(WynikObliczenia(
                nazwa="Karalność – dane niewystarczające (art. 101 § 2 k.k.)",
                termin=data_oceny,
                status="BRAK_DANYCH",
                podstawa_prawna="Art. 101 § 2 k.k.",
                zalozenia=wynik.zalozenia.copy(),
                ostrzezenia=[
                    "Przestępstwo ścigane z oskarżenia prywatnego: brak daty dowiedzenia się "
                    "przez pokrzywdzonego o osobie sprawcy. Podaj tę datę, aby obliczyć 1-roczny "
                    "termin (art. 101 § 2 k.k.)."
                ],
                orientacyjny=True
            ))
            return wynik

        termin_1_rok = dodaj_lata(data_dowiedzenia_o_sprawcy, 1)
        termin_3_lata = dodaj_lata(data_czynu, 3)
        termin_pierwotny = min(termin_1_rok, termin_3_lata)
        podstawa_prawna = "Art. 101 § 2, art. 102 k.k."
        nazwa = "Orientacyjne ustanie karalności (art. 101 § 2 k.k.)"

        wynik.zalozenia.append("Przestępstwo ścigane z oskarżenia prywatnego – termin z art. 101 § 2 k.k.")
        wynik.zalozenia.append(f"Data dowiedzenia się o osobie sprawcy: {_format_data(data_dowiedzenia_o_sprawcy)}")
        wynik.zalozenia.append(f"1 rok od dowiedzenia się o sprawcy: {_format_data(termin_1_rok)}")
        wynik.zalozenia.append(f"Bezwzględny limit 3 lat od czynu: {_format_data(termin_3_lata)}")
        if termin_3_lata < termin_1_rok:
            wynik.zalozenia.append(
                "Zastosowano bezwzględny limit 3 lat od popełnienia czynu (art. 101 § 2 k.k.) – "
                "jest krótszy niż rok od dowiedzenia się o sprawcy."
            )
        wynik.zalozenia.append(f"Pierwotny termin: {_format_data(termin_pierwotny)}")
    else:
        termin_pierwotny = dodaj_lata(data_czynu, lata_karne)
        if termin_pierwotny is None:
            wynik.bledy.append("Nie udało się obliczyć terminu karnego.")
            return wynik
        podstawa_prawna = "Art. 101 § 1, art. 102 k.k."
        nazwa = "Orientacyjne ustanie karalności (art. 101/102 k.k.)"
        wynik.zalozenia.append(
            f"Ustawowy termin przedawnienia karalności: {lata_karne} lat (art. 101 § 1 k.k.)"
        )
        wynik.zalozenia.append(f"Pierwotny termin: {_format_data(termin_pierwotny)}")

    termin_karny = termin_pierwotny

    # Art. 102 k.k.: przedłużenie karalności o 10 lat
    if data_wszcz_k:
        if data_wszcz_k <= termin_pierwotny:
            termin_karny = dodaj_lata(termin_pierwotny, 10)
            wynik.zalozenia.append(
                f"Wszczęcie postępowania przeciwko osobie: {_format_data(data_wszcz_k)} "
                f"(w okresie przedawnienia)"
            )
            wynik.zalozenia.append("Karalność przedłużona o 10 lat (art. 102 k.k.).")
            wynik.ostrzezenia.append(
                "Art. 102 k.k.: wszczęto postępowanie przeciwko osobie przed upływem "
                "pierwotnego terminu – karalność przedłużona o 10 lat."
            )
        else:
            wynik.ostrzezenia.append(
                "Postępowanie karne wszczęto po upływie pierwotnego terminu przedawnienia "
                "karalności – art. 102 k.k. nie wydłuża karalności."
            )
    else:
        wynik.ostrzezenia.append(
            "Brak daty wszczęcia postępowania przeciwko osobie – nie można ustalić, "
            "czy zachodzi przedłużenie karalności o 10 lat (art. 102 k.k.). "
            "Podaj datę wszczęcia, aby uzyskać pełny wynik."
        )

    if data_umor_k:
        wynik.zalozenia.append(f"Umorzenie postępowania: {_format_data(data_umor_k)}")
        wynik.ostrzezenia.append(
            "Skutek umorzenia (możliwość podjęcia postępowania) zależy od jego podstaw "
            "prawnych – wymaga oceny indywidualnej."
        )

    if termin_karny >= data_oceny:
        status = "TRWA"
        komunikacja = (
            f"Karalność trwa do {_format_data(termin_karny)}: zawiadomienie organów ścigania / "
            f"kontynuowanie sprawy jest prawnie możliwe."
        )
    else:
        status = "WYGASŁE"
        komunikacja = (
            f"Karalność wygasła {_format_data(termin_karny)}: organy z urzędu odmówią "
            f"wszczęcia lub umorzą postępowanie (przedawnienie)."
        )

    wynik.wyniki.append(WynikObliczenia(
        nazwa=nazwa,
        termin=termin_karny,
        status=status,
        podstawa_prawna=podstawa_prawna,
        zalozenia=wynik.zalozenia.copy(),
        ostrzezenia=[komunikacja] + wynik.ostrzezenia,
        orientacyjny=True
    ))

    return wynik


def analiza_zatarcia(
    data_wyroku_k: Optional[date],
    data_wykonania: Optional[date],
    lata_zatarcia: int,
    data_oceny: date,
    lata_zatarcia_wyjatek: Optional[int] = None,
    rodzaj_kary: str = ""
) -> WynikAnalizyZatarcia:
    """
    Analiza zatarcia skazania (art. 107 k.k.).

    - art. 107 § 1 k.k.: zatarcie z mocy prawa po 3 / 5 / 10 latach
    - art. 107 § 4 k.k.: zatarcie w drodze wyjątku na wniosek skazanego
      (po 5 latach od wykonania kary pozbawienia wolności)

    Brak daty wykonania kary -> wynik niepewny (BRAK_DANYCH).
    NIE substytuujemy datą wyroku.
    """
    wynik = WynikAnalizyZatarcia()

    if data_wyroku_k is None:
        # Brak wyroku – analiza pomijana (nie błąd)
        return wynik

    wynik.zalozenia.append(f"Data wyroku skazującego: {_format_data(data_wyroku_k)}")
    if rodzaj_kary:
        wynik.zalozenia.append(f"Rodzaj kary: {rodzaj_kary}")

    # Bez daty wykonania kary nie da się rzetelnie wyznaczyć terminu
    if data_wykonania is None:
        wynik.wyniki.append(WynikObliczenia(
            nazwa="Zatarcie skazania – dane niewystarczające",
            termin=data_oceny,
            status="BRAK_DANYCH",
            podstawa_prawna="Art. 107 k.k.",
            zalozenia=wynik.zalozenia.copy(),
            ostrzezenia=[
                "Brak daty wykonania / zakończenia / darowania kary. Termin zatarcia liczy się "
                "od wykonania (lub darowania, albo przedawnienia wykonania) kary – "
                "podaj tę datę, aby uzyskać rzetelny wynik."
            ],
            orientacyjny=True
        ))
        return wynik

    wynik.zalozenia.append(f"Data wykonania / darowania / zakończenia kary: {_format_data(data_wykonania)}")

    # --- Zatarcie automatyczne (art. 107 § 1 k.k.) ---
    termin_automatyczny = dodaj_lata(data_wykonania, lata_zatarcia)
    if termin_automatyczny is None:
        wynik.bledy.append("Nie udało się obliczyć terminu zatarcia.")
        return wynik

    if termin_automatyczny < data_oceny:
        status_auto = "ZATARTE"
        kom_auto = (
            f"Zatarcie z mocy prawa (art. 107 § 1 k.k.): nastąpiło "
            f"{_format_data(termin_automatyczny)} ({lata_zatarcia} lat od wykonania kary)."
        )
    else:
        status_auto = "W_KRK"
        kom_auto = (
            f"Zatarcie z mocy prawa (art. 107 § 1 k.k.): skazanie pozostaje w KRK do "
            f"{_format_data(termin_automatyczny)} ({lata_zatarcia} lat od wykonania kary)."
        )

    wynik.wyniki.append(WynikObliczenia(
        nazwa="Zatarcie z mocy prawa (art. 107 § 1 k.k.)",
        termin=termin_automatyczny,
        status=status_auto,
        podstawa_prawna="Art. 107 § 1 k.k.",
        zalozenia=wynik.zalozenia.copy() + [f"Okres zatarcia z mocy prawa: {lata_zatarcia} lat"],
        ostrzezenia=[kom_auto],
        orientacyjny=True
    ))

    # --- Zatarcie w drodze wyjątku na wniosek (art. 107 § 4 k.k.) ---
    if lata_zatarcia_wyjatek is not None:
        termin_wyjatek = dodaj_lata(data_wykonania, lata_zatarcia_wyjatek)
        if termin_wyjatek is not None and termin_wyjatek < termin_automatyczny:
            if termin_wyjatek < data_oceny:
                status_wyj = "ZATARTE"
                kom_wyj = (
                    f"Możliwe zatarcie w drodze wyjątku (art. 107 § 4 k.k.): termin "
                    f"minimalny upłynął {_format_data(termin_wyjatek)} – wymaga wniosku do sądu "
                    f"i spełnienia dodatkowych przesłanek."
                )
            else:
                status_wyj = "MOZLIWE_WCZEŚNIEJ"
                kom_wyj = (
                    f"Możliwe wcześniejsze zatarcie w drodze wyjątku na wniosek (art. 107 § 4 k.k.): "
                    f"od {_format_data(termin_wyjatek)}, po spełnieniu przesłanek (m.in. przestrzeganie "
                    f"porządku prawnego)."
                )

            wynik.wyniki.append(WynikObliczenia(
                nazwa="Zatarcie w drodze wyjątku na wniosek (art. 107 § 4 k.k.)",
                termin=termin_wyjatek,
                status=status_wyj,
                podstawa_prawna="Art. 107 § 4 k.k.",
                zalozenia=wynik.zalozenia.copy() + [
                    f"Minimalny okres do wniosku: {lata_zatarcia_wyjatek} lat od wykonania kary",
                    "Zatarcie w drodze wyjątku następuje wyłącznie na wniosek skazanego i zależy od decyzji sądu.",
                ],
                ostrzezenia=[kom_wyj],
                orientacyjny=True
            ))

    return wynik