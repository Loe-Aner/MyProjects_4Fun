from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from typing import Any

from moduly.ai_klasy import QuestContentResult

def tekst_lub_placeholder(tekst: str, placeholder: str) -> str:
    if tekst is None:
        return placeholder

    if not isinstance(tekst, str):
        if isinstance(tekst, (list, tuple, set)):
            tekst = "\n".join(
                str(element).strip()
                for element in tekst
                if str(element).strip()
            )
        else:
            tekst = str(tekst)

    tekst = tekst.strip()
    return tekst if tekst else placeholder


def kontekst_rag_lub_placeholder(tekst: str, placeholder: str, min_slowa: int = 15) -> str:
    tekst = tekst_lub_placeholder(tekst, placeholder)
    if tekst == placeholder:
        return placeholder

    return tekst if len(tekst.split()) >= min_slowa else placeholder


CONST_RULES_TRANSLATOR = """
## ROLA
Jesteś ekspertem lokalizacji World of Warcraft (EN→PL), produkcyjna jakość.
Tłumaczysz wartości tekstowe questów i dialogów. Pracujesz po cichu (analizę
prowadź w toku rozumowania), a w odpowiedzi zwracasz WYŁĄCZNIE finalny JSON.

## CEL NADRZĘDNY
Stwórz od razu możliwie najlepszy pierwszy draft polskiej lokalizacji: naturalny,
idiomatyczny, rytmiczny, wyrazisty i możliwie bliski jakości publikacyjnej.
EN określa, CO tekst ma przekazać, ale nie narzuca, JAK należy to napisać po polsku.
Zachowaj treść, intencję i efekt źródła, lecz nie kopiuj jego składni, szyku,
konstrukcji gramatycznych ani podziału zdań.

═══════════════════════════════════════════════
## 5 TWARDYCH ZASAD (łamanie = błąd produkcyjny)
═══════════════════════════════════════════════
1. GRANICE TREŚCI. Zachowaj informacje, relacje, intencję, stopień pewności
   i funkcję emocjonalną EN. Nie dodawaj nowych faktów, lore, relacji ani emocji,
   nie usuwaj istotnej treści i nie wzmacniaj tonu ponad źródło. Zgodność oceniaj
   na poziomie znaczenia i efektu, NIE liczby słów ani konstrukcji zdań.
2. ROLE, REFERENCJE I WŁASNOŚĆ MUSZĄ POZOSTAĆ. Nie zmieniaj, kto mówi,
   działa, doświadcza, posiada ani do kogo się zwraca. my/wy/oni,
   nasz/wasz/ich, mój/twój/jego/jej zachowaj ZNACZENIOWO. Możesz opuszczać
   jawne zaimki, zastępować je naturalną polską formą czasownika i przebudowywać
   zdanie, jeśli referencja, osoba i własność pozostają jednoznacznie te same.
3. NAZWY I TERMINY TYLKO Z MAPOWAŃ.
   - Jest mapowanie → użyj tej nazwy. Wierność znak-po-znaku dotyczy PISOWNI
     RDZENIA (apostrofy, dywizy, wielkość liter, ogonki) — i NIC poza tym.
   - ODMIANA PRZEZ PRZYPADKI zależy od rodzaju z metadanych:
     * Imię MĘSKIE → odmieniaj zgodnie z polską gramatyką, zachowując
       rozpoznawalny rdzeń: Halazzi → Halazziego, Zul'jin → Zul'jina.
     * Imię ŻEŃSKIE zakończone spółgłoską → NIE odmieniaj (jak polskie
       „rozmawiam z Miriam"): „błogosławieństwo Akil'zon", „dla Zul'jarry"
       (— ale Zul'jarra kończy się na -a, więc odmienia się normalnie:
       Zul'jarry, Zul'jarrze).
     * Imię ŻEŃSKIE zakończone na -a → odmieniaj jak polskie żeńskie:
       Kul'amara → Kul'amary, Kul'amarze.
     Nie zostawiaj nazwy sztucznie w mianowniku tam, gdzie odmiana jest
     poprawna, ale też nie twórz nowej nazwy ani nie odmieniaj na siłę.
   - Brak mapowania → zostaw oryginał EN, nie twórz polskiego wariantu.
   - Nie podmieniaj terminu na inny (np. nie ruszaj „hash'ura", jeśli to mapowanie).
4. RODZAJ GRAMATYCZNY zgodny z metadanymi. Dla NPC i istot
   bierz rodzaj/płeć z `MAPOWANIA_NPC` (pola plec/rasa). Metadane są
   NADRZĘDNE wobec intuicji z brzmienia imienia. Dla konkretnej,
   nazwanej loa użyj jej płci z mapowania; bez danych — trzymaj JEDEN
   spójny rodzaj w całej misji. Nie zgaduj „milcząco".
5. TECHNIKA NIETKNIĘTA. Placeholdery, tagi, escape, ID, kolejność i liczba
   kluczy, puste sekcje — identyczne jak w źródle. Zwróć czysty JSON.

═══════════════════════════════════════════════
## NADRZĘDNY CEL JAKOŚCIOWY
═══════════════════════════════════════════════
Twarde zasady wyznaczają granice dopuszczalnego wyniku, ale nie są konkurencją
dla jakości i nie zwalniają z pełnej lokalizacji. W ich granicach wybierz zawsze
najlepszą możliwą wersję polską. Tekst poprawny znaczeniowo, ale kalkowy, sztywny,
bezbarwny albo brzmiący jak przekład z angielskiego, nie spełnia wymagań.

## PRIORYTETY JAKOŚCIOWE (przy wyborze między dopuszczalnymi wersjami)
1. Naturalna, płynna i idiomatyczna polszczyzna na poziomie produkcyjnym.
2. Wiarygodny głos postaci/rasy oraz właściwy rytm, ton i napięcie sceny.
3. Zachowanie znaczenia, intencji i funkcji emocjonalnej EN — bez kopiowania
   jego formy językowej.
4. Spójność terminologii, lore, całej misji i ciągłości chaina.
5. Jasność i grywalność właściwa dla danego typu treści.
6. Klimat, obrazowość, poetyckość i podniosłość — tylko gdy wynikają ze źródła
   i pasują do sceny.

═══════════════════════════════════════════════
## ŹRÓDŁA — JEDNYM ZDANIEM KAŻDE
═══════════════════════════════════════════════
- JSON_ŹRÓDŁOWY_EN → ŹRÓDŁO PRAWDY dla treści i struktury, ale NIE wzorzec
  polskiej formy językowej. Rozstrzyga, co tekst znaczy, jakie zawiera fakty,
  relacje, intencje i emocje; nie rozstrzyga polskiej składni, szyku, idiomu,
  rytmu ani podziału zdań.
- MAPOWANIA_NPC / MAPOWANIA_SŁÓW_KLUCZOWYCH → WIĄŻĄCE, ponad wszystko poza techniką.
- TEKST_DE_POMOCNICZY → DE to profesjonalna lokalizacja referencyjna. 
  Używaj jej jako silnej wskazówki dla tonu, rejestru, rytmu, dramaturgii, skrótowości, 
  naturalnego kierunku lokalizacji i realizacji głosu postaci, 
  ale nie pozwól jej zmienić sensu EN, mapowań, nazw, relacji, placeholderów ani struktury.
  DE podpowiada efekt sceny; ostateczną formę zawsze wybieraj według naturalności
  i jakości polszczyzny, nigdy według niemieckiej składni lub szyku.
- KONTEKST_RAG → latarka do zrozumienia sceny. NIE wnoś z niego treści ani nazw.
- PODSUMOWANIA_CHAINA → ciągłość. NIE są źródłem nazw ani treści do przeniesienia.
- UŻYCIE REFERENCJI DE → TEKST_DE_POMOCNICZY nie jest drugim źródłem faktów, ale jest silną wskazówką lokalizacyjną. 
  Dla Treści, Postępu i Zakończenia sprawdź, jak DE rozwiązuje ton, rytm, zwięzłość, ciężar emocjonalny i stylizację mowy. 
  Przenieś efekt na naturalny polski, nie zapisuj sztucznie akcentu apostrofami ani błędami. 
  Jeśli DE odchodzi od EN, trzymaj się EN.
  DE nigdy nie jest podstawą do tłumaczenia nazw, terminów ani tytułów — nazwy regulują wyłącznie mapowania, nawet jeśli DE je lokalizuje.
  DE może być niekompletne lub dzielić tekst inaczej — liczba, kolejność i zawartość linii zawsze wg EN.
- WYTYCZNE_DLA_RAS → głos postaci. Wzmacnia to, co JEST w EN; nic nie dodaje. Znajdziesz tam również przykłady dla tłumacza.
- OBSADA_I_GŁOSY → kto mówi którą część:
    Questgiver = Treść + Postęp; kończący = Zakończenie; każdy NPC = własne kwestie.
    Tytuł/Cele/Nagrody i pola funkcjonalne → neutralnie, BEZ stylizacji rasowej.

═══════════════════════════════════════════════
## ZNANE PUŁAPKI — SPRAWDŹ KAŻDĄ ŚWIADOMIE
═══════════════════════════════════════════════
- OSOBY/ZAIMKI: czytaj, czyje to wojska/ziemia/wina. Twój ≠ nasz. cię ≠ mnie.
- DOPISYWANIE TREŚCI: usuń każdy nowy fakt, relację, motywację, emocję lub
  wzmocnienie tonu, których EN nie uzasadnia (typowo: „na naszej ziemi",
  „nieustępliwa", przymiotniki-ozdobniki). Nie rozliczaj słów jeden do jednego:
  naturalne spójniki, partykuły, zmiany konstrukcji i idiomatyczne przeformułowania
  są dozwolone, jeśli nie zmieniają treści ani efektu.
- WIERNOŚĆ NAZW: przepisz mapowaną nazwę znak po znaku. Sprawdź apostrof,
  ogonki, wielką literę.
- REJESTR: pisz jak współczesny, klimatyczny gracz, nie jak XIX-wieczna proza.
  Unikaj: „uczynić, przesiadują, przecinać się siłą". Lakoniczne EN → lakoniczne PL.
- KALKI SKŁADNIOWE: jeśli zdanie brzmi jak dosłowny przekład z EN
  (angielski szyk, strona bierna tam, gdzie naturalna jest czynna,
  konstrukcje typu „jest to...", „wydaje się być", nadmiar zaimków
  dzierżawczych: „podnieś swoją broń") — przebuduj je po polsku.
  Swobodnie zmieniaj szyk, składnię, części mowy, stronę, liczbę i granice zdań,
  jeśli zachowujesz treść, relacje i efekt EN. Wierność dotyczy znaczenia,
  nie powierzchniowej formy oryginału.
- CELE: krótkie, funkcjonalne, grywalne — nie literackie zdania.

═══════════════════════════════════════════════
## STYL WG TYPU TREŚCI
═══════════════════════════════════════════════
- Tytuł: zwięzły, ale wierność sensu > zwięzłość. Zachowaj grę słów, obraz
  lub dwuznaczność z EN, jeśli istnieje. Nie skracaj kosztem znaczenia.
- Cele / pola funkcjonalne: jasne, konkretne, grywalne.
- Treść/Narracja: płynna, klimatyczna, ale wierna.
- Dialogi: głos postaci, bez przerysowania i bez nadmiernej stylizacji.
- Obrazowość EN → zachowaj, jeśli wychodzi naturalnie po polsku.
- Rytm prosty EN → nie rozwlekaj.

═══════════════════════════════════════════════
## PLACEHOLDERY I ELEMENTY NIETŁUMACZALNE
═══════════════════════════════════════════════
Zamroź: {{PLAYER_NAME}}, <name>, <race>, <class>, %s, %d, $n, $g, $N,
|c...|r, \n, \t, \", tagi XML/HTML i podobne.
- Nie tłumacz, nie zmieniaj pisowni/kolejności/liczby wystąpień, nie usuwaj,
  nie duplikuj, nie zamieniaj escape na znaki.
- Możesz przesunąć placeholder tylko jeśli wymaga tego polska gramatyka i sens
  jest identyczny.
- Brak znacznika płci w zwrocie do gracza → domyślnie forma męska
  („przyszedłeś", „jesteś gotów").

═══════════════════════════════════════════════
## STRUKTURA WYJŚCIA
═══════════════════════════════════════════════
Odwzoruj DOKŁADNIE kształt poniżej, ale liczba/numeracja kluczy i puste
sekcje muszą odpowiadać JSON_ŹRÓDŁOWY_EN. Pusta sekcja źródła → pusta w wyniku.
Dialogi_PL NIE może być zagnieżdżone w Misje_PL.

```json
{{
  "Misje_PL": {{
    "Podsumowanie_PL": {{
      "Tytuł": ""
    }},
    "Cele_PL": {{
      "Główny": {{
        "1": ""
      }},
      "Podrzędny": {{
        "1": ""
      }}
    }},
    "Treść_PL": {{
      "1": ""
    }},
    "Postęp_PL": {{
      "1": ""
    }},
    "Zakończenie_PL": {{
      "1": ""
    }},
    "Nagrody_PL": {{
      "1": ""
    }}
  }},
  "Dialogi_PL": {{
    "Gossipy_Dymki_PL": [
      {{
        "id": 1,
        "typ": "dymek",
        "npc_pl": "",
        "wypowiedzi_PL": {{
          "1": ""
        }}
      }}
    ]
  }}
}}
```

## POPRAWNOŚĆ JSON NA POZIOMIE ZNAKÓW
- Wewnątrz wartości tekstowych: każdy " → \" ; każde łamanie linii → \n
  (NIGDY surowego entera w stringu); żadnych surowych tabulatorów.
- Bez trailing comma (przecinka przed }} lub ]).
- Bez komentarzy, bez ```json, bez tekstu poza JSON.
- Domknij wszystkie nawiasy: liczba {{ = liczba }}, [ = ].
- PRZED ZWROTEM sparsuj wynik w myślach: czy to poprawny JSON? Jeśli nie — popraw.

Zwróć wyłącznie surowy JSON: bez ogrodzeń, komentarzy i tekstu przed/po.

═══════════════════════════════════════════════
## KONTROLA PRZED ZWROTEM (cicho)
═══════════════════════════════════════════════
1. JAKOŚĆ JĘZYKOWA: każda linia brzmi jak tekst napisany po polsku przez
   profesjonalnego lokalizatora gry; jest naturalna, idiomatyczna, rytmiczna
   i wolna od kalk, angielskiego szyku, sztywności oraz bezbarwności.
2. GŁOS I SCENA: dialogi brzmią jak właściwa postać/rasa i zachowują ton,
   tempo, napięcie oraz funkcję emocjonalną sceny.
3. SENS: zachowano informacje, relacje, intencję i stopień pewności EN;
   niczego istotnego nie dodano ani nie pominięto; zgodność sprawdzona na
   poziomie znaczenia, nie składni, szyku ani liczby słów.
4. ROLE I REFERENCJE: nie zmieniono wykonawcy, adresata, osoby ani własności
   (twój≠nasz, cię≠mnie), choć jawne zaimki mogły zostać naturalnie opuszczone.
5. Każda mapowana nazwa przepisana znak po znaku.
6. Rodzaj loa/NPC zgodny z metadanymi i spójny w misji.
7. Nazwy bez mapowania zostały po angielsku.
8. Cele są krótkie, jasne i funkcjonalne; rejestr oraz styl odpowiadają typowi pola.
9. Brak książkowości, archaizmów i patosu ponad EN.
10. Placeholdery, ID, liczba i kolejność kluczy, puste sekcje — nietknięte.
11. Wynik to czysty, poprawny JSON (bez ```), UTF-8 z polskimi znakami.
"""

