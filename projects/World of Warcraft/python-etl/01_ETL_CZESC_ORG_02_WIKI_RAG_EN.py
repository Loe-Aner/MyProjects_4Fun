from scraper_wiki_rag import create_mediawiki_markdown_document

# TWORZĘ DOKUMENTY POD RAG - W FOLDERZE 01_DOCUMENTS
res = create_mediawiki_markdown_document(
    page_url="https://warcraft.wiki.gg/wiki/Xal%27atath",
    base_output_dir=r"C:\____Moje-MOJE\MyProjects_4Fun\projects\World of Warcraft\rag-pliki\01_dokumenty",
    relative_output_path=r"Characters\Xalatath\doc_Xalatath_001.md",
    document_id="doc_Xalatath_001",
    source_type="document",
    document_type="article",
    subtype="character",
    name="Xalatath"
)

# ================== 2DO ==================
# STWORZYC SLOWNIK Z PARAMETRAMI JAK WYZEJ, BY FUNKCJA LATALA W PETLI
# NA PODSTAWIE DOKUMENTU TWORZONY JEST CHUNK (ODDZIELNIE W CHATGPT/INNYM AI, BEZ SKRYPTU I API NA RAZIE)
# POWIAZAC CHUNKI Z DANYM DOKUMENTEM
# HASHOWAC TRESC I ZAPISAC DO DB RESZTE LOGOW
# POTEM NA GORZE SKRYPTU SPRAWDZAC CZY TRESC SIE ZMIENILA - JEZELI TAK, TO STARY DOKUMENT + POWIAZANE CHUNKI ROBIA OUT