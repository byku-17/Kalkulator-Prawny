# Kalkulator-Prawny

Narzędzie do **szybkiej oceny, czy roszczenie / tytuł wykonawczy jest przedawniony
i czy wierzyciel może jeszcze działać**. Obejmuje: roszczenia z umów pożyczki i kart
kredytowych, tytuły wykonawcze cywilne (art. 125 k.c.) i karne (art. 103 k.k.),
deficyty (pracownik / osoba trzecia), karalność czynów oraz zatarcie skazania.
Aplikacja webowa (Streamlit), logika oddzielona od interfejsu i pokryta testami.

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

Interfejs prowadzi przez dwa pytania:
1. **Typ sprawy** – klient (pożyczka / karta kredytowa) lub deficyt (pracownik / osoba trzecia).
2. **Co już się stało** – brak postępowania, wyrok/nakaz cywilny, egzekucja,
   postępowanie karne, zatarcie skazania.

Pola pokazują się tylko dla wybranych etapów, a wynik to **karta decyzyjna**
(„nieprzedawnione do X – możesz działać" / „przedawnione – nic nie zrobisz").

- **Roszczenie z umowy pożyczki / karty** – art. 118 k.c. w zw. z art. 720 k.c. (3 lata + koniec roku),
  wpłaty (art. 123), egzekucja (art. 123 § 1 pkt 1, art. 124).
- **Tytuł wykonawczy cywilny** – art. 125 § 1 k.c. (6 lat; 10 lat przed 09.07.2018),
  start od daty klauzuli wykonalności lub orzeczenia.
- **Tytuł wykonawczy karny** – art. 103 § 1 k.k. (30/15/10 lat od uprawomocnienia).
- **Deficyty** – art. 291 k.p. (pracownik) lub art. 442¹ § 1/§ 2 k.c. (osoba trzecia).
- **Karalność (sprawy wielowątkowe)** – wiele kwalifikacji naraz, karalność per czyn
  (art. 101/102 k.k.).
- **Zatarcie skazania** – art. 107 k.k.
- **Walidacja danych** i **ochrona hasłem** dostępu.

---

## Zakres i podstawy prawne

### Część cywilna – roszczenia umowne
| Zagadnienie | Podstawa | Zastosowana reguła |
|---|---|---|
| Roszczenie z umowy pożyczki / karty | art. 118 k.c. w zw. z art. 720 k.c. | 3 lata od wymagalności |
| Przepisy przejściowe 2018 | art. 5 ustawy z 13.04.2018 | nowe przepisy dla roszczeń nieprzedawnionych na 09.07.2018; dawne – tylko dla przedawnionych wcześniej |
| Uznanie długu / wpłata | art. 123 k.c. | nowy bieg od daty uznania |
| Wszczęcie egzekucji | art. 124 k.c. | zawieszenie biegu |
| Umorzenie egzekucji | art. 124 § 2 k.c. | bieg od nowa od umorzenia |
| Prawomocny wyrok / nakaz (tytuł wykonawczy) | art. 125 § 1 k.c. | 6 lat (10 lat przed 09.07.2018); start: data klauzuli wykonalności lub orzeczenia |

### Część cywilna – szkody / pracownik
| Zagadnienie | Podstawa | Zastosowana reguła |
|---|---|---|
| Szkoda bez kwalifikacji karnej | art. 442¹ § 1 k.c. | 3 lata od dowiedzenia się, max 10 lat od zdarzenia |
| Szkoda z przestępstwa | art. 442¹ § 2 k.c. | 20 lat od popełnienia czynu; podlega przerwaniu (art. 123 k.c.) |
| Odpowiedzialność pracownicza (nieumyślna) | art. 291 § 2 k.p. | 1 rok od powzięcia wiadomości, max 3 lata od wyrządzenia |
| Odpowiedzialność pracownicza (umyślna) | art. 291 § 3 k.p. | przepisy k.c. (art. 442¹ § 1 k.c.: 3 lata, max 10 lat) |

### Część karna
| Zagadnienie | Podstawa | Zastosowana reguła |
|---|---|---|
| Ustawowe przedawnienie karalności | art. 101 § 1 k.k. | termin zależny od kwalifikacji czynu |
| Karalność – oskarżenie prywatne | art. 101 § 2 k.k. | 1 rok od dowiedzenia się o sprawcy, max 3 lata od czynu |
| Przedłużenie karalności | art. 102 § 1 k.k. | +10 lat (art. 101 § 1) lub +5 lat (oskarżenie prywatne), jeżeli wszczęto postępowanie w terminie |
| Przedawnienie wykonania kary | art. 103 § 1 k.k. | 30/15/10 lat od uprawomocnienia (zależnie od kary) |
| Zatarcie z mocy prawa | art. 107 § 1, § 3, § 4, § 4a k.k. | grzywna 1 rok; ograniczenie wolności 3 lata; pozbawienie wolności 10 lat |
| Zatarcie na wniosek skazanego | art. 107 § 2 k.k. | po 5 latach, gdy kara pozbawienia wolności ≤ 3 lat |

