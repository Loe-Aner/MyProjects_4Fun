from sqlalchemy import text
from moduly.sciezki import sciezka_sql_tabele

LISTA_PLIKOW = [
    sciezka_sql_tabele("1_tabela_NPC.sql"),
    sciezka_sql_tabele("2_tabela_misje.sql"),
    sciezka_sql_tabele("3_tabela_zrodlo.sql"),
    sciezka_sql_tabele("4_tabela_NPC_statusy.sql"),
    sciezka_sql_tabele("5_tabela_misje_statusy.sql"),
    sciezka_sql_tabele("6_tabela_dialogi.sql"),
    sciezka_sql_tabele("7_tabela_linki_do_scrapowania.sql"),
    sciezka_sql_tabele("8_tabela_slowa_kluczowe.sql"),
    sciezka_sql_tabele("9_tabela_misje_slowa_kluczowe.sql"),
    sciezka_sql_tabele("10_tabela_misje_zmiany_wiki.sql"),
    sciezka_sql_tabele("11_archiwum_misje_dialogi.sql"),
    sciezka_sql_tabele("12_misje_wskazniki.sql"),
    sciezka_sql_tabele("13_ai_logi.sql"),
    sciezka_sql_tabele("14_rag_logi.sql"),
    sciezka_sql_tabele("15_qdrant_logi.sql")
]

def podziel_komendy_sql(tresc: str):
    batch: list[str] = []
    for linia in tresc.splitlines():
        if linia.strip().upper() == "GO":
            for komenda in "\n".join(batch).split(";"):
                komenda = komenda.strip()
                if komenda:
                    yield komenda
            batch = []
        else:
            batch.append(linia)

    for komenda in "\n".join(batch).split(";"):
        komenda = komenda.strip()
        if komenda:
            yield komenda


def czerwony_przycisk(
        silnik
    ):
    q = text("""
        DROP TABLE IF EXISTS dbo.AI_LOGI;
        DROP TABLE IF EXISTS dbo.MISJE_WSKAZNIKI_ZGODNOSCI;
        DROP TABLE IF EXISTS dbo.ZRODLO_QDRANT;
        DROP TABLE IF EXISTS dbo.ZRODLO_RAG;
        DROP TABLE IF EXISTS dbo.ARCHIWUM_MISJE_DIALOGI;
        
        DROP TABLE IF EXISTS dbo.MISJE_SLOWA_KLUCZOWE;
        DROP TABLE IF EXISTS dbo.MISJE_SLOWA;
        
        DROP TABLE IF EXISTS dbo.DIALOGI_STATUSY;
        DROP TABLE IF EXISTS dbo.MISJE_STATUSY;
        DROP TABLE IF EXISTS dbo.NPC_STATUSY;
        DROP TABLE IF EXISTS dbo.ZRODLO_MISJE;
        
        DROP TABLE IF EXISTS dbo.MISJE;
        
        DROP TABLE IF EXISTS dbo.NPC;
        DROP TABLE IF EXISTS dbo.SLOWA_KLUCZOWE;
        DROP TABLE IF EXISTS dbo.LINKI_DO_SCRAPOWANIA;
""")
    
    with silnik.begin() as conn:
        conn.execute(q)
        print("Baza danych... już nie istnieje. Zadowolony jesteś z siebie?")

def zielony_przycisk(silnik, lista = LISTA_PLIKOW):
    with silnik.connect() as conn:
        for sciezka in lista:
            with open(sciezka, "r", encoding="cp1250") as f:
                tresc = f.read()
            for k in podziel_komendy_sql(tresc):
                conn.execute(text(k))
            
            conn.commit()
            print(f"Postawiono tabelę w: {sciezka}")
