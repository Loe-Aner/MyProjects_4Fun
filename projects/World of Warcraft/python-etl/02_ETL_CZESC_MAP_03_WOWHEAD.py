from typing import Any

import pandas as pd
from sqlalchemy import BigInteger, Integer, text

from moduly.db_core import utworz_engine_do_db
from moduly.sciezki import sciezka_excel_mappingi


# TUTAJ DODAJE KOLEJNOSC MISJI Z EXCELA PER FABULA


SCIEZKA = sciezka_excel_mappingi("kolejnosc_misji.xlsx")
ARKUSZ = "kolejnosc"
TABELA_STAGING = "STG_KOLEJNOSC_MISJI"

silnik = utworz_engine_do_db()

df = pd.read_excel(
    SCIEZKA,
    sheet_name=ARKUSZ,
    usecols=["MISJA_ID_Z_GRY", "KOLEJNOSC"]
).dropna(how="all")

q_drop_staging = text(f"DROP TABLE IF EXISTS dbo.{TABELA_STAGING}")
q_update_misje = text(f"""
    UPDATE m
    SET
        m.KOLEJNOSC_LINII_FABULARNEJ = s.KOLEJNOSC,
        m.DATA_UPDATE = SYSDATETIME()
    FROM dbo.MISJE AS m
    INNER JOIN dbo.{TABELA_STAGING} AS s
        ON m.MISJA_ID_Z_GRY = s.MISJA_ID_Z_GRY;
""")

typy_staging: dict[str, Any] = {
    "MISJA_ID_Z_GRY": BigInteger(),
    "KOLEJNOSC": Integer(),
}

with silnik.begin() as conn:
    conn.execute(q_drop_staging)

df.to_sql(
    name=TABELA_STAGING,
    con=silnik,
    schema="dbo",
    if_exists="replace",
    index=False,
    dtype=typy_staging,
)

with silnik.begin() as conn:
    wynik = conn.execute(q_update_misje)
    conn.execute(q_drop_staging)

print(f"UPDATE MISJE.KOLEJNOSC_LINII_FABULARNEJ: Excel={len(df)}, zaktualizowano={wynik.rowcount}")
