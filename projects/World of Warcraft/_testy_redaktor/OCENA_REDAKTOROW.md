# Ocena redaktorów AI — 5 pierwszych misji (Amani / Forest Troll)

Metoda: dla każdej misji porównałem `01_draft_tlumacza` z czterema wersjami
(`03_redaktor_1/2/3/8`) różnicowo, a każdą zmianę zważyłem względem `00_prompt_redaktora`
(EN jako źródło prawdy, wiążące MAPOWANIA, reguły fleksji, głos rasy, „najmniejsza skuteczna zmiana").

Skala 0–100. Kryteria: **a. płynność**, **b. polska naturalność**, **c. dopasowanie do rasy**, **d. jakość redakcji vs draft**.

---

## Wyniki zbiorcze (średnia z 4 kryteriów)

| Misja | Redaktor 1 | Redaktor 2 | Redaktor 3 | Redaktor 8 |
|---|---|---|---|---|
| 2143 — *The Path of the Amani* | 83 | **88** | 84 | 79 |
| 8852 — *(rozmowa z Kul'amarą)* | 84 | **88** | **88** | 76 |
| 8861 — *Test of Conviction* | 84 | **90** | 83 | 79 |
| 8864 — *Ahead of the Issue* | 87 | 84 | **89** | 80 |
| 8933 — *Breaching the Mist* | 83 | **88** | 88 | 82 |
| **ŚREDNIA** | **84** | **88** | **86** | **79** |

**Ranking: 🥇 Redaktor 2 (88) → 🥈 Redaktor 3 (86) → 🥉 Redaktor 1 (84) → Redaktor 8 (79).**

---

## Numer 1: Redaktor 2 — i dlaczego

Najbardziej **niezawodny i „produkcyjny"**. Wygrywa lub remisuje w 4 z 5 misji. Jego przewaga to
poprawność gramatyczna + wierność, przy zachowaniu naturalnej polszczyzny i powściągliwości
(„najmniejsza skuteczna zmiana"):

- **Test loa (8861) — kluczowy.** Jako jedyny konsekwentnie poprawił rodzaj/liczbę loa:
  „Byli tu... nie odpowiadali" → **„Loa były tu... nie odpowiadały"**, „my, loa, wybieraliśmy" →
  **„wybierałyśmy"**, „nie udzielilibyśmy" → **„nie udzieliłybyśmy"**, „loa opuścili" → **„opuściły"**.
  To było najczęściej przeoczane (R1, R3, R8 się potykały).
- **Spójność rodzaju postaci (8852).** Liadrin = kobieta → konsekwentnie „elfko"/„ta elfka".
  R1 i R8 poprawili to tylko częściowo (zostawili „elfie"/„ten elf").
- **Fleksja nazw (8933).** „Odnalezienie Halazzi" → **„Halazziego"** (imię męskie odmienne),
  przy jednoczesnym zachowaniu zamrożonego terminu „Świątynia Halazzi". R1 i R8 tego nie złapali.
- **Wierność tytułów.** „Test of Conviction" zostawił jako „Próba przekonań" (poprawnie);
  „Breaching the Mist" → **„Przedzieranie się przez mgłę"** — dokładnie forma wskazana w briefie.
- **Naturalne idiomy.** „use our heads" → **„ruszymy głową"** zamiast kalki „użyjemy głów".

Słabszy punkt: bywa zachowawczy — w 8864 nie odtworzył gry słów w tytule i nie ujednolicił
imienia Helthry. Stąd jego jedyny wynik poniżej peletonu.

---

## Redaktor 3 — najlepszy stylista, drugie miejsce

Najwyższy sufit językowy i najlepszy zmysł głosu trolla (twardy, ponury, plemienny). Błyszczy w 8864:
tytuł **„O głowę przed problemem"** genialnie odtwarza dwuznaczność EN „Ahead = A Head of the Issue"
(quest o ścinaniu głów) i jako jedyny **ujednolicił imię Helthry** (Kruszycielka) między celem a dialogiem.
Ale: **przegrywa test loa w 8861** — zostawił/wprowadził formy męskie („Oni byli", „nie zamierzaliśmy
udzielić"), tylko 1 z 4 poprawek. Ma też tendencję do **nadredakcji** (przepisuje poprawne zdania,
podnosi rejestr: „pomsta", „pałałam", „przezeń"), co łamie regułę „najmniejszej skutecznej zmiany",
i zostawia odmienione „loą" zamiast nieodmiennego „loa".

## Redaktor 1 — sprawne pióro, ale błędy wierności

Bardzo płynny i odważny (jako jedyny naprawił kalkę „naostrzyć ostrze" → „naostrzę klingę";
dobre tytuły-gry-słów w 8864). Problemy dotyczą **wiążących ograniczeń**:
- **Złamał zmapowany termin** w 2143: „Rubież **Akil'zona**" (forma bazowa z mapowania) „poprawił"
  na „Akil'zon" **3×** — to naruszenie reguły o niezmienności wnętrza terminów wielowyrazowych.
- **Dryf tytułu** 8861: „Test of Conviction" → „Próba **wiary**" (conviction = przekonanie, nie wiara),
  i przeniósł ten dryf do treści.
- Niespójny rodzaj Liadrin (8852), przeoczona fleksja „Halazziego" (8933).

## Redaktor 8 — najwięcej twardych błędów

Łapie pojedyncze rzeczy (puste `npc_pl` w 2143, część form loa, dokładny tytuł 8933), ale kumuluje
najwięcej **błędów gramatyczno-strukturalnych**:
- **Systemowa nie-odmiana imienia Halazzi** (8852, 8933): „odszukać Halazzi", „z Halazzi",
  „błogosławieństwa Halazzi" — imię męskie powinno się odmieniać (Halazziego/Halazzim).
- **Usunął nawiasy `< >`** didaskaliów w 8861 (naruszenie struktury/placeholderów).
- Regresje w 2143: wokatyw „Jarra" zamiast „Jarro", „Nalorakk" zamiast „Nalorakku".
- Apozycja „Maisara" zamiast „Maisarę" (8852), niespójny rodzaj „ten elf" (8852).

---

## Jak podnieść jakość i naturalność (rekomendacje)

1. **Reguła loa „na sztywno".** Dopisz do briefu wyraźnie: *loa jako bóstwo/zbiorowość = rodzaj
   żeński; mnogo → żeńska liczba mnoga (były, opuściły, wybierałyśmy); „my, loa" w ustach loa =
   „-łyśmy".* To był najsłabszy punkt 3 z 4 redaktorów — wart osobnej sekcji z 4–5 przykładami.

2. **Rozwiąż sprzeczne mapowania przed redakcją.** W 8864 `MAPOWANIA_NPC` mówi „Miażdżycielka
   Helthra", a `MAPOWANIA_SŁÓW` „Helthra Kruszycielka" — stąd niespójny draft. Dodaj pre-pass, który
   wykrywa konflikty i regułę rozstrzygającą (np. „term/keyword wygrywa w tekście, jedna forma
   propagowana wszędzie").

3. **Rozdziel „termin zamrożony" od „imienia odmiennego" z przykładami per nazwa.**
   Np. *„Świątynia Halazzi" — wnętrze zamrożone; ale samodzielne „Halazzi" odmieniaj: Halazziego,
   Halazzim.* To usunie naraz nad-korektę R1 (Akil'zona) i pod-odmianę R8 (Halazzi).

4. **Wstrzyknij „kartę postaci" do każdej linii** (płeć + rasa mówcy i adresata): Liadrin = F →
   elfka/elfko; gracz = forma męska. Ucięłoby to wszystkie niespójności rodzaju (R1, R8).

5. **Walidacja strukturalna programistyczna (po redakcji).** Diff sprawdzający: liczba linii,
   nienaruszone `< >`, placeholdery, ID. Złapałby usunięcie nawiasów przez R8.

6. **Pod-check tytułów = obraz + gra słów EN.** Tytuł ma odtwarzać dosłowne *i* przenośne znaczenie
   (head/ahead, breaching). Najlepsze tytuły (R3) pokazują wartość — wpisz to do checklisty.

7. **Linter spójności + kalek.** Jedno EN → jedna forma PL we wszystkich polach (Helthra);
   wykrywaj dosłowne powtórzenia typu „naostrzyć ostrze".

8. **Kalibracja „najmniejszej skutecznej zmiany".** Mierz wskaźnik *edycje vs realnie naprawione
   błędy*. R3 ma świetne ucho, ale nadpisuje poprawne zdania — to ryzyko regresji i niespójności.

9. **Dwa przebiegi: poprawność → styl.** Najpierw twarda warstwa (gramatyka, rodzaj, mapowania,
   struktura — profil R2), potem warstwa naturalności/głosu (ucho R3). Profil R2 sugeruje, że
   „correctness-first" daje najlepszy wynik produkcyjny.

10. **Selekcja ensemble.** Najmocniejszy wynik dałby pipeline: **baza = R2**, a następnie selektywny
    import lepszych sformułowań R3 (gry słów w tytułach, idiomy) pod kontrolą walidatora.
