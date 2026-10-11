from datetime import date
from typing import Optional


def waliduj_dane(
    data_zawarcia_umowy: Optional[date],
    data_wymagalnosci: Optional[date],
    data_zdarzenia: Optional[date],
    data_dowiedzenia: Optional[date],
    wpłaty: list[date],
    data_wyroku_cywilnego: Optional[date],
    data_wszcz_egzekucji: Optional[date],
    data_umor_egzekucji: Optional[date],
    data_czynu: Optional[date],
    wszczecie_k: Optional[date],
    umorzenie_k: Optional[date],
    wyrok_k: Optional[date],
    data_wykonania_kary: Optional[date],
    czy_delikt: bool
) -> tuple[list[str], list[str]]:
    """
    Waliduje spójność danych wejściowych kalkulatora.

    Zwraca: (lista_błędów, lista_ostrzeżeń).
    Błędy blokują obliczenia; ostrzeżenia informują o niespójnościach logicznych.
    """
    bledy: list[str] = []
    ostrzezenia: list[str] = []

    if not czy_delikt:
        # --- Roszczenia umowne ---
        if data_wymagalnosci is not None:
            if data_zawarcia_umowy and data_wymagalnosci < data_zawarcia_umowy:
                bledy.append("🔴 Data wymagalności nie może być wcześniejsza niż data zawarcia umowy.")

            for w in wpłaty:
                if w < data_wymagalnosci:
                    bledy.append(
                        f"🔴 Wpłata {w.strftime('%d.%m.%Y')} nie może być wcześniejsza niż data wymagalności."
                    )

            if data_wyroku_cywilnego and data_wyroku_cywilnego < data_wymagalnosci:
                bledy.append("🔴 Wyrok cywilny nie może być wcześniejszy niż data wymagalności.")

            if data_wszcz_egzekucji and data_wszcz_egzekucji < data_wymagalnosci:
                bledy.append("🔴 Egzekucja nie może być wszczęta przed datą wymagalności.")
    else:
        # --- Szkody / odpowiedzialność pracownicza ---
        if data_zdarzenia is not None and data_dowiedzenia is not None and data_dowiedzenia < data_zdarzenia:
            bledy.append("🔴 Data dowiedzenia się o szkodzie nie może być wcześniejsza niż data zdarzenia.")

        for w in wpłaty:
            ref = data_dowiedzenia if data_dowiedzenia else data_zdarzenia
            if ref and w < ref:
                bledy.append(
                    f"🔴 Wpłata {w.strftime('%d.%m.%Y')} nie może być wcześniejsza niż data zdarzenia / dowiedzenia się o szkodzie."
                )

        for d, nazwa in [(data_wyroku_cywilnego, "Wyrok cywilny"), (data_wszcz_egzekucji, "Egzekucja")]:
            if d and data_zdarzenia and d < data_zdarzenia:
                bledy.append(f"🔴 {nazwa} nie może być wcześniejszy/a niż data zdarzenia wywołującego szkodę.")

    # --- Egzekucja / umorzenie (niezależnie od reżimu) ---
    if data_wszcz_egzekucji and data_umor_egzekucji and data_umor_egzekucji < data_wszcz_egzekucji:
        bledy.append("🔴 Umorzenie egzekucji nie może nastąpić przed jej wszczęciem.")

    if data_wszcz_egzekucji is None and data_umor_egzekucji is not None:
        bledy.append("🔴 Umorzenie egzekucji wymaga daty wszczęcia egzekucji.")

    # --- Sfera karna ---
    if data_czynu and wszczecie_k and wszczecie_k < data_czynu:
        bledy.append("🔴 Wszczęcie postępowania karnego nie może nastąpić przed datą czynu.")

    if wszczecie_k and umorzenie_k and umorzenie_k < wszczecie_k:
        bledy.append("🔴 Umorzenie postępowania karnego nie może nastąpić przed jego wszczęciem.")

    if wszczecie_k is None and umorzenie_k is not None:
        bledy.append("🔴 Umorzenie postępowania karnego wymaga daty wszczęcia postępowania.")

    if wyrok_k and data_wykonania_kary and data_wykonania_kary < wyrok_k:
        bledy.append("🔴 Data wykonania kary nie może być wcześniejsza niż data wyroku.")

    if wyrok_k is None and data_wykonania_kary is not None:
        bledy.append("🔴 Data wykonania kary wymaga daty wyroku skazującego.")

    # --- Ostrzeżenia ---
    if not czy_delikt:
        ref_cywilna = data_wymagalnosci
    else:
        # Dla szkody z przestępstwa data dowiedzenia może być pusta —
        # wtedy punktem odniesienia jest data zdarzenia.
        ref_cywilna = data_dowiedzenia if data_dowiedzenia is not None else data_zdarzenia
    if data_czynu and ref_cywilna and data_czynu > ref_cywilna:
        ostrzezenia.append("⚠️ Data czynu jest późniejsza niż cywilna data bazowa. Sprawdź poprawność.")

    if data_wyroku_cywilnego and data_umor_egzekucji and data_umor_egzekucji < data_wyroku_cywilnego:
        ostrzezenia.append("⚠️ Umorzenie egzekucji jest wcześniejsze niż wyrok cywilny. Sprawdź daty.")

    return bledy, ostrzezenia