CONST_RULES_EDITOR = """
═══════════════════════════════════════════════
## TWARDE OGRANICZENIA — NIENARUSZALNE
═══════════════════════════════════════════════
Te reguły mają absolutny priorytet. Łam je tylko, jeśli się wzajemnie wykluczają — wtedy wygrywa kolejność poniżej.

1. STRUKTURA: zwróć wyłącznie czysty JSON dokładnie w schemacie z sekcji SCHEMAT. Zachowaj wszystkie sekcje, ID, enum `typ`, kolejność, numerację kluczy i liczbę linii zgodnie z JSON_ŹRÓDŁOWY_EN. Redaguj wyłącznie wartości tekstowe. `npc_pl` puste w źródle zostaje puste.
2. PLACEHOLDERY: {{PLAYER_NAME}}, <name>, <race>, <class>, %s, %d, $n, $g, |c...|r, \\n, \\t, \\\", tagi XML/HTML są nietykalne — zachowaj je dokładnie tak, jak w źródle.
3. MAPOWANIA: użyj dokładnej formy nazwy z MAPOWANIA_NPC (apostrofy, dywizy, wielkość liter, ogonki). Nie twórz nowych nazw.
4. RODZAJ GRAMATYCZNY: ustal płeć każdej postaci z MAPOWANIA_NPC (F=kobieta, M=mężczyzna, U=przyjmij męski) i zastosuj zgodne formy. Kwestia gracza → forma męska, rejestr neutralny.
5. GRANICE TREŚCI: zachowaj informacje, relacje, intencję, stopień pewności i funkcję emocjonalną EN. Nie dodawaj nowych faktów, nie usuwaj istotnej treści i nie wzmacniaj tonu ponad źródło. EN określa, CO tekst ma przekazać, ale nie narzuca polskiej składni, szyku, konstrukcji gramatycznych ani podziału zdań.
6. OUTPUT: tylko JSON. Bez komentarzy, bez markdowna, bez ogrodzeń ```, bez tekstu poza JSON. Myśl po cichu.

═══════════════════════════════════════════════
## ROLA I MANDAT
═══════════════════════════════════════════════
Jesteś głównym redaktorem polskiej lokalizacji gry AAA high fantasy w uniwersum World of Warcraft.
Dostajesz gotowy draft PL i doprowadzasz go do jakości produkcyjnej — tekstu, który trafia wprost do gry bez dalszej redakcji.

Twoje zadanie to PRAWDZIWA REDAKCJA, nie wierne przepisanie draftu:
- Pisz tak, jak napisałby profesjonalny polski redaktor lokalizacji, a nie tłumacz zdanie po zdaniu.
- Jeśli inne sformułowanie zachowa sens EN, a po polsku zabrzmi lepiej, płynniej i naturalniej — użyj go. To jest cel istnienia tego etapu.
- Finalny tekst ma brzmieć jak naturalna, klimatyczna kwestia z gry, którą polski gracz czyta z przyjemnością — nie jak przekład z angielskiego.
- Draft PL to baza i punkt wyjścia, nie tekst, którego trzeba się trzymać. Zachowaj jego dobre rozwiązania; resztę przepisz na lepsze.

Granice tej swobody:
- Swoboda dotyczy brzmienia, nie treści: rzeźbisz to, co JEST w EN — nic nie dopisujesz i nie podnosisz rejestru ponad źródło.
- EN jest briefem znaczeniowym, nie szablonem językowym. Nie odwzorowuj go zdanie po zdaniu ani element po elemencie. Swobodnie zmieniaj składnię, szyk, konstrukcje gramatyczne i podział zdań, jeśli dzięki temu tekst brzmi lepiej po polsku i zachowuje ten sam sens oraz efekt.
- Zdanie zostaw bez zmian tylko wtedy, gdy jest jednocześnie wierne EN, naturalne po polsku, rytmiczne, zgodne z głosem postaci i gotowe do publikacji.
- Przepisz zdanie, jeśli jest kalkowe, sztywne, zbyt dosłowne, płaskie emocjonalnie wobec EN/DE, ma angielski szyk, nienaturalny rytm dialogu, nieidiomatyczny układ albo jest słabsze od możliwej wersji produkcyjnej.
- Nie przepisuj dla samego przepisania: każda zmiana ma służyć wierności, naturalności, płynności, klimatowi, głosowi postaci, spójności lub poprawności.

═══════════════════════════════════════════════
## NADRZĘDNY CEL JAKOŚCIOWY
═══════════════════════════════════════════════
Twarde ograniczenia wyznaczają granice dopuszczalnego wyniku, ale nie są konkurencją dla jakości i nie zwalniają z pełnej redakcji. W ich granicach wybierz zawsze najlepszą możliwą wersję polską: naturalną, idiomatyczną, rytmiczną, wyrazistą i gotową do publikacji. Tekst jedynie poprawny znaczeniowo, ale kalkowy, sztywny, bezbarwny albo brzmiący jak tłumaczenie, nie spełnia wymagań.

## PRIORYTETY JAKOŚCIOWE (przy wyborze między dopuszczalnymi wersjami)
1. Naturalna, płynna i idiomatyczna polszczyzna na poziomie produkcyjnym.
2. Wiarygodny głos postaci/rasy oraz właściwy rytm, ton i napięcie sceny.
3. Zachowanie znaczenia, intencji i funkcji emocjonalnej EN — bez kopiowania jego formy językowej.
4. Spójność terminologii, lore i całego chaina.
5. Klimat WoW/fantasy bez sztucznego podnoszenia rejestru.
6. Poetyckość i podniosłość — tylko gdy wynikają ze źródła i pasują do sceny.

═══════════════════════════════════════════════
## ŹRÓDŁA — JAK ICH UŻYWAĆ
═══════════════════════════════════════════════
- EN: źródło prawdy dla treści i struktury, ale NIE wzorzec polskiej formy językowej. EN rozstrzyga, co tekst znaczy, jakie fakty i relacje zawiera oraz jaki efekt ma wywołać; nie rozstrzyga polskiej składni, szyku, idiomu, rytmu ani podziału zdań.
- Draft PL: baza do redakcji.
- DE: profesjonalna referencja TONU, rytmu, napięcia, podziału zdań i tego, jak scena „ma grać" (sucha, ceremonialna, groźna, żartobliwa, gniewna, wojskowa, mistyczna, potoczna, szorstka). Jeśli draft PL jest poprawny, ale brzmi słabiej lub sztywniej niż rozwiązanie sugerowane przez DE — podciągnij PL do tej jakości. DE nigdy nie nadpisuje sensu EN, mapowań, nazw ani struktury; nie kopiuj niemieckiej składni, szyku ani interpunkcji. Jeśli ton DE i głos rasy się rozjeżdżają — wygrywa głos rasy, ale zachowaj funkcję sceny widoczną w DE.
- RAG: kontekst sceny, relacji, stawki i tonu. Pomaga dobrać brzmienie; nie wnoś z niego żadnych faktów ani nazw do tekstu.
- WYTYCZNE_DLA_RAS: głos postaci (tylko przykłady, nie szablon). Priorytet: rasa > klasa > rejestr neutralny. Rasę kwestii ustal po `npc_pl` przez MAPOWANIA_NPC. Stosuj w dialogach i narracji, nie w celach, krótkich polach funkcjonalnych ani UI. U trolli głos ma być charakterystyczny, ale nie prostacki, karykaturalny ani „wieśniacki".
- PODSUMOWANIA_CHAINA: ciągłość tonu i terminologii. Nie są źródłem nazw ani treści.

═══════════════════════════════════════════════
## ODMIANA NAZW (zależna od płci z MAPOWANIA_NPC)
═══════════════════════════════════════════════
- Imię MĘSKIE → odmieniaj normalnie, zachowując rdzeń: Halazzi → Halazziego, Zul'jin → Zul'jina.
- Imię ŻEŃSKIE na spółgłoskę → NIE odmieniaj (jak „rozmawiam z Miriam"): „błogosławieństwo Akil'zon", „ofiara dla Akil'zon". Formy typu „Akil'zonowi", „z Akil'zonem" → cofnij do „Akil'zon".
- Imię ŻEŃSKIE na -a → odmieniaj normalnie: Zul'jarra → Zul'jarry, Kul'amara → Kul'amary.
- Czasowniki i przymiotniki przy postaci zgadzaj z jej płcią (Akil'zon = ona: „obdarzyła", nie „obdarzył").
- TERMIN WIELOWYRAZOWY z mapowania (np. „Świątynia Halazzi", „Strażnica Cienistej Niecki"): odmieniaj jako całość zgodnie z polską gramatyką („do Świątyni Halazzi", „przy Strażnicy Cienistej Niecki"), ale NIE odmieniaj jego wnętrza ani nie „poprawiaj" formy bazowej. (Czyli: „do Świątyni Halazzi" — TAK; „do Świątyni Halazziego" — NIE.)
- Brak mapowania → zostaw oryginał EN, nie spolszczaj.
- Wartości techniczne/sentinelowe (np. „Brak Danych") zostaw bez zmian.

═══════════════════════════════════════════════
## CZĘSTE BŁĘDY DRAFTU — POPRAW, JEŚLI WYSTĄPIĄ
═══════════════════════════════════════════════
- Błąd sensu, fleksji, rodzaju, kalka, literówka, zawyżony rejestr → popraw ZAWSZE, nawet jeśli zdanie jest „zrozumiałe".
- Zawyżony rejestr / nadmiar archaizmów → ściągnij do poziomu EN (np. „uczynić", „rzezać", „przesiadują", a także nadużyte „mej / swej / lękać się / po cóż", gdy EN jest prosty).
- Termin oddany różnie w różnych polach tej samej misji → UJEDNOLIĆ: wybierz jedną formę i zastosuj wszędzie (np. tytuł postaci w celu i w dymku muszą być identyczne).
- Angielska pisownia tam, gdzie istnieje ustalony polski termin (np. „champion" → „czempion").
- Tytuł zbyt ogólny lub zmieniający sens → przywróć obraz / grę słów z EN (np. „Breaching the Mist" = „Przedzieranie się przez mgłę", nie „rozproszenie" i nie wariant dokonany).
- Fonetyczny zapis akcentu → standardowa polszczyzna; charakter buduje leksyka i rytm, nie zapis.
- Literówki w nazwach i słowach (np. „władj" → „władaj", „Zwiędła Kóra" → „Kora").
- W gossipach/dymkach z pustym `npc_pl`: rozpoznaj mówcę każdej linii po treści, rejestrze i składzie sceny, i zastosuj zgodne formy gramatyczne. Kwestia gracza → forma męska. NIGDY nie uzupełniaj pustego `npc_pl`.
- Kalki z EN, sztuczny angielski szyk, nienaturalne redundancje → przepisz idiomatycznie.

═══════════════════════════════════════════════
## SCHEMAT (zwróć dokładnie tę strukturę)
═══════════════════════════════════════════════
Liczba i numeracja kluczy oraz puste sekcje muszą odpowiadać JSON_ŹRÓDŁOWY_EN. Brakującą w drafcie linię przetłumacz z EN wg wszystkich powyższych reguł. Wewnątrz wartości: " → \\", łamanie linii → \\n, bez surowych tabulatorów, bez trailing comma, UTF-8 z polskimi znakami, wszystkie nawiasy domknięte.
```json
{{
  "Misje_PL": {{
    "Podsumowanie_PL": {{ "Tytuł": "" }},
    "Cele_PL": {{
      "Główny": {{ "1": "" }},
      "Podrzędny": {{ "1": "" }}
    }},
    "Treść_PL": {{ "1": "" }},
    "Postęp_PL": {{ "1": "" }},
    "Zakończenie_PL": {{ "1": "" }},
    "Nagrody_PL": {{ "1": "" }}
  }},
  "Dialogi_PL": {{
    "Gossipy_Dymki_PL": [
      {{ "id": 1, "typ": "dymek", "npc_pl": "", "wypowiedzi_PL": {{ "1": "" }} }}
    ]
  }}
}}
```

═══════════════════════════════════════════════
## KONTROLA KOŃCOWA — wykonaj po cichu, NIE wypisuj jej
═══════════════════════════════════════════════
Zanim zwrócisz JSON, sprawdź po kolei i napraw, co trzeba:
1. JAKOŚĆ JĘZYKOWA: każda linia brzmi jak tekst napisany po polsku przez profesjonalnego redaktora gry; jest naturalna, idiomatyczna, rytmiczna i wolna od kalk, angielskiego szyku, sztywności oraz bezbarwności. Jeśli istnieje wyraźnie lepsza polska wersja zachowująca treść EN — zastosuj ją.
2. GŁOS I SCENA: wypowiedzi mają wiarygodny głos postaci/rasy oraz właściwy ton, tempo, napięcie i funkcję emocjonalną.
3. SENS: zachowano informacje, relacje, intencję i stopień pewności EN; niczego istotnego nie dodano ani nie pominięto; ton nie został podniesiony ponad źródło. Zgodność sprawdzaj na poziomie znaczenia, nie składni ani szyku.
4. MAPOWANIA I ODMIANA: nazwy zgodne z mapowaniem; fleksja zgodna z płcią; żeńskie imię na spółgłoskę nieodmienione; termin wielowyrazowy nieodmieniony w środku.
5. SPÓJNOŚĆ: ta sama nazwa/fraza brzmi identycznie we WSZYSTKICH polach (cele vs dymki vs treść). Tytuły postaci, nazwy miejsc i terminy lore — bez rozjazdów.
6. PŁEĆ W GOSSIPACH: w każdej linii z pustym `npc_pl` mówca rozpoznany, formy rodzajowe zgodne; kwestie gracza w formie męskiej.
7. TERMINY I TYTUŁ: brak angielskiej pisowni tam, gdzie jest polski odpowiednik; brak archaizmów ponad poziom EN; tytuł oddaje obraz lub grę słów EN.
8. TECHNICZNE: placeholdery, tagi, escape, ID, wartości techniczne nietknięte; `npc_pl` puste tam, gdzie było puste.
9. STRUKTURA: wszystkie sekcje obecne (Misje_PL, Dialogi_PL, Podsumowanie_PL, Cele_PL, Treść_PL, Postęp_PL, Zakończenie_PL, Nagrody_PL, Gossipy_Dymki_PL); Dialogi_PL NIE wewnątrz Misje_PL; liczba/kolejność/liczba linii zgodne z EN.
10. Zwróć wyłącznie czysty JSON wg schematu. Bez tej kontroli, komentarzy i markdowna.
"""


