import streamlit as st
from datetime import date
from obliczenia import (
    LATA_UMOWNE,
    PODSTAWA_DELIKTOWA,
    PODSTAWA_PRACOWNICZA,
    PODSTAWA_PRZESTEPSTWO,
    PODSTAWA_UMOWNA,
    TypOdpowiedzialnosci,
    WynikAnalizyCywilnej,
    WynikAnalizyKarne,
    WynikAnalizyZatarcia,
    analiza_cywilna,
    analiza_deliktowa,
    analiza_karna,
    analiza_zatarcia,
)
from walidacja import waliduj_dane

# Ustawienia strony
st.set_page_config(page_title="Analiza prawna i windykacyjna", layout="wide")

# ─────────────────────────────────────────────
# BEZPIECZEŃSTWO: CORS, XSRF, HEADERS
# ─────────────────────────────────────────────
def configure_security_headers():
    """Dokleja meta tagi bezpieczeństwa (best-effort).

    Streamlit nie pozwala na ustawianie nagłówków HTTP z poziomu aplikacji —
    meta tagi nie zastępują X-Frame-Options/CSP z reverse proxy.
    W szczególności X-Frame-Options w <meta> jest ignorowane przez przeglądarki.
    """
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
czy_pracownik = "pracownik" in kategoria_podmiotu
czy_przestepstwo = False
czy_umyslne = False

if not czy_delikt:
    typ_odpowiedzialnosci = TypOdpowiedzialnosci.UMOWNA
    rodzaj_zdarzenia = None
    st.info(
        f"📌 **Podstawa cywilna:** {PODSTAWA_UMOWNA} – roszczenie związane z prowadzeniem "
        f"działalności gospodarczej. Co do zasady: **{LATA_UMOWNE} lata**."
    )
else:
    typ_odpowiedzialnosci = (
        TypOdpowiedzialnosci.PRACOWNICZA if czy_pracownik else TypOdpowiedzialnosci.DELIKTOWA
    )
    rodzaj_zdarzenia = st.selectbox(
        "Rodzaj zdarzenia deficytowego",
        ["Przywłaszczenie zaliczek / zbiórek", "Nieuprawnione wypłaty BLIK / z karty", "Kradzież gotówki / karty", "Fałszowanie dowodów bankowania", "Umowy fikcyjne / na słupa"],
        help="Kategoria opisowa do raportu — bez wpływu na termin przedawnienia."
    )
    czy_przestepstwo = st.checkbox("Czy szkoda bezpośrednio wynika ze zbrodni lub występku (przestępstwa)?")
    czy_umyslne = st.checkbox("Czy szkoda została wyrządzona umyślnie?", help="Dotyczy odpowiedzialności pracowniczej – przy szkodzie umyślnej stosuje się przepisy k.c. (art. 291 § 3 k.p.), nie zaś 1-roczny termin z art. 291 § 2 k.p.")

    if czy_pracownik:
        st.info(
            f"📌 **Reżim pracowniczy:** {PODSTAWA_PRACOWNICZA}. Odpowiedzialność materialna "
            "pracownika (nieumyślna) – **1 rok** od powzięcia wiadomości o szkodzie, "
            "nie później niż **3 lata** od jej wyrządzenia."
        )

    if czy_przestepstwo:
        st.error(f"📌 **Podstawa cywilna:** {PODSTAWA_PRZESTEPSTWO}. Przedawnienie: **20 lat** od popełnienia przestępstwa.")
    elif not czy_pracownik:
        st.warning(
            f"📌 **Podstawa cywilna:** {PODSTAWA_DELIKTOWA}. Czyn niedozwolony bez kwalifikacji "
            "karnej – przedawnienie: **3 lata** od dnia dowiedzenia się o szkodzie ORAZ o osobie "
            "obowiązanej do jej naprawienia, nie dłużej niż 10 lat od zdarzenia."
        )

