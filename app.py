import streamlit as st
from datetime import date
from obliczenia import (
    LATA_UMOWNE,
    PODSTAWA_UMOWNA,
    TypOdpowiedzialnosci,
    WynikAnalizyCywilnej,
    WynikAnalizyKarne,
    WynikAnalizyZatarcia,
    analiza_cywilna,
    analiza_deliktowa,
    analiza_karna,
    analiza_wykonania_kary,
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
st.title("⚖️ Czy sprawa jest przedawniona?")

st.warning(
    "⚠️ **Zastrzeżenie:** narzędzie pomocnicze i informacyjne — wynik nie stanowi wiążącej "
    "porady prawnej. Podstawy: art. 118, 123, 124, 125, 442¹ k.c.; art. 291 k.p.; "
    "art. 101, 102, 107 k.k."
)

MIN_DATE = date(2000, 1, 1)

OPCJE_KK = {
    "Oszustwo ogólne z art. 286 (występek > 5 lat, przedawnienie: 15 lat)": 15,
    "Oszustwo kredytowe, fałszerstwo, przywłaszczenie powierzone (występek 3-5 lat, przedawnienie: 10 lat)": 10,
    "Zwykłe przywłaszczenie (występek do 3 lat, przedawnienie: 5 lat)": 5,
    "Zbrodnia np. podrabianie środków płatniczych (przedawnienie: 20 lat)": 20,
}

OPCJE_ZATARCIA = {
    "Grzywna": {"auto": 1, "auto_podstawa": "Art. 107 § 4a k.k.", "wyjatek": None, "wyjatek_podstawa": None},
    "Kara ograniczenia wolności": {"auto": 3, "auto_podstawa": "Art. 107 § 4 k.k.", "wyjatek": None, "wyjatek_podstawa": None},
    "Pozbawienie wolności do 3 lat": {"auto": 10, "auto_podstawa": "Art. 107 § 1 k.k.", "wyjatek": 5, "wyjatek_podstawa": "Art. 107 § 2 k.k."},
    "Pozbawienie wolności powyżej 3 lat": {"auto": 10, "auto_podstawa": "Art. 107 § 1 k.k.", "wyjatek": None, "wyjatek_podstawa": None},
    "Dożywotnie pozbawienie wolności": {"auto": 10, "auto_podstawa": "Art. 107 § 3 k.k.", "wyjatek": None, "wyjatek_podstawa": None},
}


OPCJE_WYKONANIA = {
    "Pozbawienie wolności powyżej 5 lat albo kara surowsza (25 lat, dożywocie)": 30,
    "Pozbawienie wolności do 5 lat": 15,
    "Inna kara (grzywna, ograniczenie wolności)": 10,
}


# ─────────────────────────────────────────────
# KROK 1 — TYP SPRAWY
# ─────────────────────────────────────────────
st.subheader("1. Co to za sprawa?")
typ_sprawy = st.radio(
    "Typ sprawy",
    [
        "Klient – umowa pożyczki",
        "Klient – karta kredytowa",
        "Deficyt – pracownik",
        "Deficyt – osoba trzecia",
    ],
    label_visibility="collapsed",
)

jest_klient = typ_sprawy.startswith("Klient")
jest_pracownik = "pracownik" in typ_sprawy

# ─────────────────────────────────────────────
# KROK 2 — CO SIĘ JUŻ STAŁO
# ─────────────────────────────────────────────
st.subheader("2. Co już się stało? (można zaznaczyć kilka)")
ck1, ck2 = st.columns(2)
with ck1:
    etap_brak = st.checkbox("Roszczenie / zdarzenie bez postępowania", value=True)
    etap_cywilny = st.checkbox("Jest wyrok / nakaz cywilny (tytuł wykonawczy)")
    etap_egzekucja = st.checkbox("Egzekucja komornicza")
with ck2:
    etap_karny = st.checkbox("Postępowanie karne (zawiadomienie / skazanie)")
    etap_zatarcie = st.checkbox("Zatarcie skazania (KRK)")

st.divider()

# ─────────────────────────────────────────────
# POLA ZALEŻNE OD WYBORÓW
# ─────────────────────────────────────────────
data_zawarcia_umowy = None
data_wymagalnosci = None
data_zdarzenia = None
data_dowiedzenia = None
czy_przestepstwo = False
czy_umyslne = False
wpłaty: list[date] = []
data_wyroku_cywilnego = None
data_wszcz_egzekucji = None
data_umor_egzekucji = None
data_czynu = None
wybor_kk = None
wszczecie_k = None
umorzenie_k = None
wyrok_k = None
data_wykonania_kary = None
wybor_zatarcia = None
wybor_wykonania = None

if jest_klient:
    st.subheader("Roszczenie z umowy")
    data_zawarcia_umowy = st.date_input("Data zawarcia umowy", value=None, min_value=MIN_DATE)
    data_wymagalnosci = st.date_input("Data wymagalności (pierwsza zaległa rata)", value=None, min_value=MIN_DATE)
else:
    st.subheader("Szkoda (deficyt)")
    data_zdarzenia = st.date_input("Data zdarzenia (wyrządzenia szkody)", value=None, min_value=MIN_DATE)
    data_dowiedzenia = st.date_input("Data dowiedzenia się o szkodzie i osobie", value=None, min_value=MIN_DATE)
    czy_przestepstwo = st.checkbox("Czy szkoda wynika z przestępstwa (zbrodni lub występku)?")
    if jest_pracownik:
        czy_umyslne = st.checkbox("Czy szkoda wyrządzona umyślnie?")

wpłaty_input = st.text_area(
    "Wpłaty / uznania długu (daty RRRR-MM-DD, po jednej w linii)",
    value="", height=80,
    help="Każda wpłata może stanowić uznanie długu (art. 123 § 1 pkt 2 k.c.).",
)
bledne_wplaty = []
for linia in wpłaty_input.strip().split("\n"):
    linia = linia.strip()
    if linia:
        try:
            wpłaty.append(date.fromisoformat(linia))
        except ValueError:
            bledne_wplaty.append(linia)
if bledne_wplaty:
    st.warning("Nie rozpoznano daty (oczekiwano RRRR-MM-DD): " + ", ".join(bledne_wplaty))

if etap_cywilny:
    data_wyroku_cywilnego = st.date_input(
        "Data prawomocnego wyroku / nakazu cywilnego", value=None, min_value=MIN_DATE,
        help="Roszczenie stwierdzone orzeczeniem przedawnia się z upływem 6 lat (10 lat, gdy orzeczenie przed 09.07.2018) – art. 125 § 1 k.c.",
    )

if etap_egzekucja:
    data_wszcz_egzekucji = st.date_input("Data wszczęcia egzekucji", value=None, min_value=MIN_DATE)
    data_umor_egzekucji = st.date_input("Data umorzenia egzekucji (jeśli było)", value=None, min_value=MIN_DATE)

if etap_karny:
    st.subheader("Postępowanie karne")
    data_czynu = st.date_input("Data popełnienia czynu", value=None, min_value=MIN_DATE)
    wybor_kk = st.selectbox("Kwalifikacja czynu", list(OPCJE_KK.keys()))
    wszczecie_k = st.date_input("Data wszczęcia postępowania karnego", value=None, min_value=MIN_DATE)
    umorzenie_k = st.date_input("Data umorzenia postępowania karnego", value=None, min_value=MIN_DATE)

if etap_zatarcie or etap_karny:
    wyrok_k = st.date_input("Data wyroku karnego skazującego", value=None, min_value=MIN_DATE)

if wyrok_k is not None:
    wybor_wykonania = st.selectbox(
        "Rodzaj kary (dla przedawnienia wykonania kary, art. 103 k.k.)",
        list(OPCJE_WYKONANIA.keys()),
    )

if etap_zatarcie:
    data_wykonania_kary = st.date_input("Data wykonania / darowania kary", value=None, min_value=MIN_DATE)
    wybor_zatarcia = st.selectbox(
        "Orzeczona kara (dla zatarcia, art. 107 k.k.)",
        list(OPCJE_ZATARCIA.keys()),
        disabled=(wyrok_k is None),
    )

st.divider()


# ─────────────────────────────────────────────
# WYNIK — KARTA DECYZYJNA
# ─────────────────────────────────────────────
def _karta_cywilna(wynik: WynikAnalizyCywilnej) -> None:
    for w in wynik.wyniki:
        if w.status == "W_TOKU":
            st.info(f"⏸️ **{w.nazwa}**: egzekucja w toku — przedawnienie nie biegnie do jej zakończenia.")
        elif w.status == "OK":
            st.success(f"✅ **{w.nazwa}**: nieprzedawnione do **{w.termin.strftime('%d.%m.%Y')}** — wierzyciel może działać.")
        elif w.status == "PRZEDAWNIONE":
            st.error(f"❌ **{w.nazwa}**: przedawnione **{w.termin.strftime('%d.%m.%Y')}** — nic nie zrobisz.")
        st.caption(f"📜 {w.podstawa_prawna}")
        if w.zalozenia:
            with st.expander("🔍 Założenia i przebieg obliczeń"):
                for z in w.zalozenia:
                    st.write(f"• {z}")
        for o in w.ostrzezenia:
            st.caption(f"ℹ️ {o}")


def _karta_karna(wynik: WynikAnalizyKarne) -> None:
    for w in wynik.wyniki:
        if w.status == "BRAK_DANYCH":
            st.warning(f"❓ **{w.nazwa}**: dane niewystarczające.")
        elif w.status == "TRWA":
            st.success(f"✅ **{w.nazwa}**: karalność do **{w.termin.strftime('%d.%m.%Y')}** — można zawiadomić prokuraturę.")
        else:
            st.error(f"❌ **{w.nazwa}**: karalność wygasła **{w.termin.strftime('%d.%m.%Y')}**.")
        st.caption(f"📜 {w.podstawa_prawna}")
        if w.zalozenia:
            with st.expander("🔍 Założenia i przebieg obliczeń"):
                for z in w.zalozenia:
                    st.write(f"• {z}")
        for o in w.ostrzezenia:
            st.caption(f"ℹ️ {o}")


def _karta_wykonania(wynik: WynikAnalizyKarne) -> None:
    for w in wynik.wyniki:
        if w.status == "TRWA":
            st.success(f"✅ **{w.nazwa}**: karę można jeszcze wykonać do **{w.termin.strftime('%d.%m.%Y')}**.")
        elif w.status == "WYGASŁE":
            st.error(f"❌ **{w.nazwa}**: kara przedawniona {w.termin.strftime('%d.%m.%Y')} — nie można już wykonać.")
        st.caption(f"📜 {w.podstawa_prawna}")
        for o in w.ostrzezenia:
            st.caption(f"ℹ️ {o}")


def _karta_zatarcia(wynik: WynikAnalizyZatarcia) -> None:
    for w in wynik.wyniki:
        if w.status == "BRAK_DANYCH":
            st.warning(f"❓ **{w.nazwa}**: dane niewystarczające.")
        elif w.status in ("W_KRK", "MOZLIWE_WCZEŚNIEJ"):
            st.info(f"🗂️ **{w.nazwa}**: {w.termin.strftime('%d.%m.%Y')}.")
        elif w.status == "ZATARTE":
            st.success(f"✅ **{w.nazwa}**: zatarte.")
        st.caption(f"📜 {w.podstawa_prawna}")
        for o in w.ostrzezenia:
            st.caption(f"ℹ️ {o}")


if st.button("Sprawdź sprawę", type="primary"):
    czy_delikt = not jest_klient
    bledy, ostrzezenia = waliduj_dane(
        data_zawarcia_umowy, data_wymagalnosci, data_zdarzenia, data_dowiedzenia, wpłaty,
        data_wyroku_cywilnego, data_wszcz_egzekucji, data_umor_egzekucji,
        data_czynu, wszczecie_k, umorzenie_k, wyrok_k, data_wykonania_kary,
        czy_delikt,
    )
    if bledy:
        for blad in bledy:
            st.error(blad)
        st.stop()
    for ost in ostrzezenia:
        st.warning(ost)

    data_oceny = date.today()
    st.subheader("Wynik")

    # --- Cywilnie: roszczenie / tytuł wykonawczy ---
    wynik_cywilny: WynikAnalizyCywilnej | None = None
    if jest_klient:
        if data_wymagalnosci is not None:
            wynik_cywilny = analiza_cywilna(
                data_zawarcia_umowy, data_wymagalnosci, wpłaty,
                data_wyroku_cywilnego, data_wszcz_egzekucji, data_umor_egzekucji,
                LATA_UMOWNE, PODSTAWA_UMOWNA, data_oceny,
            )
    else:
        if data_zdarzenia is not None:
            wynik_cywilny = analiza_deliktowa(
                data_zdarzenia, data_dowiedzenia, czy_przestepstwo, czy_umyslne,
                TypOdpowiedzialnosci.PRACOWNICZA if jest_pracownik else TypOdpowiedzialnosci.DELIKTOWA,
                wpłaty, data_wyroku_cywilnego, data_wszcz_egzekucji, data_umor_egzekucji,
                data_oceny,
            )
    if wynik_cywilny and wynik_cywilny.wyniki:
        st.markdown("#### Roszczenie / tytuł wykonawczy")
        _karta_cywilna(wynik_cywilny)
    elif wynik_cywilny:
        for o in wynik_cywilny.ostrzezenia:
            st.info(o)

    # --- Karne: karalność ---
    if etap_karny and data_czynu is not None and wybor_kk is not None:
        wynik_karny = analiza_karna(
            data_czynu, OPCJE_KK[wybor_kk], wszczecie_k, umorzenie_k, data_oceny,
        )
        st.markdown("#### Karalność (możliwość ścigania)")
        _karta_karna(wynik_karny)

    # --- Wykonanie kary (tytuł wykonawczy karny) ---
    if wyrok_k is not None and wybor_wykonania is not None:
        wynik_wykonania = analiza_wykonania_kary(
            wyrok_k, OPCJE_WYKONANIA[wybor_wykonania], data_oceny, wybor_wykonania,
        )
        st.markdown("#### Wykonanie kary (tytuł wykonawczy karny)")
        _karta_wykonania(wynik_wykonania)

    # --- Zatarcie ---
    if etap_zatarcie and wyrok_k is not None and wybor_zatarcia is not None:
        opcja_zat = OPCJE_ZATARCIA[wybor_zatarcia]
        wynik_zatarcia = analiza_zatarcia(
            wyrok_k, data_wykonania_kary,
            opcja_zat["auto"], data_oceny,
            opcja_zat["wyjatek"], wybor_zatarcia,
            opcja_zat["auto_podstawa"], opcja_zat["wyjatek_podstawa"],
        )
        st.markdown("#### Zatarcie skazania")
        _karta_zatarcia(wynik_zatarcia)