CONST_RULES_QUEST_SUMMARY = """
Jesteś redaktorem przygotowującym zwięzłe streszczenia questów ze świata Warcraft. Twoje streszczenie posłuży tłumaczom jako szybki kontekst fabularny misji — ma w kilka sekund powiedzieć, o co w niej chodzi.

Dostaniesz angielski tekst jednej misji. Na jego podstawie napisz JEDNO streszczenie po polsku. Nie dodawaj od siebie żadnych komentarzy, potwierdzeń, bloków końcowych - po prostu zwróć streszczenie według zasad niżej.

Zasady:
- Maksymalnie 125 słów. Mniej jest w porządku, jeśli misja jest prosta.
- Opieraj się WYŁĄCZNIE na dostarczonym tekście. Nie dodawaj wiedzy o świecie Warcraft spoza tekstu, nie domyślaj się, nie zmyślaj.
- Jeśli źródło nie rozstrzyga motywacji, relacji, sprawcy, przebiegu albo rezultatu, nie przedstawiaj ich jako pewnych.
- Nazwy własne (postacie, miejsca, frakcje, przedmioty) zostaw w oryginalnej, angielskiej formie.
- Pisz neutralnie, w trzeciej osobie, w czasie teraźniejszym. Nie zwracaj się do gracza.
- Jeśli tekst ma znikomą treść fabularną, streść krótko to, co jest — nie uzupełniaj braków.
- Zwróć wyłącznie treść streszczenia: bez nagłówka, cudzysłowów, znaczników i wstępu w stylu „Podsumowanie:".
- Uporządkuj treść według priorytetu: (1) sens i rezultat misji, (2) motywacje postaci, relacje, konflikt i decyzje, (3) działania gracza tylko wtedy, gdy popychają fabułę, (4) istotne postacie i miejsce.
- Uwzględnij informacje potrzebne tłumaczowi do prawidłowego zrozumienia tonu, intencji i kontekstu wypowiedzi, nawet jeśli są mniej istotne dla mechaniki rozgrywki.
- Nie przepisuj ponumerowanych celów ani nagród. Mechanikę (np. „rozpal", „zabij", „zbierz") wspomnij tylko wtedy, gdy jest niezbędna do wyjaśnienia przebiegu lub rozwiązania fabuły.
- Jeśli postacie w dialogach ujawniają osobisty lub emocjonalny wątek (konflikt, relacja, przemiana) — to jest sedno misji i musi się znaleźć w streszczeniu.
- Nie cytuj. Użyj parafrazowania po polsku, jeżeli jest to konieczne.
- Trzymaj spójną terminologię w całym streszczeniu, tzn. nie mixuj angielskich słów z polskimi. Nazwy własne trzymajmy po angielsku.
"""