> Rejestr wszystkich stosowanych przepisów i status ich weryfikacji: [`docs/przepisy.md`](docs/przepisy.md).

---

## Ograniczenia i przypadki nieobsługiwane

Aplikacja **jawnie zgłasza** przypadki, których nie obsługuje, zamiast podawać
niepewne terminy jako pewne:

- Przepisy szczególne przewidujące odrębne terminy przedawnienia.
- art. 442¹ § 3 i § 4 k.c. (szkoda na osobie; małoletni) — poza zakresem aplikacji.
- Przedłużenie karalności, gdy nie podano daty wszczęcia postępowania przeciwko osobie.
- Karalność przy oskarżeniu prywatnym bez daty dowiedzenia się o osobie sprawcy
  (status „dane niewystarczające”).
- Zatarcie: przeszkody z art. 107 § 6 k.k. (środek karny/przepadek/środek kompensacyjny)
  oraz zawieszenie wykonania kary (6 miesięcy od upływu okresu próby).
- Sporna kwestia stosowania reguły końca roku (art. 118 § 1 k.c.) do terminów
  z art. 442¹ k.c. — aplikacja jej nie stosuje, co wymaga weryfikacji prawnej.
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
| `tests/test_obliczenia.py` | logika umowna, karna, zatarcie | 44 |
| `tests/test_deliktowa.py` | szkody / odpowiedzialność pracownicza | 22 |
| `tests/test_validacja.py` | walidacja danych wejściowych | 22 |
| `tests/test_podstawy.py` | spójność podstaw prawnych (stałe) | 5 |
| `tests/test_app_smoke.py` | dymny test interfejsu (AppTest) | 4 |
| **Razem** | | **97** |

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
├── docs/przepisy.md                # Rejestr przepisów i status weryfikacji
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
| A | Lint (Ruff), usunięcie martwego kodu i nieużywanych importów | `b15f312` |
| B | Spójność podstaw prawnych: wspólne stałe dla logiki i interfejsu | `b15f312` |
| C | Obsługa oskarżenia prywatnego (art. 101 § 2 k.k.) | `b15f312` |
| D | Limit 20 lat po resecie biegu (art. 442¹ § 2 k.c.) – cofnięty w Fix 11 | `b15f312` |
| E | Dopełnienie walidacji deliktów i daty oskarżenia prywatnego | `b15f312` |
| F | Dokumentacja: uzupełnienie historii zmian i opisu funkcji | `b15f312` |
| 10 | Pracownik: art. 291 § 2 k.p. (1 rok / 3 lata) + § 3 (umyślne → k.c.) | `76fbb95` |
| 11 | art. 442¹ § 2 k.c. nie jest limitem nieprzerywalnym | `864dc1f` |
| 12 | Reżim przejściowy 2018 wg wymagalności (skorygowany w 19) | `1a7eeda` |
| 13 | Zatarcie: aktualne okresy art. 107 k.k. | `e015f51` |
| 14 | Egzekucja: art. 123 § 1 pkt 1 + art. 124 § 1/§ 2 k.c. | `9747ff7` |
| 15 | Ostrzeżenie: sporna reguła końca roku vs art. 442¹ | `90767e9` |
| 16 | art. 125 § 1 k.c. – 10 lat dla orzeczeń przed 09.07.2018 | `9e97717` |
| 17 | Rejestr przepisów (`docs/przepisy.md`) | `0ff04ef` |
| 18 | art. 102 § 1 k.k. – +5 lat dla oskarżenia prywatnego | `162ecd6` |
| 19 | Przepisy przejściowe 2018 wg art. 5 ustawy nowelizującej | `c5b30fb` |
| 20 | art. 442¹ § 3 k.c. (szkoda na osobie) – cofnięty w 25 | `3ca2d1b` |
| 21 | Redesign UI: 2 kroki + karta decyzyjna | `5247c0e` |
| 22 | art. 103 k.k. – przedawnienie wykonania kary | `0ea7062` |
| 23 | Multi-select kwalifikacji czynów (sprawy wielowątkowe) | `8dcc1af` |
| 24 | Data klauzuli wykonalności jako start art. 125 k.c. | `20b75be` |
| 25 | Porządki: usunięcie art. 442¹ § 3 (poza zakresem) + README | `—` |

> Rejestr zweryfikowanych przepisów: [`docs/przepisy.md`](docs/przepisy.md).

---

## Licencja

Projekt prywatny / edukacyjny.
