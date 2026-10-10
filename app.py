import streamlit as st
from datetime import date
from dateutil.relativedelta import relativedelta

# Ustawienia strony
st.set_page_config(page_title="Analiza prawna i windykacyjna", layout="wide")

# ─────────────────────────────────────────────
# BEZPIECZEŃSTWO: CORS, XSRF, HEADERS
# ─────────────────────────────────────────────
def configure_security_headers():
    """Konfiguruje nagłówki bezpieczeństwa dla Streamlit."""
    # Streamlit nie pozwala na bezpośrednią modyfikację nagłówków HTTP,
    # ale możemy dodać meta tagi przez st.markdown
    st.markdown("""
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
    """, unsafe_allow_html=True)

configure_security_headers()

# ─────────────────────────────────────────────
# 0. SYSTEM LOGOWANIA (OCHRONA HASŁEM)
# ─────────────────────────────────────────────
def check_password() -> bool:
    """Zwraca True, jeśli hasło jest poprawne. Obsługuje brak sekretu."""
    def password_entered():
        expected = st.secrets.get("HASLO_DO_APLIKACJI")
        if expected is None:
            st.session_state["password_correct"] = False
            st.session_state["_password_error"] = "❌ Brak skonfigurowanego hasła w secrets (HASLO_DO_APLIKACJI). Skontaktuj się z administratorem."
            return
        if st.session_state["password"] == expected:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔒 Wprowadź hasło dostępu do kalkulatora:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔒 Wprowadź hasło dostępu do kalkulatora:", type="password", on_change=password_entered, key="password")
        error_msg = st.session_state.get("_password_error", "❌ Błędne hasło. Spróbuj ponownie.")
        st.error(error_msg)
        return False
    else:
        return True

if not check_password():
    st.stop()

# ─────────────────────────────────────────────
# WŁAŚCIWA APLIKACJA
# ─────────────────────────────────────────────
st.title("📝 Precyzyjna analiza przedawnienia (cywilne i karne)")

st.warning(
    "⚠️ **Ważne (Zastrzeżenie):** Narzędzie ma charakter pomocniczy i informacyjny. "
    "Część cywilna opiera się na podstawowych regułach art. 118, 123, 124, 125 i 442¹ k.c. "
    "Część karna (art. 101, 102, 107 k.k.) ma charakter wyłącznie orientacyjny. "
    "Wynik nie stanowi wiążącej porady prawnej."
)

MIN_DATE = date(2000, 1, 1)

# ─────────────────────────────────────────────
# 1. KATEGORYZACJA ROSZCZENIA
# ─────────────────────────────────────────────
st.subheader("Źródło roszczenia i podstawa cywilna")

kategoria_podmiotu = st.selectbox(
    "Grupa roszczeń",
    ["Klient spółki (Umowa pożyczki)", "Klient spółki (Karta kredytowa)", "Były pracownik spółki (Deficyt)", "Osoba trzecia (Deficyt)"]
)

czy_delikt = "Deficyt" in kategoria_podmiotu
czy_przestepstwo = False

if not czy_delikt:
    st.info("📌 **Podstawa cywilna:** Roszczenie związane z prowadzeniem działalności gospodarczej. Co do zasady: **3 lata** (art. 118 k.c.).")
    lata_cywilne_baza = 3
    podstawa_cywilna = "Art. 118 k.c. (działalność gospodarcza)"
else:
    rodzaj_zdarzenia = st.selectbox(
        "Rodzaj zdarzenia deficytowego",
        ["Przywłaszczenie zaliczek / zbiórek", "Nieuprawnione wypłaty BLIK / z karty", "Kradzież gotówki / karty", "Fałszowanie dowodów bankowania", "Umowy fikcyjne / na słupa"]
    )
    czy_przestepstwo = st.checkbox("Czy szkoda bezpośrednio wynika ze zbrodni lub występku (przestępstwa)?")

    if czy_przestepstwo:
        st.error("📌 **Podstawa cywilna:** Szkoda ze zbrodni lub występku. Przedawnienie: **20 lat** od popełnienia przestępstwa (art. 442¹ § 2 k.c.).")
        lata_cywilne_baza = 20
        podstawa_cywilna = "Art. 442¹ § 2 k.c. (szkoda z przestępstwa)"
    else:
        st.warning("📌 **Podstawa cywilna:** Czyn niedozwolony bez kwalifikacji karnej. Przedawnienie: **3 lata** od dnia dowiedzenia się o szkodzie ORAZ o osobie obowiązanej do jej naprawienia (art. 442¹ § 1 k.c.).")
        lata_cywilne_baza = 3
        podstawa_cywilna = "Art. 442¹ § 1 k.c. (szkoda deliktowa)"

