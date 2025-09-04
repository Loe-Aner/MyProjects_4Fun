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
),

zbior_min_max_ytd AS (
  SELECT 
    nazwa,
    MIN(DATA) FILTER (WHERE DATA >= '2025-01-01') AS MinDate,
    MAX(DATA) FILTER (WHERE DATA <= '2025-12-31') AS MaxDate
  FROM Notowania
  GROUP BY nazwa
),

unpivoted_zbior_ytd AS (
  SELECT
    nazwa, MinDate AS Data
  FROM zbior_min_max_ytd
  UNION ALL
  SELECT
    nazwa, MaxDate
  FROM zbior_min_max_ytd AS Data
  ORDER BY nazwa
),

zbior_min_max_3y AS (
  SELECT 
    nazwa,
    MAX(DATA) FILTER (WHERE DATA <= '2024-12-31') AS MaxDate24,
    MIN(DATA) FILTER (WHERE DATA >= '2022-01-01') AS MinDate22
  FROM Notowania
  GROUP BY nazwa
),

unpivoted_zbior_3y AS (
  SELECT
    nazwa, MaxDate24 AS Data
  FROM zbior_min_max_3y AS DATA
  UNION ALL
  SELECT
    nazwa, MinDate22 AS Data
  FROM zbior_min_max_3y
  ORDER BY nazwa
)

-- 5. Ranking funduszy po średniej rocznej stopie zwrotu z ostatnich 3 pelnych lat (CAGR)
SELECT
  uz.nazwa,
  (ROUND(POWER(n.Zamkniecie / LAG(n.Zamkniecie) OVER w, 1.0/3), 3) - 1) * 100 AS CAGR_3y_perc
FROM unpivoted_zbior_3y AS uz
INNER JOIN notowania AS n
  ON uz.DATA = n.DATA
 AND uz.nazwa = n.nazwa
WINDOW w AS (PARTITION BY uz.nazwa ORDER BY uz.DATA)
QUALIFY ROW_NUMBER() OVER w > 1
ORDER BY CAGR_3y_perc DESC;


/* ODPOWIEDZ TOP3:

1. Goldman Sachs Japonia = 19.5%
2. inPZU Akcje Sektora Informatycznego = 14.3%
3. inPZU Akcje Sektora Cyberbezpieczenstwa = 11%

 */




