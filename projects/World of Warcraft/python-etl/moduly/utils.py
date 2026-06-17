from sqlalchemy import text
import pandas as pd
from urllib.parse import unquote, urlparse
import base64
import json
import re
import zlib

from json_repair import repair_json


def strip_json_fence(text: str) -> str:
    text = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    return fenced.group(1).strip() if fenced else text


def parse_json_with_repair(text: str) -> dict:
    cleaned = strip_json_fence(text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = repair_json(cleaned, return_objects=True)

    if not isinstance(parsed, dict):
        raise ValueError("Odpowiedź JSON nie jest obiektem głównym.")
    return parsed

def generuj_hash_djb2(tekst):

    tekst = str(tekst)
    
    if not tekst:
        return None
    
    tekst = tekst.lower()

    hash_val = 5381
    hash_val_2 = 0
    
    for znak in tekst:
        kod_znaku = ord(znak)
        
        hash_val = (hash_val * 33 + kod_znaku) & 0xFFFFFFFF
        hash_val_2 = (hash_val_2 * 65599 + kod_znaku) & 0xFFFFFFFF
        
    return f"{hash_val:08x}{hash_val_2:08x}"

def hash_do_wsad_json(zakodowany_string: str, jezyk: str = "EN") -> str:
    if not zakodowany_string:
        return "{}"

    import base64
    import json
    import zlib

    from moduly.services_persist_wynik import przefiltruj_dane_misji
    from scraper_wiki_main import parsuj_misje_z_url

    skompresowane_bajty = base64.b64decode(zakodowany_string)
    tekst_html = zlib.decompress(skompresowane_bajty).decode("utf-8")
    surowe_dane = parsuj_misje_z_url(url=None, html_content=tekst_html)
    przetworzone_dane = przefiltruj_dane_misji(dane_wejsciowe=surowe_dane, jezyk=jezyk)

    return json.dumps(przetworzone_dane, indent=4, ensure_ascii=False)


def skompresuj_tekst(tekst: str | None) -> str | None:
    """Kompresja odwracalna (zlib + base64), jak HTML_SKOMPRESOWANY w dbo.ZRODLO."""
    if not tekst:
        return None
    skompresowane_bajty = zlib.compress(tekst.encode("utf-8"))
    return base64.b64encode(skompresowane_bajty).decode("utf-8")


def odkoduj_tekst(zakodowany_string: str | None) -> str | None:
    """Odwrotność skompresuj_tekst: base64 -> zlib -> czysty string."""
    if not zakodowany_string:
        return None
    skompresowane_bajty = base64.b64decode(zakodowany_string)
    return zlib.decompress(skompresowane_bajty).decode("utf-8")


def formatuj_podsumowania_poprzednich_misji(wiersze, kolejnosc_biezacej=None, limit=5) -> str:
    if not wiersze:
        return ""

    posortowane_wiersze = sorted(wiersze, key=lambda x: x[0])
    if limit is not None:
        posortowane_wiersze = posortowane_wiersze[-limit:]

    podsumowania = {
        str(numer_misji): podsumowanie
        for numer_misji, podsumowanie in posortowane_wiersze
    }
    blok = json.dumps(podsumowania, indent=4, ensure_ascii=False)
    limit_txt = limit if limit is not None else "wszystkie"

    if kolejnosc_biezacej is not None:
        naglowek = (
            f"Aktualnie tłumaczysz misję nr {kolejnosc_biezacej} w tym łańcuchu fabularnym.\n"
            f"Poniżej streszczenia ostatnich maksymalnie {limit_txt} WCZEŚNIEJSZYCH misji z tego łańcucha "
            "(klucz = numer misji w łańcuchu). Służą wyłącznie jako kontekst ciągłości - "
            "nie tłumacz ich i nie przenoś ich treści do wyniku."
        )
        return f"{naglowek}\n\n{blok}"

    return blok


def formatuj_referencje_de(wiersze) -> str:
    if not wiersze:
        return ""

    segmenty: dict[str, list[tuple[int, str]]] = {}
    for segment, nr, tresc in wiersze:
        tresc = (tresc or "").strip()
        if not tresc:
            continue

        segmenty.setdefault(segment, []).append((nr or 1, tresc))

    kolejnosc_segmentow = ["TREŚĆ", "POSTĘP", "ZAKOŃCZENIE"]
    bloki = []
    for segment in kolejnosc_segmentow:
        linie = segmenty.get(segment)
        if not linie:
            continue

        tekst_linii = "\n".join(
            f"{nr}. {tresc}"
            for nr, tresc in sorted(linie, key=lambda x: x[0])
        )
        bloki.append(f"[{segment}]\n{tekst_linii}")

    return "\n\n".join(bloki)


def formatuj_obsada(wiersze) -> str:
    if not wiersze:
        return ""

    etykiety = {
        "START": "Questgiver (Treść, Postęp)",
        "KONIEC": "Kończący misję (Zakończenie)",
        "DIALOG": "Dialogi / dymki",
    }
    grupy: dict[str, list[str]] = {"START": [], "KONIEC": [], "DIALOG": []}
    for rola, _kolejnosc, nazwa_en, rasa in wiersze:
        nazwa = (nazwa_en or "Brak Danych").strip() or "Brak Danych"
        rasa_txt = (rasa or "Unknown").strip() or "Unknown"
        grupy.setdefault(rola, grupy["DIALOG"]).append(f"{nazwa} ({rasa_txt})")

    linie = []
    for rola in ("START", "KONIEC", "DIALOG"):
        pozycje = grupy[rola]
        if not pozycje:
            continue

        unikalne = list(dict.fromkeys(pozycje))
        linie.append(f"- {etykiety[rola]}: {', '.join(unikalne)}")

    return "\n".join(linie)


def formatuj_slowa_kluczowe(wiersze) -> str:
    if not wiersze:
        return ""

    linie = []
    for slowo_en, slowo_pl in sorted(wiersze, key=lambda x: (x[0] or "", x[1] or "")):
        slowo_en = (slowo_en or "").strip()
        slowo_pl = (slowo_pl or "").strip()

        if not slowo_en or not slowo_pl:
            continue
        if slowo_en == slowo_pl:
            continue

        linie.append(f"- {slowo_en}: {slowo_pl}")

    return "\n".join(linie)


def formatuj_style_ras(style_map: dict, rasy, etap: str) -> str:
    if not rasy:
        return ""

    bloki = []
    for rasa in sorted(rasy):
        styl = style_map.get(rasa)
        if styl is None:
            bloki.append(f"rasa: {rasa}\nwytyczne:\nBrak wytycznych dla tej rasy")
            continue

        sekcje = [
            f"rasa: {getattr(styl, 'race_name', rasa)}",
            f"etykieta: {getattr(styl, 'label', '')}",
            f"głos: {getattr(styl, 'voice', '')}",
            f"rytm_i_składnia: {getattr(styl, 'syntax_rhythm', '')}",
            f"leksyka: {getattr(styl, 'lexicon', '')}",
            f"unikaj: {getattr(styl, 'avoid', '')}",
            f"esencja: {getattr(styl, 'essence', '')}",
        ]

        if etap == "tlumacz":
            sekcje.append(_formatuj_przyklady_tlumacza(getattr(styl, "translator_examples", [])))
        elif etap == "redaktor":
            sekcje.append(_formatuj_przyklady_redaktora(getattr(styl, "editor_examples", [])))
        else:
            raise ValueError(f"Nieznany etap formatowania stylu rasy: {etap}")

        bloki.append("\n".join(sekcja for sekcja in sekcje if sekcja))

    return "\n\n".join(bloki)


def _formatuj_przyklady_tlumacza(przyklady) -> str:
    if not przyklady:
        return "przykłady_tłumacza: brak"

    bloki = ["przykłady_tłumacza:"]
    for i, przyklad in enumerate(przyklady, start=1):
        bloki.append(
            "\n".join(
                [
                    f"{i}. kontekst: {getattr(przyklad, 'context', '')}",
                    f"   en: {getattr(przyklad, 'en', '')}",
                    f"   good: {getattr(przyklad, 'good', '')}",
                    f"   bad: {getattr(przyklad, 'bad', '')}",
                    f"   note: {getattr(przyklad, 'note', '')}",
                ]
            )
        )

    return "\n".join(bloki)


def _formatuj_przyklady_redaktora(przyklady) -> str:
    if not przyklady:
        return "przykłady_redaktora: brak"

    bloki = ["przykłady_redaktora:"]
    for i, przyklad in enumerate(przyklady, start=1):
        zmiany = getattr(przyklad, "zmiany", [])
        tekst_zmian = "\n".join(
            f"   - {getattr(zmiana, 'tag', '')}: {getattr(zmiana, 'change', '')} Powód: {getattr(zmiana, 'reason', '')}"
            for zmiana in zmiany
        )
        if not tekst_zmian:
            tekst_zmian = "   - brak opisanych zmian"

        bloki.append(
            "\n".join(
                [
                    f"{i}. kontekst: {getattr(przyklad, 'context', '')}",
                    f"   en: {getattr(przyklad, 'en', '')}",
                    f"   robocze: {getattr(przyklad, 'robocze', '')}",
                    f"   po_redakcji_good: {getattr(przyklad, 'po_redakcji_good', '')}",
                    f"   po_redakcji_bad: {getattr(przyklad, 'po_redakcji_bad', '')}",
                    "   zmiany:",
                    tekst_zmian,
                ]
            )
        )

    return "\n".join(bloki)

# if __name__ == "__main__":
#     przyklady = [
#         ("Apocalyptic threats have taken many forms in Azeroth's history, but today we face Xal'atath and her Twilight's Blade.", "6b7431ab582fdb80")
#     ]

#     print("\n" + "=" * 50)
#     print(f"{'HASH Z LUA':<18} | {'HASH Z PYTHONA':<18} | {'WYNIK'}")
#     print("=" * 50)

#     for tekst, hash_lua in przyklady:
#         hash_python = generuj_hash_djb2(tekst)
        
#         if hash_python == hash_lua:
#             czy_zgodne = "OK"
#         else:
#             czy_zgodne = "BŁĄD"
            
#         print(f"{hash_lua:<18} | {hash_python:<18} | {czy_zgodne}")

#     print("=" * 50 + "\n")

def sklej_warunki_w_WHERE(
    kraina: str | None = None, 
    fabula: str | None = None, 
    dodatek: str | None = None,
    id_misji: int | None = None
):
    if id_misji is not None:
        return "AND m.MISJA_ID_MOJE_PK = :id_misji"

    czesci_warunku = []
    
    if kraina is not None:
        czesci_warunku.append("AND m.KRAINA_EN = :kraina_en")
        
    if fabula is not None:
        czesci_warunku.append("AND m.NAZWA_LINII_FABULARNEJ_EN = :fabula_en")

    if dodatek is not None:
        czesci_warunku.append("AND m.DODATEK_EN = :dodatek_en")
    
    if czesci_warunku:
        return "\n        ".join(czesci_warunku)

    raise ValueError("Nie podano żadnych parametrów filtrowania (ID, Kraina, Fabuła lub Dodatek).")

def usun_stare_daty_pokaz_zmiany(silnik):
    """
    Zostawia tylko dwie najnowsze daty.
    Pokazuje dataframe ze zmianami, tzn. w której grupie zostały dodane/usunięte misje.
    """
    q_delete_stare = text("""
    WITH UNIKALNE_DATY AS (
        SELECT DISTINCT
            DATA_STATUS
        FROM dbo.MISJE_ZMIANY_WIKI
    ),

    RANKING_DAT AS (
        SELECT
            DATA_STATUS,
            ROW_NUMBER() OVER (ORDER BY DATA_STATUS DESC) AS RNK
        FROM UNIKALNE_DATY
    ),

    DO_WYRZUCENIA AS (
        SELECT
            DATA_STATUS
        FROM RANKING_DAT
        WHERE RNK >= 3
    )

    DELETE FROM dbo.MISJE_ZMIANY_WIKI
    WHERE DATA_STATUS IN (
        SELECT DATA_STATUS
        FROM DO_WYRZUCENIA
    );
    """)

    q_select_roznice = text("""
    WITH UNIKALNE_DATY AS (
        SELECT DISTINCT
            DATA_STATUS
        FROM dbo.MISJE_ZMIANY_WIKI
    ),

    RANKING_DAT AS (
        SELECT
            DATA_STATUS,
            ROW_NUMBER() OVER (ORDER BY DATA_STATUS DESC) AS RNK
        FROM UNIKALNE_DATY
    ),

    DANE AS (
        SELECT
            MZW.ZAKRES,
            MZW.LICZBA_MISJI,
            MZW.DATA_STATUS,
            RD.RNK
        FROM dbo.MISJE_ZMIANY_WIKI AS MZW
        INNER JOIN RANKING_DAT AS RD
            ON MZW.DATA_STATUS = RD.DATA_STATUS
        WHERE RD.RNK IN (1, 2)
    ),

    WYNIK AS (
        SELECT
            ZAKRES,
            MAX(CASE WHEN RNK = 2 THEN DATA_STATUS END) AS DATA_POPRZEDNIA,
            MAX(CASE WHEN RNK = 1 THEN DATA_STATUS END) AS DATA_NAJNOWSZA,
            MAX(CASE WHEN RNK = 2 THEN LICZBA_MISJI END) AS LICZBA_MISJI_POPRZEDNIA,
            MAX(CASE WHEN RNK = 1 THEN LICZBA_MISJI END) AS LICZBA_MISJI_NAJNOWSZA,
            MAX(CASE WHEN RNK = 1 THEN LICZBA_MISJI END)
                - MAX(CASE WHEN RNK = 2 THEN LICZBA_MISJI END) AS ROZNICA
        FROM DANE
        GROUP BY ZAKRES
    )

    SELECT
        ZAKRES,
        DATA_POPRZEDNIA,
        DATA_NAJNOWSZA,
        LICZBA_MISJI_POPRZEDNIA,
        LICZBA_MISJI_NAJNOWSZA,
        ROZNICA
    FROM WYNIK
    WHERE ROZNICA <> 0
    ORDER BY ZAKRES;
    """)

    try:
        with silnik.begin() as conn:
            conn.execute(q_delete_stare)
            wynik = pd.read_sql_query(q_select_roznice, conn)
        return wynik

    except Exception as e:
        print(f"--- Błąd podczas odczytywania danych: {e}")
        return pd.DataFrame()

def extract_wiki_name(page_url: str) -> str:
    path = urlparse(page_url).path
    return unquote(path.split("/wiki/", 1)[1])