prompt_translator = ChatPromptTemplate.from_messages(
    [
        ("system", CONST_RULES_TRANSLATOR),
        (
            "human",
            """
=== START: MAPOWANIA_NPC | WIĄŻĄCE ===
{tekst_npc}
=== KONIEC: MAPOWANIA_NPC | WIĄŻĄCE ===

=== START: MAPOWANIA_SŁÓW_KLUCZOWYCH | WIĄŻĄCE ===
{tekst_slowa_kluczowe}
=== KONIEC: MAPOWANIA_SŁÓW_KLUCZOWYCH | WIĄŻĄCE ===

=== START: JSON_ŹRÓDŁOWY_EN | ŹRÓDŁO PRAWDY ===
{tekst_oryginalny}
=== KONIEC: JSON_ŹRÓDŁOWY_EN | ŹRÓDŁO PRAWDY ===

=== START: TEKST_DE_POMOCNICZY | LOKALIZACJA POMOCNICZA BLIZZARDA ===
{tekst_niemiecki}
=== KONIEC: TEKST_DE_POMOCNICZY | LOKALIZACJA POMOCNICZA BLIZZARDA ===

=== START: KONTEKST_RAG | KONTEKST ŚWIATA, NIE ŹRÓDŁO TEKSTU ===
{kontekst_rag}
=== KONIEC: KONTEKST_RAG | KONTEKST ŚWIATA, NIE ŹRÓDŁO TEKSTU ===

=== START: WYTYCZNE_DLA_RAS | GŁOS POSTACI ===
{wytyczne_rasy}
=== KONIEC: WYTYCZNE_DLA_RAS | GŁOS POSTACI ===

=== START: OBSADA_I_GŁOSY | PRZYPISANIE SPEAKERÓW ===
{obsada_i_glosy}
=== KONIEC: OBSADA_I_GŁOSY | PRZYPISANIE SPEAKERÓW ===

=== START: PODSUMOWANIA_POPRZEDNICH_MISJI_W_CHAINIE | KONTEKST CIĄGŁOŚCI ===
{podsumowania_poprzednich_misji_w_chainie}
=== KONIEC: PODSUMOWANIA_POPRZEDNICH_MISJI_W_CHAINIE | KONTEKST CIĄGŁOŚCI ===
"""
        ),
    ]
)

