from moduly.repo_misje import get_missing_quests_from_wowhead
from moduly.db_core import utworz_engine_do_db

silnik = utworz_engine_do_db()

misje_2do = get_missing_quests_from_wowhead(
    silnik=silnik,
    dodatek="Midnight"
)
