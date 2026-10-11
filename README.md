# Kalkulator-Prawny

Narzędzie do orientacyjnej analizy przedawnienia roszczeń cywilnych, przedawnienia
karalności oraz zatarcia skazania. Aplikacja webowa oparta na Streamlit, z logiką
obliczeniową oddzieloną od interfejsu i pokrytą testami jednostkowymi.

> ⚠️ **Zastrzeżenie prawne:** Narzędzie ma charakter wyłącznie pomocniczy i
> informacyjny. Wyniki **nie stanowią wiążącej porady prawnej** i nie mogą być
> podstawą samodzielnych decyzji. Zakres zastosowania i ograniczenia opisano poniżej.
> Reguły prawne wymagają weryfikacji przez prawnika przed wdrożeniem produkcyjnym.

---

## Spis treści

- [Funkcjonalności](#funkcjonalności)
- [Zakres i podstawy prawne](#zakres-i-podstawy-prawne)
- [Ograniczenia i przypadki nieobsługiwane](#ograniczenia-i-przypadki-nieobsługiwane)
- [Wymagania](#wymagania)
- [Instalacja i uruchomienie](#instalacja-i-uruchomienie)
- [Konfiguracja sekretów](#konfiguracja-sekretów)
- [Testy](#testy)
- [Struktura projektu](#struktura-projektu)
- [Historia zmian](#historia-zmian)

---

## Funkcjonalności

- **Roszczenia umowne** (cywilne) – osobna data zawarcia umowy i wymagalności,
  uznanie długu, wyrok, egzekucja, umorzenie egzekucji.
- **Szkody i odpowiedzialność pracownicza** (deliktowa) – osobna data zdarzenia i
  dowiedzenia się o szkodzie oraz sprawcy, kwalifikacja przestępstwa, umyślność.
- **Przedawnienie karalności** – ustawowy termin (art. 101 § 1 k.k.), oskarżenie
  prywatne (art. 101 § 2 k.k.) oraz przedłużenie o 10 lat.
- **Zatarcie skazania** – automatyczne oraz w drodze wyjątku na wniosek.
- **Walidacja danych** – blokada obliczeń przy sprzecznych danych i jasne
  komunikaty o brakach.
- **Ochrona hasłem** dostępu do aplikacji (sekret Streamlit).

---

## Zakres i podstawy prawne

### Część cywilna – roszczenia umowne
| Zagadnienie | Podstawa | Zastosowana reguła |
|---|---|---|
| Termin ogólny (działalność gospodarcza) | art. 118 k.c. | 3 lata od wymagalności |
| Przepisy przejściowe 2018 | art. 118 k.c. (nowelizacja) | umowy przed 09.07.2018 – bez końca roku; po – z końcem roku |
| Uznanie długu / wpłata | art. 123 k.c. | nowy bieg od daty uznania |
| Wszczęcie egzekucji | art. 124 k.c. | zawieszenie biegu |
| Umorzenie egzekucji | art. 124 § 2 k.c. | bieg od nowa od umorzenia |
| Prawomocny wyrok / nakaz | art. 125 § 1 k.c. | 6 lat od wyroku |

### Część cywilna – szkody / pracownik
| Zagadnienie | Podstawa | Zastosowana reguła |
|---|---|---|
| Szkoda bez kwalifikacji karnej | art. 442¹ § 1 k.c. | 3 lata od dowiedzenia się, max 10 lat od zdarzenia |
| Szkoda z przestępstwa | art. 442¹ § 2 k.c. | 20 lat od popełnienia czynu (bezwzględny limit – reset go nie wydłuża) |
| Odpowiedzialność pracownicza | art. 291 § 1 k.p. | 3 lata od dowiedzenia się o szkodzie i sprawcy |
| Umyślność szkody pracownika | art. 122 k.p. | ostrzeżenie o pełnym zakresie odpowiedzialności |

### Część karna
| Zagadnienie | Podstawa | Zastosowana reguła |
|---|---|---|
| Ustawowe przedawnienie karalności | art. 101 § 1 k.k. | termin zależny od kwalifikacji czynu |
| Karalność – oskarżenie prywatne | art. 101 § 2 k.k. | 1 rok od dowiedzenia się o sprawcy, max 3 lata od czynu |
| Przedłużenie karalności | art. 102 k.k. | +10 lat, jeżeli wszczęto postępowanie przeciwko osobie w terminie |
| Zatarcie z mocy prawa | art. 107 § 1 k.k. | 3 / 5 / 10 lat od wykonania kary |
| Zatarcie w drodze wyjątku | art. 107 § 4 k.k. | min. 5 lat, na wniosek skazanego |

---

## Ograniczenia i przypadki nieobsługiwane

Aplikacja **jawnie zgłasza** przypadki, których nie obsługuje, zamiast podawać
niepewne terminy jako pewne:

- Przepisy szczególne przewidujące odrębne terminy przedawnienia.
- Przedłużenie karalności, gdy nie podano daty wszczęcia postępowania przeciwko osobie.
- Karalność przy oskarżeniu prywatnym bez daty dowiedzenia się o osobie sprawcy
  (status „dane niewystarczające”).
- Zatarcie, gdy nie podano daty wykonania / darowania kary (status „dane niewystarczające”).
- Złożone stany faktyczne (czyny ciągłe, skutkowe, wielodniowe) wymagają oceny indywidualnej.

Reguły dot. odpowiedzialności pracowniczej oraz części karnej mają charakter
orientacyjny i **wymagają przeglądu prawnego**.

> Uwaga bezpieczeństwa: meta tagi w `app.py` to wyłącznie best-effort —
> Streamlit nie ustawia nagłówków HTTP z poziomu aplikacji. Prawdziwe
> `CSP / X-Frame-Options` muszą pochodzić z reverse proxy; devcontainer
> używa domyślnych (włączonych) `CORS/XSRF`.

---

## Wymagania

- Python 3.11 lub 3.12
- Zależności runtime: `streamlit`, `python-dateutil` (wersje w `requirements.txt`)
- Zależności deweloperskie: `pytest`, `ruff` (`requirements-dev.txt`)

---

## Instalacja i uruchomienie

```bash
# 1. Klonowanie
git clone https://github.com/byku-17/Kalkulator-Prawny.git
cd Kalkulator-Prawny

# 2. Środowisko wirtualne (zalecane)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Zależności
pip install -r requirements.txt

# 4. Hasło dostępu (patrz niżej)
mkdir -p .streamlit
echo 'HASLO_DO_APLIKACJI = "twoje_haslo"' > .streamlit/secrets.toml

# 5. Uruchomienie
streamlit run app.py
```

Aplikacja dostępna pod `http://localhost:8501`.

---

## Konfiguracja sekretów

Plik `.streamlit/secrets.toml` (**nie commitować – wpisany w `.gitignore`**):

```toml
HASLO_DO_APLIKACJI = "silne_haslo_dostepu"
```

Dla wdrożenia na Streamlit Cloud sekret ustawia się w panelu aplikacji
(**Settings → Secrets**).

---

## Testy

```bash
pip install -r requirements-dev.txt
pytest
```

Testy są uruchamiane automatycznie w GitHub Actions (`.github/workflows/tests.yml`)
dla Pythona 3.11 i 3.12 przy każdym pushu i pull requeście.

Zakres testów:

| Plik | Zakres | Liczba |
|---|---|---|
| `tests/test_obliczenia.py` | logika umowna, karna, zatarcie | 35 |
| `tests/test_deliktowa.py` | szkody / odpowiedzialność pracownicza | 19 |
| `tests/test_validacja.py` | walidacja danych wejściowych | 21 |
| `tests/test_podstawy.py` | spójność podstaw prawnych (stałe) | 5 |
| `tests/test_app_smoke.py` | dymny test interfejsu (AppTest) | 4 |
| **Razem** | | **84** |

Lint kodu (Ruff):

```bash
ruff check .
```

---

## Struktura projektu

```
├── app.py                          # Interfejs Streamlit (UI)
├── obliczenia.py                   # Logika obliczeniowa (bez zależności od UI)
├── walidacja.py                    # Walidacja danych wejściowych
├── requirements.txt                # Zależności runtime (przypięte wersje)
├── requirements-dev.txt            # Zależności deweloperskie (pytest, ruff)
├── pytest.ini                      # Konfiguracja pytest
├── ruff.toml                       # Konfiguracja lintera Ruff
├── README.md                       # Dokumentacja
├── .gitignore
├── .github/workflows/tests.yml     # CI – automatyczne testy
├── .streamlit/secrets.toml         # Sekrety (nie w git)
├── .devcontainer/                  # Konfiguracja devcontainer
└── tests/
    ├── test_obliczenia.py
    ├── test_deliktowa.py
    ├── test_validacja.py
    ├── test_podstawy.py
    └── test_app_smoke.py
```

Architektura rozdziela trzy warstwy:

1. **`obliczenia.py`** – czysta logika, `date_oceny` przekazywana jako parametr
   (testowalna bez Streamlit).
2. **`walidacja.py`** – sprawdzanie spójności danych.
3. **`app.py`** – wyłącznie interfejs i prezentacja.

---

## Historia zmian

| Faza | Zakres | Commit |
|---|---|---|
| 1 | Walidacja danych, bezpieczeństwo, dokumentacja, testy walidacji | `3e584ec` |
| 2 | Oddzielenie obliczeń od interfejsu, typy wyników, testy logiki | `791b4a3` |
| 3 | Roszczenia umowne, przepisy przejściowe 2018, oś czasu zdarzeń | `dd93e46` |
| 4 | Szkody i odpowiedzialność pracownicza (art. 442¹ k.c., art. 291 k.p.) | `e2c6dfb` |
| 5 | Część karna i zatarcie (art. 101, 102, 107 k.k.) | `629702f` |
| 6 | Stabilna wersja: przypięte zależności, CI, dokumentacja, refaktor walidacji | — |
| 7 | Raport: rodzaj zdarzenia (opisowo) + widok osi czasu zdarzeń | `d6a8801` |
| 8a | Uproszczenie `_oblicz_termin_koncowy` (usunięcie martwego fallbacku) | `e47897d` |
| 8b | Walidacja: umorzenie egzekucji nie przed datą zdarzenia deliktowego | `9a3c665` |
| 8c | Dokumentacja: licznik testów i notka bezpieczeństwa meta tagów | `3ef03a3` |
| A | Lint (Ruff), usunięcie martwego kodu i nieużywanych importów | `—` |
| B | Spójność podstaw prawnych: wspólne stałe dla logiki i interfejsu | `—` |
| C | Obsługa oskarżenia prywatnego (art. 101 § 2 k.k.) | `—` |
| D | Bezwzględny limit 20 lat od czynu po resecie biegu (art. 442¹ § 2 k.c.) | `—` |
| E | Dopełnienie walidacji deliktów i daty oskarżenia prywatnego | `—` |
| F | Dokumentacja: uzupełnienie historii zmian i opisu funkcji | `—` |

> Fazy 7–8c są zacommitowane. Fazy A–F to bieżący przegląd kodu (stan: niecommitowany).

---

## Licencja

Projekt prywatny / edukacyjny.