# ─────────────────────────────────────────────
# 2. WPROWADZANIE DAT
# ─────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Oś czasu cywilna")
    
    data_zdarzenia = None
    if not czy_delikt:
        # Umowy: osobne daty zawarcia i wymagalności
        data_zawarcia_umowy = st.date_input("Data zawarcia umowy", value=None, min_value=MIN_DATE, help="Data podpisania umowy (dla przepisów przejściowych 2018 r.).")
        data_wymagalnosci = st.date_input("Data wymagalności roszczenia (pierwsza zaległa rata / termin płatności)", value=None, min_value=MIN_DATE, help="Data, od której roszczenie stało się wymagalne – początek biegu przedawnienia.")
        data_dowiedzenia = None
    else:
        # Delikty: osobna data zdarzenia i data dowiedzenia się o szkodzie i sprawcy
        data_zawarcia_umowy = None
        data_wymagalnosci = None
        data_zdarzenia = st.date_input("Data zdarzenia wywołującego szkodę", value=None, min_value=MIN_DATE, help="Data samego czynu/zdarzenia, w wyniku którego powstała szkoda (moment wyrządzenia szkody).")
        data_dowiedzenia = st.date_input("Data dowiedzenia się o szkodzie i sprawcy", value=None, min_value=MIN_DATE, help="Data, w której poszkodowany/pracodawca uzyskał wiedzę o szkodzie ORAZ o osobie zobowiązanej do jej naprawienia (art. 442¹ § 1 k.c. / art. 291 § 1 k.p.).")
    
    # Wpłaty - lista dat
    st.markdown("**Wpłaty / uznania długu** (można dodać wiele):")
    wpłaty_input = st.text_area(
        "Daty wpłat (po jednej w linii, format RRRR-MM-DD):",
        value="",
        height=100,
        help="Każda wpłata może stanowić uznanie długu (art. 123 k.c.) i uruchamiać bieg przedawnienia od nowa."
    )
    # Parsowanie wpłat
    wpłaty = []
    bledne_wplaty = []
    if wpłaty_input.strip():
        for linia in wpłaty_input.strip().split('\n'):
            linia = linia.strip()
            if linia:
                try:
                    wpłaty.append(date.fromisoformat(linia))
                except ValueError:
                    bledne_wplaty.append(linia)
    if bledne_wplaty:
        st.warning(
            "Nie rozpoznano formatu daty (oczekiwano RRRR-MM-DD): "
            + ", ".join(bledne_wplaty)
        )
    
    data_wyroku_cywilnego = st.date_input("Data prawomocnego wyroku cywilnego / nakazu", value=None, min_value=MIN_DATE, help="Prawomocne orzeczenie sądu wyznacza odrębny reżim przedawnienia (6 lat od wyroku – art. 125 k.c.).")

    st.markdown("---")
    data_wszcz_egzekucji = st.date_input("Data wszczęcia egzekucji", value=None, min_value=MIN_DATE, help="Data złożenia wniosku egzekucyjnego u komornika (zawiesza bieg przedawnienia – art. 124 k.c.).")
    data_umor_egzekucji = st.date_input("Data prawomocnego umorzenia egzekucji", value=None, min_value=MIN_DATE, help="Data uprawomocnienia się postanowienia komornika o umorzeniu (bieg od nowa – art. 124 § 2 k.c.).")

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
    czy_oskarzenie_prywatne = st.checkbox("Przestępstwo ścigane z oskarżenia prywatnego?", help="Art. 101 § 2 k.k. – odrębny termin: 1 rok od dowiedzenia się o osobie sprawcy, nie później niż 3 lata od czynu.")
    if czy_oskarzenie_prywatne:
        data_dowiedzenia_o_sprawcy = st.date_input("Data dowiedzenia się o osobie sprawcy", value=None, min_value=MIN_DATE, help="Wymagana dla oskarżenia prywatnego (art. 101 § 2 k.k.). Bez niej wynik karny będzie niepewny.")
    else:
        data_dowiedzenia_o_sprawcy = None

    wszczecie_k = st.date_input("Data wszczęcia postępowania karnego (przeciwko osobie)", value=None, min_value=MIN_DATE, help="Wszczęcie postępowania PRZECIWKO OSOBIE przed upływem terminu przedłuża karalność o 10 lat (art. 102 k.k.).")
    umorzenie_k = st.date_input("Data umorzenia postępowania karnego", value=None, min_value=MIN_DATE)

    st.markdown("---")
    wyrok_k = st.date_input("Data wyroku karnego skazującego", value=None, min_value=MIN_DATE)
    data_wykonania_kary = st.date_input("Data wykonania / zakończenia / darowania kary (do zatarcia)", value=None, min_value=MIN_DATE, help="Od tej daty liczy się termin zatarcia. Jeśli brak – aplikacja oznaczy wynik jako niepewny (nie zastąpi datą wyroku).")

    # Rodzaj kary: termin z mocy prawa zależy od kary (art. 107 § 1, § 3, § 4, § 4a);
    # dla kary pozbawienia wolności do 3 lat sąd może zarządzić zatarcie na wniosek po 5 latach (§ 2).
    OPCJE_ZATARCIA = {
        "Grzywna": {"auto": 1, "auto_podstawa": "Art. 107 § 4a k.k.", "wyjatek": None, "wyjatek_podstawa": None},
        "Kara ograniczenia wolności": {"auto": 3, "auto_podstawa": "Art. 107 § 4 k.k.", "wyjatek": None, "wyjatek_podstawa": None},
        "Pozbawienie wolności do 3 lat": {"auto": 10, "auto_podstawa": "Art. 107 § 1 k.k.", "wyjatek": 5, "wyjatek_podstawa": "Art. 107 § 2 k.k."},
        "Pozbawienie wolności powyżej 3 lat": {"auto": 10, "auto_podstawa": "Art. 107 § 1 k.k.", "wyjatek": None, "wyjatek_podstawa": None},
        "Dożywotnie pozbawienie wolności": {"auto": 10, "auto_podstawa": "Art. 107 § 3 k.k.", "wyjatek": None, "wyjatek_podstawa": None},
    }
    wybor_zatarcia = st.selectbox("Orzeczona kara (dla zatarcia z art. 107 k.k.)", list(OPCJE_ZATARCIA.keys()), disabled=(wyrok_k is None), help="Rodzaj kary decyduje o terminie zatarcia z mocy prawa (art. 107 k.k.).")