# ─────────────────────────────────────────────
# 2. WPROWADZANIE DAT
# ─────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Oś czasu cywilna")
    etykieta_start_cywil = "Data dowiedzenia się o szkodzie i sprawcy" if czy_delikt else "Data zawarcia umowy / wymagalności"
    
    data_bazowa_cywilna = st.date_input(etykieta_start_cywil, value=None, min_value=MIN_DATE, help="Data, od której pierwotnie rozpoczął się bieg przedawnienia.")
    ostatnia_wplata = st.date_input("Data ostatniej wpłaty / uznania długu", value=None, min_value=MIN_DATE, help="Dobrowolna wpłata może stanowić tzw. niewłaściwe uznanie długu, ale skutek prawny zależy od okoliczności sprawy.")
    data_wyroku_cywilnego = st.date_input("Data prawomocnego wyroku cywilnego / nakazu", value=None, min_value=MIN_DATE, help="Prawomocne orzeczenie sądu wyznacza odrębny reżim przedawnienia.")

    st.markdown("---")
    data_wszcz_egzekucji = st.date_input("Data wszczęcia egzekucji", value=None, min_value=MIN_DATE, help="Data złożenia wniosku egzekucyjnego u komornika (przerywa bieg przedawnienia).")
    data_umor_egzekucji = st.date_input("Data prawomocnego umorzenia egzekucji", value=None, min_value=MIN_DATE, help="Data uprawomocnienia się postanowienia komornika o umorzeniu.")

with col2:
    st.subheader("Sfera karna i zatarcie (orientacyjnie)")
    data_czynu = st.date_input("Data popełnienia czynu (do obliczeń karnych)", value=None, min_value=MIN_DATE, help="Data samego czynu jest potrzebna do obliczenia przedawnienia karalności z art. 101 k.k.; w przypadku czynów skutkowych lub wielodniowych może być potrzebne dodatkowe doprecyzowanie.")

    OPCJE_KK = {
        "Oszustwo ogólne z art. 286 (występek > 5 lat, przedawnienie: 15 lat)": 15,
        "Oszustwo kredytowe, fałszerstwo, przywłaszczenie powierzone (występek 3-5 lat, przedawnienie: 10 lat)": 10,
        "Zwykłe przywłaszczenie (występek do 3 lat, przedawnienie: 5 lat)": 5,
        "Zbrodnia np. podrabianie środków płatniczych (przedawnienie: 20 lat)": 20
    }
    wybor_kk = st.selectbox("Kwalifikacja czynu (najczęstsze przestępstwa)", list(OPCJE_KK.keys()), help="Wybierz konkretny artykuł k.k., aby ustalić ustawowy okres przedawnienia karalności.")

    wszczecie_k = st.date_input("Data wszczęcia postępowania karnego (przeciwko osobie)", value=None, min_value=MIN_DATE, help="Przedstawienie zarzutów osobie fizycznej (przedłuża karalność o 10 lat).")
    umorzenie_k = st.date_input("Data umorzenia postępowania karnego", value=None, min_value=MIN_DATE)

    st.markdown("---")
    wyrok_k = st.date_input("Data wyroku karnego skazującego", value=None, min_value=MIN_DATE)
    data_wykonania_kary = st.date_input("Data wykonania / zakończenia / darowania kary (do zatarcia)", value=None, min_value=MIN_DATE, help="Od tej daty faktycznie liczy się termin do usunięcia wpisu z KRK (zatarcie).")

    OPCJE_ZATARCIA = {
        "Grzywna lub ograniczenie wolności (3 lata)": 3,
        "Pozbawienie wolności do 3 lat (5 lat)": 5,
        "Pozbawienie wolności powyżej 3 lat (10 lat)": 10
    }
    wybor_zatarcia = st.selectbox("Orzeczona kara (dla zatarcia skazania z art. 107 k.k.)", list(OPCJE_ZATARCIA.keys()), disabled=(wyrok_k is None), help="Rodzaj orzeczonej i wykonanej kary determinuje czas do zatarcia skazania.")

st.divider()

