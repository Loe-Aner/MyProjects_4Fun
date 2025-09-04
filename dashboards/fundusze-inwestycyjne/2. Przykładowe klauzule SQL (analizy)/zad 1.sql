-- ============================ WIRTUALNE TABELE ============================

WITH notowania_base AS (
  SELECT *
  FROM read_parquet('abc\notowania.parquet')
),

extra_info AS (
  SELECT *
  FROM read_parquet('abc\extra_info.parquet')
),

notowania AS (
  SELECT
    ei.nazwa,
    ei.kategoria,
    ei.firma,
    CAST(nb.DATA AS DATE) AS Data,
    CAST(REPLACE(nb.Zamkniecie, ',', '.') AS NUMERIC) AS Zamkniecie
  FROM notowania_base AS nb
  INNER JOIN extra_info AS ei
    ON nb.Nazwa_Funduszu = ei.nazwa
)

-- 1. Ile funduszy jest w zbiorze?
SELECT COUNT(DISTINCT nazwa)
FROM notowania

-- ODPOWIEDZ: W zbiorze jest 48 funduszy.