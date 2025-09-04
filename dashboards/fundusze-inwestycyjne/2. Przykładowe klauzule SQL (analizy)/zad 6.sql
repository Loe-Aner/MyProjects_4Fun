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

-- 6. Jakie było notowanie najbliższe sprzed roku (do 20 dni wcześniej) w latach 2023–2024?
SELECT
  n1.nazwa,
  n1.DATA AS data_n,
  n1.Zamkniecie AS zamkniecie_n,
  n2.Zamkniecie AS zamkniecie_n_minus1
FROM notowania AS n1
LEFT JOIN notowania AS n2
  ON n2.DATA BETWEEN n1.DATA - INTERVAL '1 year 20 days' AND n1.DATA - INTERVAL '1 year'
 AND n1.nazwa = n2.nazwa
WHERE n1.DATA BETWEEN '2023-01-01' AND '2024-12-31'
WINDOW w AS (PARTITION BY n1.nazwa, n1.DATA ORDER BY n2.DATA DESC)
QUALIFY ROW_NUMBER() OVER w = 1;