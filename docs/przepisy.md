# Rejestr przepisów używanych w aplikacji

Zestawienie wszystkich przepisów stosowanych w kalkulatorze wraz ze statusem weryfikacji
z aktualnym tekstem urzędowym (LEX / ISAP, teksty jednolite).

Legenda statusu:
- ✅ **zweryfikowany** – porównany z tekstem urzędowym,
- ⚠️ **do weryfikacji** – zaimplementowany, ale jeszcze niepotwierdzony tekstem urzędowym,
- ⛔ **nieobsługiwany** – przepis istotny, ale świadomie nie modelowany (jawnie oznaczony w UI/README).

---

## Kodeks cywilny

| Artykuł | Reguła w aplikacji | Miejsce | Status |
|---|---|---|---|
| art. 118 § 1 k.c. | 3 lata (działalność gosp.) + reguła końca roku | `analiza_cywilna`, `_oblicz_termin_koncowy` | ✅ zweryfikowany (Dz.U.2026.795) |
| art. 120 § 1 k.c. | bieg od wymagalności (kryterium przepisów przejściowych) | `_czy_stara_przedawnienie`, `analiza_cywilna` | ✅ zweryfikowany (Dz.U.2026.795) |
| art. 123 § 1 pkt 1 k.c. | przerwanie – czynność przed sądem/organem egzekwującym (egzekucja) | `analiza_cywilna`, `analiza_deliktowa` | ✅ zweryfikowany (Dz.U.2026.795) |
| art. 123 § 1 pkt 2 k.c. | przerwanie – uznanie roszczenia (wpłata) | `analiza_cywilna`, `analiza_deliktowa` | ✅ zweryfikowany |
| art. 123 § 1 pkt 3 k.c. | uchylony – mediacja nie modelowana | — | ✅ zweryfikowany |
| art. 124 § 1 k.c. | po przerwaniu przedawnienie biegnie na nowo | `analiza_cywilna`, `analiza_deliktowa` | ✅ zweryfikowany |
| art. 124 § 2 k.c. | nie biegnie na nowo do zakończenia postępowania | `analiza_cywilna`, `analiza_deliktowa` | ✅ zweryfikowany |
| art. 125 § 1 k.c. | wyrok: 6 lat (10 lat, gdy orzeczenie przed 09.07.2018) | `_lata_po_wyroku` | ✅ zweryfikowany |
| art. 442¹ § 1 k.c. | 3 lata od dowiedzenia + bezwzględny limit 10 lat | `_oblicz_termin_deliktowy` | ✅ zweryfikowany (Dz.U.2026.795) |
| art. 442¹ § 2 k.c. | 20 lat od popełnienia czynu | `_oblicz_termin_deliktowy` | ✅ zweryfikowany |
| art. 442¹ § 3 k.c. | szkoda na osobie: min. 3 lata od dowiedzenia (znosi limit 10 lat) | `_oblicz_termin_deliktowy` | ✅ zweryfikowany (Dz.U.2026.795) |
| art. 442¹ § 4 k.c. | małoletni | — | ⛔ nieobsługiwany |
| art. 121 k.c. | zawieszenie biegu (siła wyższa itd.) | — | ⛔ nieobsługiwany |
| art. 5 ustawy z 13.04.2018 (Dz.U. 2018 poz. 1104) | przepisy przejściowe: nowe przepisy dla roszczeń nieprzedawnionych na 09.07.2018 (ust. 1); dawne – tylko dla przedawnionych przed tą datą | `_czy_stara_przedawnienie` | ✅ zweryfikowany |

## Kodeks pracy

| Artykuł | Reguła w aplikacji | Miejsce | Status |
|---|---|---|---|
| art. 291 § 1 k.p. | 3 lata – zwykłe roszczenia pracownika (nie używane wprost) | — | ✅ zweryfikowany (Dz.U.2026.1245) |
| art. 291 § 2 k.p. | pracownik nieumyślny: 1 rok od wiadomości, max 3 lata od wyrządzenia | `_oblicz_termin_deliktowy` | ✅ zweryfikowany |
| art. 291 § 3 k.p. | pracownik umyślny → przepisy k.c. (art. 442¹ § 1) | `_oblicz_termin_deliktowy` | ✅ zweryfikowany |
| art. 291 § 5 k.p. | roszczenie stwierdzone orzeczeniem/ugodą → 10 lat | — | ⛔ nieobsługiwany |

## Kodeks karny

| Artykuł | Reguła w aplikacji | Miejsce | Status |
|---|---|---|---|
| art. 101 § 1 k.k. | przedawnienie karalności wg zagrożenia karą (40/20/15/10/5) | `analiza_karna`, `app.py` (OPCJE_KK) | ✅ zweryfikowany (Dz.U.2025.383) |
| art. 101 § 2 k.k. | oskarżenie prywatne: 1 rok od sprawcy, max 3 lata od czynu | `analiza_karna` | ✅ zweryfikowany |
| art. 102 § 1 k.k. | przedłużenie: +10 lat (art. 101 § 1), +5 lat (oskarżenie prywatne) | `analiza_karna` | ✅ zweryfikowany |
| art. 103 § 1 k.k. | przedawnienie wykonania kary (tytuł wykonawczy karny): 30/15/10 lat od uprawomocnienia | `analiza_wykonania_kary` | ✅ zweryfikowany (Dz.U.2025.383) |
| art. 107 § 1 k.k. | pozbawienie wolności: 10 lat | `analiza_zatarcia` | ✅ zweryfikowany (Dz.U.2025.383) |
| art. 107 § 2 k.k. | na wniosek: 5 lat (kara ≤ 3 lat) | `analiza_zatarcia` | ✅ zweryfikowany |
| art. 107 § 3 k.k. | dożywotnie pozbawienie wolności: 10 lat | `analiza_zatarcia` | ✅ zweryfikowany |
| art. 107 § 4 k.k. | ograniczenie wolności: 3 lata | `analiza_zatarcia` | ✅ zweryfikowany |
| art. 107 § 4a k.k. | grzywna: 1 rok | `analiza_zatarcia` | ✅ zweryfikowany |
| art. 107 § 5 k.k. | odstąpienie od wymierzenia kary: 1 rok | — | ⛔ nieobsługiwany |
| art. 107 § 6 k.k. | przeszkody zatarcia (środki karne/kompensacyjne/przepadek) | — | ⛔ nieobsługiwany |

---
## Do dokończenia weryfikacji (⚠️)

Wszystkie stosowane przepisy zostały zweryfikowane z tekstem urzędowym.
Do rozważenia (poza zakresem): art. 5 ust. 2 i ust. 3 ustawy nowelizującej 2018
(reguła „terminu korzystniejszego” oraz odrębny reżim dla konsumentów).

> Uwaga: część merytoryczna ma charakter orientacyjny i wymaga końcowej weryfikacji
> przez prawnika przed wdrożeniem produkcyjnym.
