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
    # {"category": "Category:Worlds", "subtype": "Worlds", "excluded": ["film universe"], "min_body_words": 150},
    # {"category": "Category:Domanaar_characters", "subtype": "characters", "excluded": [], "min_body_words": 250},
    # {"category": "Category:Haranir_characters", "subtype": "characters", "excluded": [], "min_body_words": 250},
    # {"category": "Category:Old_Gods", "subtype": "old_gods", "excluded": [], "min_body_words": 150},
    # {"category": "Category:Religions", "subtype": "religions", "excluded": ["alternate universe"], "min_body_words": 250},
    # {"category": "Category:Forest_troll_territories", "subtype": "forest_troll_territories", "excluded": [], "min_body_words": 200},
    # {"category": "Category:Forest_troll_characters", "subtype": "characters", "excluded": ["Amani", "(tactics)", "Amani'shi", "Disciple", "Classic", "Gurubashi", "(beta)", "Smolderthorn", "Shadowpine", "Shadowglen", "Revantusk", "Mossflayer"], "min_body_words": 250},
    # {"category": "Category:Loa", "subtype": "loa", "excluded": ["tactics", "group"], "min_body_words": 250},
    # {"category": "Category:Forest_troll_organizations", "subtype": "organizations", "excluded": [], "min_body_words": 150},
    # {"category": "Category:Zul'Aman_subzones", "subtype": "subzones", "excluded": [], "min_body_words": 150},
    # {"category": "Category:Twilight's_Blade", "subtype": "characters", "excluded": [], "min_body_words": 250},
    # {"category": "Category:A_Thousand_Years_of_War_characters", "subtype": "characters", "excluded": [], "min_body_words": 250},
    # {"category": "Category:Aberrations", "subtype": "aberrations", "excluded": [], "min_body_words": 150},
    # {"category": "Category:Abominations", "subtype": "abominations", "excluded": [], "min_body_words": 250},
    # {"category": "Category:Abyssal_Depths", "subtype": "abbysal_depths", "excluded": [], "min_body_words": 250},
    # {"category": "Category:Abyssal_Depths_subzones", "subtype": "abbysal_depths", "excluded": [], "min_body_words": 100},
    # {"category": "Category:Ahn'Qiraj: The Fallen Kingdom", "subtype": "ahn_qiraj", "excluded": [], "min_body_words": 150},
    # {"category": "Category:Air_elementals", "subtype": "air_elementals", "excluded": [], "min_body_words": 150},
    # {"category": "Category:Air_revenants", "subtype": "air_revenants", "excluded": [], "min_body_words": 200},  
    # {"category": "Category:Airstrips", "subtype": "airstrips", "excluded": [], "min_body_words": 200},   
    # {"category": "Category:Alchemists", "subtype": "alchemists", "excluded": ["warcraft"], "min_body_words": 200},  
    # {"category": "Category:Aldor", "subtype": "aldor", "excluded": ["Comparison"], "min_body_words": 250},  
    # {"category": "Category:Alliance", "subtype": "alliance", "excluded": [], "min_body_words": 200}, 
    # {"category": "Category:Light", "subtype": "light", "excluded": [], "min_body_words": 200}, 
    # {"category": "Category:Alliance_air_force", "subtype": "alliance", "excluded": [], "min_body_words": 250}, 
    # {"category": "Category:Alliance_army", "subtype": "alliance", "excluded": [], "min_body_words": 250}, 
    # {"category": "Category:Alliance_factions", "subtype": "alliance", "excluded": ["alternate", "faction", "Classic"], "min_body_words": 250}, 
    # {"category": "Category:Alterac_Mountains", "subtype": "alterac", "excluded": ["film", "Classic"], "min_body_words": 250}, 
    # {"category": "Category:Ogre_organizations", "subtype": "ogres", "excluded": ["alternate", "Classic"], "min_body_words": 250}, 
    # {"category": "Category:Cities", "subtype": "cities", "excluded": ["alternate", "Classic", "Warcraft"], "min_body_words": 350}, 
    # {"category": "Category:Demon_hunter_characters", "subtype": "characters", "excluded": ["alternate", "Classic", "Warcraft"], "min_body_words": 350}, 
    {"category": "Category:Races", "subtype": "races", "excluded": ["alternate", "Classic", "Warcraft"], "min_body_words": 350}, 
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