st.divider()

# ─────────────────────────────────────────────
# 4. GŁÓWNA PĘTLA WYKONAWCZA I RAPORT
# ─────────────────────────────────────────────
if st.button("Przeprowadź analizę", type="primary"):
    bledy, ostrzezenia = waliduj_dane(
        data_zawarcia_umowy, data_wymagalnosci, data_zdarzenia, data_dowiedzenia, wpłaty,
        data_wyroku_cywilnego, data_wszcz_egzekucji, data_umor_egzekucji,
        data_czynu, wszczecie_k, umorzenie_k, wyrok_k, data_wykonania_kary,
        czy_delikt, data_dowiedzenia_o_sprawcy
    )

    # Wyświetl wszystkie błędy naraz
    if bledy:
        for blad in bledy:
            st.error(blad)
        st.stop()

    # Wyświetl ostrzeżenia
    for ost in ostrzezenia:
        st.warning(ost)

    data_oceny = date.today()

    # --- Analiza cywilna (umowy) lub deliktowa (szkody) ---
    wynik_cywilny: WynikAnalizyCywilnej
    if not czy_delikt:
        if data_wymagalnosci is not None:
            wynik_cywilny = analiza_cywilna(
                data_zawarcia_umowy, data_wymagalnosci, wpłaty,
                data_wyroku_cywilnego, data_wszcz_egzekucji, data_umor_egzekucji,
                LATA_UMOWNE, PODSTAWA_UMOWNA,
                data_oceny
            )
        else:
            wynik_cywilny = WynikAnalizyCywilnej(
                bledy=[],
                ostrzezenia=["Analiza cywilna pominięta: brak daty wymagalności."]
            )
    else:
        if data_zdarzenia is not None:
            wynik_cywilny = analiza_deliktowa(
                data_zdarzenia, data_dowiedzenia, czy_przestepstwo, czy_umyslne,
                typ_odpowiedzialnosci, wpłaty,
                data_wyroku_cywilnego, data_wszcz_egzekucji, data_umor_egzekucji,
                data_oceny
            )
        else:
            wynik_cywilny = WynikAnalizyCywilnej(
                bledy=[],
                ostrzezenia=["Analiza szkody pominięta: brak daty zdarzenia wywołującego szkodę."]
            )

    # --- Analiza karna ---
    wynik_karny: WynikAnalizyKarne
    if data_czynu is not None:
        wynik_karny = analiza_karna(
            data_czynu, OPCJE_KK[wybor_kk], wszczecie_k, umorzenie_k,
            data_oceny, czy_oskarzenie_prywatne, data_dowiedzenia_o_sprawcy
        )
    else:
        wynik_karny = WynikAnalizyKarne(
            bledy=[],
            ostrzezenia=["Analiza karna pominięta: brak daty popełnienia czynu."]
        )

    # --- Analiza zatarcia ---
    wynik_zatarcia: WynikAnalizyZatarcia
    if wyrok_k is not None:
        opcja_zat = OPCJE_ZATARCIA[wybor_zatarcia]
        wynik_zatarcia = analiza_zatarcia(
            wyrok_k, data_wykonania_kary,
            opcja_zat["auto"], data_oceny,
            opcja_zat["wyjatek"], wybor_zatarcia,
            opcja_zat["auto_podstawa"], opcja_zat["wyjatek_podstawa"]
        )
    else:
        wynik_zatarcia = WynikAnalizyZatarcia(
            bledy=[],
            ostrzezenia=["Analiza zatarcia pominięta: brak daty wyroku skazującego."]
        )

    # Zbierz wszystkie daty do karty (tylko realne terminy —
    # W_TOKU i BRAK_DANYCH mają termin=data_oceny i nie są deadline'ami)
    wszystkie_wyniki = [
        w for w in (wynik_cywilny.wyniki + wynik_karny.wyniki + wynik_zatarcia.wyniki)
        if w.status not in ("W_TOKU", "BRAK_DANYCH")
    ]
    wszystkie_wyniki.sort()  # sortowanie po terminie

    # Raport błędów i ostrzeżeń z modułów
    for w in wynik_cywilny.bledy: st.error(w)
    for w in wynik_karny.bledy: st.error(w)
    for w in wynik_zatarcia.bledy: st.error(w)

    st.markdown("---")
    col_res1, col_res2 = st.columns([1.2, 1])

    with col_res1:
        st.subheader("📋 Wyniki analizy cywilnej")
        if czy_delikt and rodzaj_zdarzenia:
            st.caption(f"Rodzaj zdarzenia (opisowo, bez wpływu na termin): {rodzaj_zdarzenia}")
        if wynik_cywilny.wyniki:
            for w in wynik_cywilny.wyniki:
                # Główna informacja
                if w.status == "OK":
                    st.success(f"✅ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}")
                elif w.status == "PRZEDAWNIONE":
                    st.error(f"❌ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}")
                elif w.status == "W_TOKU":
                    st.info(f"⏸️ **{w.nazwa}**: Egzekucja w toku")
                
                # Podstawa prawna
                st.caption(f"📜 {w.podstawa_prawna}")
                
                # Założenia
                if w.zalozenia:
                    with st.expander("🔍 Założenia i przebieg obliczeń"):
                        for z in w.zalozenia:
                            st.write(f"• {z}")
                
                # Ostrzeżenia
                for o in w.ostrzezenia:
                    if o.startswith("OSTRZEŻENIE") or o.startswith("Wpłata po") or o.startswith("Zarejestrowano"):
                        st.warning(o)
                    else:
                        st.info(o)
        else:
            for o in wynik_cywilny.ostrzezenia:
                st.info(o)

        if wynik_cywilny.os_czasu:
            with st.expander("🕒 Oś czasu zdarzeń"):
                for z in wynik_cywilny.os_czasu:
                    st.write(f"• {z.data.strftime('%d.%m.%Y')} — {z.opis}")

        st.subheader("⚖️ Informacje karne i KRK (orientacyjne)")
        wyniki_karne_krk = wynik_karny.wyniki + wynik_zatarcia.wyniki
        if wyniki_karne_krk:
            for w in wyniki_karne_krk:
                if w.status == "TRWA":
                    st.warning(f"⚠️ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}")
                elif w.status == "WYGASŁE":
                    st.error(f"❌ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}")
                elif w.status == "ZATARTE":
                    st.success(f"✅ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}")
                elif w.status == "W_KRK":
                    st.warning(f"⚠️ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}")
                elif w.status == "BRAK_DANYCH":
                    st.error(f"❓ **{w.nazwa}**: dane niewystarczające")
                elif w.status == "MOZLIWE_WCZEŚNIEJ":
                    st.info(f"🕓 **{w.nazwa}**: od {w.termin.strftime('%d.%m.%Y')}")
                else:
                    st.info(f"ℹ️ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}")

                st.caption(f"📜 {w.podstawa_prawna}")

                if w.zalozenia:
                    with st.expander("🔍 Założenia i przebieg obliczeń"):
                        for z in w.zalozenia:
                            st.write(f"• {z}")

                for o in w.ostrzezenia:
                    if o.startswith("OSTRZEŻENIE") or o.startswith("Art. 102"):
                        st.warning(o)
                    else:
                        st.info(o)
        else:
            for o in wynik_karny.ostrzezenia + wynik_zatarcia.ostrzezenia:
                st.info(o)

        # Przypadki nieobsługiwane
        nieobslugiwane = wynik_karny.nieobslugiwane + wynik_zatarcia.nieobslugiwane
        if nieobslugiwane:
            st.subheader("🚧 Przypadki nieobsługiwane")
            for n in nieobslugiwane:
                st.warning(n)

    with col_res2:
        st.subheader("📅 Karta dat brzegowych")
        st.caption("✅ Daty cywilne twarde | ℹ️ Daty orientacyjne karne")
        if not wszystkie_wyniki:
            st.write("Brak wystarczających danych do wyliczenia dat.")
        
        for w in wszystkie_wyniki:
            if w.orientacyjny:
                st.info(f"ℹ️ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')} [{w.status}]")
            else:
                if w.status == "OK":
                    st.success(f"✅ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}")
                elif w.status == "PRZEDAWNIONE":
                    st.error(f"❌ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}")
                else:
                    st.info(f"ℹ️ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')} [{w.status}]")