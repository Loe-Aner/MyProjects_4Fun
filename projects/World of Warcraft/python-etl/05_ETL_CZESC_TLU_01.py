from moduly.ai import misje_dialogi_przetlumacz_zapisz
from moduly.db_core import utworz_engine_do_db
from moduly.repo_misje import ujednolic_tytuly_misji

silnik = utworz_engine_do_db()

# TŁUMACZY ZAPISUJĄC DO BAZY DANYCH Z ODPOWIEDNIMI STATUSAMI
# MOŻNA PODAĆ DOWOLNIE KTORY PARAMETR
# BIERZE POD UWAGE TYLKO MISJE Z TRESCIA
misje_dialogi_przetlumacz_zapisz(
    silnik, 
    fabula="The Light's Summons",
    liczba_watkow=8,
    printing=False
    )

# KOREKTA MISJI - JEŻELI NP. DWIE MISJE O ID 37, 38 MAJĄ TEN SAM TYTUŁ PO ENG, ALE INNY PO PL, TO WYBIERAM PIERWSZY TYTUŁ
ujednolic_tytuly_misji(silnik)
