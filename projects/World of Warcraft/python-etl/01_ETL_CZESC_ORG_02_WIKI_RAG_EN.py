from scraper_wiki_rag import create_mediawiki_markdown_document
from moduly.db_core import utworz_engine_do_db

silnik = utworz_engine_do_db()

# TWORZĘ DOKUMENTY POD RAG - W FOLDERZE 01_DOCUMENTS
# W PRZYPADKU GDY TRESC SIE ZMIENILA (PO HASHASH) STARE DOKUMENTY SA ARCHIWIZOWANE
res = create_mediawiki_markdown_document(
    silnik=silnik,
    page_url="https://warcraft.wiki.gg/wiki/Alleria_Windrunner",
    base_output_dir=r"C:\____Moje-MOJE\MyProjects_4Fun\projects\World of Warcraft\rag-pliki\01_dokumenty",
    arch_update_dir=r"C:\____Moje-MOJE\MyProjects_4Fun\projects\World of Warcraft\rag-pliki\00_arch",
    relative_output_path=r"Characters\Alleria_Windrunner\doc_Alleria_Windrunner_001.md",
    document_id="doc_Alleria_Windrunner_001",
    source_type="document",
    document_type="article",
    subtype="character",
    name="AlleriaWindrunner"
)

# ================== 2DO ==================
# STWORZYC SLOWNIK Z PARAMETRAMI JAK WYZEJ, BY FUNKCJA LATALA W PETLI