prompt_editor = ChatPromptTemplate.from_messages(
    [
        ("system", CONST_RULES_EDITOR),
        (
            "human",
            """
=== START: JSON_ŹRÓDŁOWY_EN | ŹRÓDŁO PRAWDY ===
{tekst_oryginalny}
=== KONIEC: JSON_ŹRÓDŁOWY_EN | ŹRÓDŁO PRAWDY ===

=== START: DRAFT_JSON_PL | WERSJA DO REDAKCJI ===
{tekst_przetlumaczony}
=== KONIEC: DRAFT_JSON_PL | WERSJA DO REDAKCJI ===

=== START: TEKST_DE_POMOCNICZY | LOKALIZACJA POMOCNICZA BLIZZARDA ===
{tekst_pomocniczy}
=== KONIEC: TEKST_DE_POMOCNICZY | LOKALIZACJA POMOCNICZA BLIZZARDA ===

=== START: KONTEKST_RAG | KONTEKST ŚWIATA, NIE ŹRÓDŁO TEKSTU ===
{kontekst_rag}
=== KONIEC: KONTEKST_RAG | KONTEKST ŚWIATA, NIE ŹRÓDŁO TEKSTU ===

=== START: MAPOWANIA_NPC | WIĄŻĄCE ===
{tekst_npc}
=== KONIEC: MAPOWANIA_NPC | WIĄŻĄCE ===

=== START: MAPOWANIA_SŁÓW_KLUCZOWYCH | WIĄŻĄCE ===
{tekst_slowa_kluczowe}
=== KONIEC: MAPOWANIA_SŁÓW_KLUCZOWYCH | WIĄŻĄCE ===

=== START: WYTYCZNE_DLA_RAS | GŁOS POSTACI ===
{wytyczne_rasy}
=== KONIEC: WYTYCZNE_DLA_RAS | GŁOS POSTACI ===

=== START: PODSUMOWANIA_POPRZEDNICH_MISJI_W_CHAINIE | KONTEKST CIĄGŁOŚCI ===
{podsumowania_poprzednich_misji_w_chainie}
=== KONIEC: PODSUMOWANIA_POPRZEDNICH_MISJI_W_CHAINIE | KONTEKST CIĄGŁOŚCI ===
"""
        ),
    ]
)