# ─────────────────────────────────────────────
# 3. FUNKCJE POMOCNICZE I ANALITYCZNE
# ─────────────────────────────────────────────
def dodaj_lata(d: date, lata: int) -> date:
    if d is None: return None
    return d + relativedelta(years=lata)

def analiza_cywilna(data_bazowa, wplata, wyrok, wszcz_egz, umor_egz, lata_baza, podstawa, czy_jest_delikt):
    wyniki, daty_kluczowe = [], {}
    dzis = date.today()

    if data_bazowa is None:
        return ["⚠️ Brak daty bazowej – analiza cywilna niemożliwa."], daty_kluczowe

    if wyrok:
        lata_cywil, aktualna_podstawa, start_cywil = 6, "Art. 125 § 1 k.c. (wyrok)", wyrok
    else:
        lata_cywil, aktualna_podstawa, start_cywil = lata_baza, podstawa, data_bazowa

    if wplata:
        if wyrok and wplata > wyrok:
            wyniki.append("ℹ️ **Uwaga:** Zarejestrowano wpłatę po dacie prawomocnego wyroku. Wpłata może mieć znaczenie dla oceny uznania roszczenia, ale nie przesądza automatycznie o skutkach przedawnieniowych.")
            start_cywil = wplata
        elif not wyrok and wplata > start_cywil:
            wyniki.append("ℹ️ **Uwaga:** Zarejestrowano wpłatę / uznanie długu. Może to stanowić uznanie roszczenia i przerwać bieg przedawnienia, ale skutek zależy od okoliczności sprawy.")
            start_cywil = wplata

    if umor_egz and umor_egz > start_cywil:
        start_cywil = umor_egz
        wyniki.append("ℹ️ **Uwaga:** Po prawomocnym umorzeniu egzekucji bieg przedawnienia co do zasady biegnie na nowo od tej daty.")

    if wszcz_egz is not None and umor_egz is None:
        wyniki.append("⏸️ **Egzekucja w toku:** Wszczęcie egzekucji przerwało bieg przedawnienia. Zgodnie z art. 124 § 2 k.c. przedawnienie nie biegnie na nowo, dopóki postępowanie nie zostanie prawomocnie zakończone.")
    else:
        termin_podstawowy = dodaj_lata(start_cywil, lata_cywil)
        po_nowelizacji = start_cywil >= date(2018, 7, 9)
        to_czysty_delikt = (czy_jest_delikt and not wyrok)
        
        if po_nowelizacji and not to_czysty_delikt:
            termin_ostateczny = date(termin_podstawowy.year, 12, 31)
            adnotacja_3112 = " (przesunięto na koniec roku - art. 118 k.c.)"
        else:
            termin_ostateczny = termin_podstawowy
            adnotacja_3112 = " (bez reguły na koniec roku)"

        daty_kluczowe[f"Przedawnienie cywilne [{aktualna_podstawa}]"] = termin_ostateczny
        if termin_ostateczny >= dzis:
            wyniki.append(f"✅ **Brak przedawnienia cywilnego:** roszczenie ważne do {termin_ostateczny.strftime('%d.%m.%Y')}{adnotacja_3112}.")
        else:
            wyniki.append(f"❌ **Przedawnienie cywilne:** termin upłynął {termin_ostateczny.strftime('%d.%m.%Y')}{adnotacja_3112}.")

    return wyniki, daty_kluczowe

def analiza_karna(data_czynu_karna, lata_karne, data_wszcz_k, data_umor_k):
    wyniki, daty_kluczowe = [], {}
    dzis = date.today()

    if data_czynu_karna is None:
        wyniki.append("⚠️ **Brak daty czynu:** nie można obliczyć przedawnienia karalności bez daty popełnienia czynu.")
        return wyniki, daty_kluczowe

    termin_karny = dodaj_lata(data_czynu_karna, lata_karne)

    if data_wszcz_k:
        if data_wszcz_k <= termin_karny:
            termin_karny = dodaj_lata(termin_karny, 10)
            wyniki.append("ℹ️ **Art. 102 k.k.:** Wszczęto postępowanie przed upływem przedawnienia. Karalność czynu wydłuża się o 10 lat.")
        else:
            wyniki.append("❌ **Uwaga:** Postępowanie karne wszczęto po pierwotnym upływie terminu przedawnienia karalności.")
    else:
        wyniki.append("ℹ️ **Art. 102 k.k.:** Brak daty wszczęcia. Wyliczenia nie uwzględniają ewentualnego przedłużenia o 10 lat.")

    if data_umor_k:
        wyniki.append(f"ℹ️ **Umorzenie:** Postępowanie umorzono ({data_umor_k.strftime('%d.%m.%Y')}). Opcja podjęcia go na nowo zależy od podstaw prawnych umorzenia.")

    daty_kluczowe["* Orientacyjne ustanie karalności (Art. 101/102 k.k.)"] = termin_karny
    if termin_karny >= dzis:
        wyniki.append("⚠️ **Karalność trwa:** Zawiadomienie organów ścigania / kontynuowanie sprawy jest prawnie możliwe.")
    else:
        wyniki.append("❌ **Karalność wygasła:** Organy z urzędu odmówią wszczęcia lub umorzą postępowanie (przedawnienie).")

    return wyniki, daty_kluczowe

