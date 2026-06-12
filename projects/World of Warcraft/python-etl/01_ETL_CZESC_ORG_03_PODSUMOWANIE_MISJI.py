from moduly.db_core import utworz_engine_do_db
from moduly.ai_modele import llm_quest_summary
from moduly.ai_quest_summary import generate_and_save_quest_summary

silnik = utworz_engine_do_db()
llm = llm_quest_summary()


# GENERUJE PODSUMOWANIE MISJI I NASTEPNIE ZAPISUJE DO DBO.MISJE_PODSUMOWANIA ORAZ AI_LOGI
generate_and_save_quest_summary(
    silnik=silnik,
    llm=llm,
    
    # ZMIENIC NONE NA KONKRETNA NAZWE W PRZYPADKU POTRZEB
    kraina=None,
    fabula="Ripple Effects",
    dodatek=None,
    id_misji=None
)