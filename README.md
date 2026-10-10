# Kalkulator-Prawny

Aplikacja do analizy przedawnienia roszczeń cywilnych i karnych oraz zatarcia skazań.

## Funkcjonalności

- **Analiza cywilna**: przedawnienie roszczeń umownych, deliktowych, z wyroków i egzekucji
- **Analiza karna**: przedawnienie karalności (art. 101, 102 k.k.)
- **Zatracie skazań**: termin usunięcia wpisu z KRK (art. 107 k.k.)
- **Walidacja danych**: blokada obliczeń przy sprzecznych lub niepełnych danych
- **Ochrona hasłem**: dostęp chroniony sekretem w `st.secrets`

## Wymagania

- Python 3.9+
- Streamlit
- python-dateutil

## Instalacja i uruchomienie

```bash
# 1. Sklonuj repozytorium
git clone https://github.com/byku-17/Kalkulator-Prawny.git
cd Kalkulator-Prawny

# 2. Zainstaluj zależności
pip install -r requirements.txt

# 3. Skonfiguruj hasło dostępu
# Utwórz plik .streamlit/secrets.toml:
mkdir -p .streamlit
echo 'HASLO_DO_APLIKACJI = "twoje_haslo"' > .streamlit/secrets.toml

# 4. Uruchom aplikację
streamlit run app.py
```

Aplikacja będzie dostępna pod adresem `http://localhost:8501`.

## Konfiguracja sekretów

Plik `.streamlit/secrets.toml` (nie commituj do git!):

```toml
HASLO_DO_APLIKACJI = "silne_haslo_dostepu"
```

## Użycie

1. Wprowadź hasło dostępu
2. Wybierz kategorię roszczenia (umowna / deliktowa)
3. Wypełnij daty:
   - **Oś czasu cywilna**: data bazowa, wpłaty, wyrok, egzekucja, umorzenie
   - **Sfera karna**: data czynu, kwalifikacja, wszczęcie/umorzenie postępowania, wyrok, wykonanie kary
4. Kliknij "Przeprowadź analizę"
5. Przeczytaj wyniki i kartę dat brzegowych

## Walidacja danych

Aplikacja sprawdza spójność wprowadzonych dat i blokuje obliczenia przy wykryciu błędów:
- Umorzenie egzekucji bez daty wszczęcia
- Wykonanie kary bez daty wyroku
- Nieprawidłowa kolejność dat (np. wyrok przed czynem)
- Umorzenie postępowania karnego bez wszczęcia

Analizę karną można przeprowadzić niezależnie od cywilnej (wystarczy data czynu).

## Zastrzeżenie prawne

⚠️ **Narzędzie ma charakter pomocniczy i informacyjny.** Wyniki nie stanowią wiążącej porady prawnej. Część cywilna opiera się na art. 118, 123, 124, 125, 442¹ k.c. Część karna na art. 101, 102, 107 k.k. Zawsze skonsultuj się z prawnikiem.

## Testy

```bash
# Uruchom testy (wymaga pytest)
pip install pytest
pytest tests/ -v
```

## Struktura projektu

```
├── app.py              # Główna aplikacja Streamlit
├── requirements.txt    # Zależności
├── README.md           # Ta dokumentacja
├── .streamlit/
│   └── secrets.toml    # Sekrety (nie w git!)
├── .devcontainer/      # Konfiguracja devcontainer
└── tests/              # Testy jednostkowe (faza 2+)
```

## Licencja

Projekt prywatny / edukacyjny.