def analiza_zatarcia(data_wyroku_k, data_wykonania, lata_zat):
    wyniki, daty_kluczowe = [], {}
    dzis = date.today()

    if data_wyroku_k is None: return wyniki, daty_kluczowe

    if data_wykonania:
        termin_zatarcia, baza_zatarcia = dodaj_lata(data_wykonania, lata_zat), "od wykonania/darowania kary"
    else:
        termin_zatarcia, baza_zatarcia = dodaj_lata(data_wyroku_k, lata_zat), "od wyroku (orientacyjnie)"
        wyniki.append("⚠️ **OSTRZEŻENIE:** Zatarcie wyliczono orientacyjnie od daty wyroku, ponieważ nie wprowadzono daty wykonania kary.")

    daty_kluczowe["* Orientacyjne zatarcie skazania"] = termin_zatarcia
    if termin_zatarcia < dzis:
        wyniki.append(f"✅ **Zatarcie skazania:** Prawdopodobnie nastąpiło {termin_zatarcia.strftime('%d.%m.%Y')} ({baza_zatarcia}).")
    else:
        wyniki.append(f"⚠️ **Zatarcie skazania:** Skazanie prawdopodobnie nadal widnieje w KRK (orientacyjnie: {termin_zatarcia.strftime('%d.%m.%Y')}).")

    return wyniki, daty_kluczowe

# ─────────────────────────────────────────────
# 4. WALIDACJA DANYCH WEJŚCIOWYCH
# ─────────────────────────────────────────────
def waliduj_dane(
    data_bazowa_cywilna, ostatnia_wplata, data_wyroku_cywilnego,
    data_wszcz_egzekucji, data_umor_egzekucji,
    data_czynu, wszczecie_k, umorzenie_k, wyrok_k, data_wykonania_kary
) -> tuple[list[str], list[str]]:
    """
    Waliduje spójność danych.
    Zwraca: (lista_błędów, lista_ostrzeżeń)
    """
    bledy = []
    ostrzezenia = []

    # --- Sfera cywilna ---
    if data_wszcz_egzekucji and data_umor_egzekucji and data_umor_egzekucji < data_wszcz_egzekucji:
        bledy.append("🔴 Umorzenie egzekucji nie może nastąpić przed jej wszczęciem.")
    
    if data_wszcz_egzekucji is None and data_umor_egzekucji is not None:
        bledy.append("🔴 Umorzenie egzekucji wymaga daty wszczęcia egzekucji.")
    
    if data_bazowa_cywilna and data_wyroku_cywilnego and data_wyroku_cywilnego < data_bazowa_cywilna:
        bledy.append("🔴 Wyrok cywilny nie może być wcześniejszy niż cywilna data bazowa.")
    
    if data_wszcz_egzekucji and data_bazowa_cywilna and data_wszcz_egzekucji < data_bazowa_cywilna:
        bledy.append("🔴 Egzekucja nie może być wszczęta przed datą wymagalności / dowiedzenia się o szkodzie.")
    
    if ostatnia_wplata and data_bazowa_cywilna and ostatnia_wplata < data_bazowa_cywilna:
        bledy.append("🔴 Data wpłaty nie może być wcześniejsza niż data bazowa.")

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
    
    if wyrok_k is None and data_wykonania_kary is None and umorzenie_k is not None:
        # Umorzenie bez wyroku jest OK (np. umorzenie na etapie postępowania)
        pass

    # --- Ostrzeżenia ---
    if data_czynu and data_bazowa_cywilna and data_czynu > data_bazowa_cywilna:
        ostrzezenia.append("⚠️ Data czynu jest późniejsza niż cywilna data bazowa. Sprawdź poprawność.")

    if data_wyroku_cywilnego and data_umor_egzekucji and data_umor_egzekucji < data_wyroku_cywilnego:
        ostrzezenia.append("⚠️ Umorzenie egzekucji jest wcześniejsze niż wyrok cywilny. Sprawdź daty.")

    return bledy, ostrzezenia