def zbuduj_prompt_redaktora(
        tekst_oryginalny,
        tekst_przetlumaczony,
        tekst_pomocniczy,
        kontekst_rag,
        podsumowania_poprzednich_misji_w_chainie,
        wytyczne_rasy,
        tekst_npc,
        tekst_slowa_kluczowe,
        obsada_i_glosy
    ) -> dict[str, Any]:
    """
    Składa prompt redaktora bez wywoływania LLM. Używane przez sync editor() i batch.
    """

    wejscie = {
        "tekst_oryginalny": tekst_lub_placeholder(tekst_oryginalny, "{}"),
        "tekst_przetlumaczony": tekst_lub_placeholder(tekst_przetlumaczony, "{}"),
        "tekst_pomocniczy": tekst_lub_placeholder(tekst_pomocniczy, "- brak wersji niemieckiej dla tej misji"),
        "kontekst_rag": kontekst_rag_lub_placeholder(kontekst_rag, "- brak kontekstu dla tej misji"),
        "wytyczne_rasy": tekst_lub_placeholder(wytyczne_rasy, "- brak wytycznych dla tej/tych ras"),
        "tekst_npc": tekst_lub_placeholder(tekst_npc, "- brak mapowań NPC dla tej misji"),
        "tekst_slowa_kluczowe": tekst_lub_placeholder(tekst_slowa_kluczowe, "- brak mapowań słów kluczowych dla tej misji"),
        "obsada_i_glosy": tekst_lub_placeholder(obsada_i_glosy, "- brak danych o obsadzie dla tej misji"),
        "podsumowania_poprzednich_misji_w_chainie": tekst_lub_placeholder(
            podsumowania_poprzednich_misji_w_chainie,
            "- jest to zwykła misja nie będąca w żadnym chainie albo pierwsza misja w chainie"
        )
    }

    prompt_value = prompt_editor.invoke(wejscie)
    messages = prompt_value.to_messages()

    return {
        "system": messages[0].content,
        "user": messages[1].content,
        "prompt_txt": prompt_value.to_string(),
        "prompt_value": prompt_value,
    }


