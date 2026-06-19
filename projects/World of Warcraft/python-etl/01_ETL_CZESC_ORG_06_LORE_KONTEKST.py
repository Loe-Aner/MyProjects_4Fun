from moduly.ai_lore_kontekst import buduj_kontekst_lore

# PREKOMPUTUJE KONTEKST LORE (RAG) DLA MISJI — niezależnie od tłumaczenia.
# Dla wybranych misji: generuje pytania (-> MISJE_LORE_PYTANIA), robi Qdrant + rerank
# (-> MISJE_LORE_TRAFIENIA, ślad bez treści) i zapisuje podsumowanie (-> MISJE_LORE_KONTEKST).
# Bierze tylko misje, które jeszcze nie mają kontekstu.
#
# Filtrowanie (co najmniej jeden parametr; reszta domyślnie None):
#   buduj_kontekst_lore(dodatek="Midnight")
#   buduj_kontekst_lore(fabula="Dawn of Reckoning")
#   buduj_kontekst_lore(dodatek="Midnight", fabula="Dawn of Reckoning")
#   buduj_kontekst_lore(id_misji=1234)

buduj_kontekst_lore(fabula="The Light's Summons")