# ─────────────────────────────────────────────
# 5. GŁÓWNA PĘTLA WYKONAWCZA I RAPORT
# ─────────────────────────────────────────────
if st.button("Przeprowadź analizę", type="primary"):
    bledy, ostrzezenia = waliduj_dane(
        data_bazowa_cywilna, ostatnia_wplata, data_wyroku_cywilnego,
        data_wszcz_egzekucji, data_umor_egzekucji,
        data_czynu, wszczecie_k, umorzenie_k, wyrok_k, data_wykonania_kary
    )

    # Wyświetl wszystkie błędy naraz
    if bledy:
        for blad in bledy:
            st.error(blad)
        st.stop()

    # Wyświetl ostrzeżenia
    for ost in ostrzezenia:
        st.warning(ost)

    # --- Analiza cywilna (tylko jeśli są dane cywilne) ---
    wyniki_cywilne, daty_kluczowe_cywilne = [], {}
    if data_bazowa_cywilna is not None:
        wyniki_cywilne, daty_kluczowe_cywilne = analiza_cywilna(
            data_bazowa_cywilna, ostatnia_wplata, data_wyroku_cywilnego,
            data_wszcz_egzekucji, data_umor_egzekucji,
            lata_cywilne_baza, podstawa_cywilna, czy_delikt
        )
    else:
        wyniki_cywilne = ["ℹ️ **Analiza cywilna pominięta:** Brak daty bazowej (wymagalności / dowiedzenia się o szkodzie)."]

    # --- Analiza karna (tylko jeśli są dane karne) ---
    wyniki_karne, daty_kluczowe_karne = [], {}
    if data_czynu is not None:
        wyniki_karne, daty_kluczowe_karne = analiza_karna(
            data_czynu, OPCJE_KK[wybor_kk], wszczecie_k, umorzenie_k
        )
    else:
        wyniki_karne.append("ℹ️ **Analiza karna pominięta:** Brak daty popełnienia czynu.")

    # --- Analiza zatarcia (tylko jeśli jest wyrok) ---
    wyniki_zatarcia, daty_kluczowe_zatarcia = [], {}
    if wyrok_k is not None:
        wyniki_zatarcia, daty_kluczowe_zatarcia = analiza_zatarcia(
            wyrok_k, data_wykonania_kary, OPCJE_ZATARCIA[wybor_zatarcia]
        )
    else:
        wyniki_zatarcia.append("ℹ️ **Analiza zatarcia pominięta:** Brak daty wyroku skazującego.")

    wszystkie_daty_kluczowe = {**daty_kluczowe_cywilne, **daty_kluczowe_karne, **daty_kluczowe_zatarcia}

    st.markdown("---")
    col_res1, col_res2 = st.columns([1.2, 1])

    with col_res1:
        st.subheader("📋 Wyniki analizy cywilnej")
        for w in wyniki_cywilne: st.markdown(w)

        st.subheader("⚖️ Informacje karne i KRK (orientacyjne)")
        wszystkie_wyniki_karne = wyniki_karne + wyniki_zatarcia
        if not wszystkie_wyniki_karne:
            st.write("Brak wprowadzonych danych karnych.")
        for w in wszystkie_wyniki_karne: st.markdown(w)

    with col_res2:
        st.subheader("📅 Karta dat brzegowych")
        st.caption("✅ Daty cywilne twarde | ℹ️ Daty orientacyjne karne")
        if not wszystkie_daty_kluczowe:
            st.write("Brak wystarczających danych do wyliczenia dat.")
        
        for k, v in wszystkie_daty_kluczowe.items():
            if k.startswith("*"):
                st.info(f"ℹ️ **{k.replace('* ', '')}:** {v.strftime('%d.%m.%Y')}")
            else:
                st.success(f"✅ **{k}:** {v.strftime('%d.%m.%Y')}")