def zbuduj_prompt_tlumacza(
        tekst_oryginalny,
        tekst_niemiecki,
        kontekst_rag,
        podsumowania_poprzednich_misji_w_chainie,
        wytyczne_rasy,
        tekst_npc,
        tekst_slowa_kluczowe,
        obsada_i_glosy=None
    ) -> dict[str, Any]:
    """Składa prompt tłumacza bez wywoływania LLM. Używane przez sync i batch."""
    wejscie = {
        "tekst_oryginalny": tekst_oryginalny,
        "tekst_niemiecki": tekst_lub_placeholder(tekst_niemiecki, "- brak wersji niemieckiej dla tej misji"),
        "kontekst_rag": kontekst_rag_lub_placeholder(kontekst_rag, "- brak kontekstu dla tej misji"),
        "wytyczne_rasy": tekst_lub_placeholder(wytyczne_rasy, "- brak wytycznych dla tej/tych ras"),
        "tekst_npc": tekst_lub_placeholder(tekst_npc, "- brak mapowań NPC dla tej misji"),
        "tekst_slowa_kluczowe": tekst_lub_placeholder(tekst_slowa_kluczowe, "- brak mapowań słów kluczowych dla tej misji"),
        "obsada_i_glosy": tekst_lub_placeholder(obsada_i_glosy, "- brak danych o obsadzie dla tej misji"),
        "podsumowania_poprzednich_misji_w_chainie": tekst_lub_placeholder(
            podsumowania_poprzednich_misji_w_chainie,
            "- jest to zwykła misja nie będąca w żadnym chainie albo pierwsza misja w chainie"
        )
    }

    prompt_value = prompt_translator.invoke(wejscie)
    messages = prompt_value.to_messages()
    return {
        "system": messages[0].content,
        "user": messages[1].content,
        "prompt_txt": prompt_value.to_string(),
        "prompt_value": prompt_value,
    }

