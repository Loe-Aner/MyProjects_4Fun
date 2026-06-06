from pathlib import Path

from scraper_wiki_rag import create_mediawiki_markdown_documents_from_category
from moduly.db_core import utworz_engine_do_db


silnik = utworz_engine_do_db()

base_output_dir = Path(r"C:\____Moje-MOJE\MyProjects_4Fun\projects\World of Warcraft\rag-pliki\01_dokumenty")
arch_update_dir = Path(r"C:\____Moje-MOJE\MyProjects_4Fun\projects\World of Warcraft\rag-pliki\00_arch")
chunks_output_dir = Path(r"C:\____Moje-MOJE\MyProjects_4Fun\projects\World of Warcraft\rag-pliki\02_chunki")

rag_categories = [
    # {"category": "Category:7th Legion", "subtype": "faction", "excluded": ["7th Legion", "SI:7"], "min_body_words": 30},
    # {"category": "Category:A Brewing Storm", "subtype": "scenarios", "excluded": [""], "min_body_words": 30},
    # {"category": "Category:A Gilnean's Dream", "subtype": "scenarios", "excluded": [""], "min_body_words": 30},
    # {"category": "Category:A Good War characters", "subtype": "characters", "excluded": [""], "min_body_words": 30},
    # {"category": "Category:Void ethereals", "subtype": "etherals", "excluded": ["Shadowguard", "Ethereal", "Unbound", "Untethered", "Netherguard", "Nascent"], "min_body_words": 100},
    {"category": "Category:Worlds", "subtype": "Worlds", "excluded": ["film universe"], "min_body_words": 150},
]


# TWORZĘ DOKUMENTY POD RAG - W FOLDERZE 01_dokumenty
# JAK TWORZY NOWY FOLDER, JEST ON TEZ TWORZONY W 02_chunks
# W PRZYPADKU GDY TRESC SIE ZMIENILA (WG HASHY) STARE DOKUMENTY SA ARCHIWIZOWANE
rag_results = []

for item in rag_categories:
    rag_results.extend(
        create_mediawiki_markdown_documents_from_category(
            silnik=silnik,
            category=item["category"],
            subtype=item["subtype"],
            base_output_dir=base_output_dir,
            arch_update_dir=arch_update_dir,
            chunks_output_dir=chunks_output_dir,
            excluded=item.get("excluded"),
            min_body_words=item.get("min_body_words"),
        )
    )