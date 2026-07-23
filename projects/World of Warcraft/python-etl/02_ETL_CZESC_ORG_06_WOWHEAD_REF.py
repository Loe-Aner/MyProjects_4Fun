from scraper_wowhead_misje import buduj_referencje_dodatku

# BUDUJE NIEMIECKĄ REFERENCJĘ (4_REFERENCJA) DLA WYBRANYCH MISJI.
# Bierze tylko misje istniejące w dbo.MISJE, które NIE mają jeszcze referencji,
# scrapuje je z Wowheada DE i wstawia do dbo.MISJE_STATUSY. Pierwszeństwo ma wiki - jak tam jest zmiana, to 4_REFERENCJA też robi out.
#
# Filtrować można na trzy sposoby:
#   buduj_referencje_dodatku("Midnight")                            # sam dodatek
#   buduj_referencje_dodatku("Midnight", "Dawn of Reckoning")       # dodatek + linia fabularna (EN)
#   buduj_referencje_dodatku(linia_fabularna="Dawn of Reckoning")   # sama linia fabularna (EN)

buduj_referencje_dodatku(dodatek="Midnight")