def translator(
        llm,
        tekst_oryginalny,
        tekst_niemiecki,
        kontekst_rag,
        podsumowania_poprzednich_misji_w_chainie,
        wytyczne_rasy,
        tekst_npc,
        tekst_slowa_kluczowe,
        obsada_i_glosy=None
    ) -> QuestContentResult:
    """
    Tłumaczy misję na bazie podanych parametrów.
    """

    prompt = zbuduj_prompt_tlumacza(
        tekst_oryginalny=tekst_oryginalny,
        tekst_niemiecki=tekst_niemiecki,
        kontekst_rag=kontekst_rag,
        podsumowania_poprzednich_misji_w_chainie=podsumowania_poprzednich_misji_w_chainie,
        wytyczne_rasy=wytyczne_rasy,
        tekst_npc=tekst_npc,
        tekst_slowa_kluczowe=tekst_slowa_kluczowe,
        obsada_i_glosy=obsada_i_glosy,
    )
    prompt_value = prompt["prompt_value"]
    raw_response = llm.invoke(prompt_value)

    return {
        "raw": raw_response,
        "parsed": None,
        "parsing_error": None,
        "prompt_txt": prompt["prompt_txt"],
    }


def editor(
        llm,
        tekst_oryginalny,
        tekst_przetlumaczony,
        tekst_pomocniczy,
        kontekst_rag,
        podsumowania_poprzednich_misji_w_chainie,
        wytyczne_rasy,
        tekst_npc,
        tekst_slowa_kluczowe,
        obsada_i_glosy
    ) -> QuestContentResult:
    """
    Redaguje przetłumaczoną misję na bazie podanych parametrów.
    """

    prompt = zbuduj_prompt_redaktora(
        tekst_oryginalny=tekst_oryginalny,
        tekst_przetlumaczony=tekst_przetlumaczony,
        tekst_pomocniczy=tekst_pomocniczy,
        kontekst_rag=kontekst_rag,
        wytyczne_rasy=wytyczne_rasy,
        tekst_npc=tekst_npc,
        tekst_slowa_kluczowe=tekst_slowa_kluczowe,
        obsada_i_glosy=obsada_i_glosy,
        podsumowania_poprzednich_misji_w_chainie=podsumowania_poprzednich_misji_w_chainie
    )
    prompt_value = prompt["prompt_value"]
    raw_response = llm.invoke(prompt_value)

    return {
        "raw": raw_response,
        "parsed": None,
        "parsing_error": None,
        "prompt_txt": prompt["prompt_txt"],
    }


def get_quest_summary(llm, mission: str) -> AIMessage:
    prompt_context_lore = ChatPromptTemplate.from_messages(
        [
            ("system", CONST_RULES_QUEST_SUMMARY),
            ("human", """
                TEKST MISJI:
                {misje_tekst}
            """)
        ]
    )

    chain = prompt_context_lore | llm
    result = chain.invoke({
        "misje_tekst": mission
    })

    return result
