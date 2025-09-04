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
)

-- 4. Ranking funduszy po stopie zwrotu YTD
SELECT
  uz.nazwa,
  uz.DATA AS max_date,
  ROUND((n.Zamkniecie / LAG(n.Zamkniecie) OVER w - 1) * 100, 2) AS stopa_zwrotu_YTD_perc
FROM unpivoted_zbior_ytd AS uz
INNER JOIN notowania AS n
  ON uz.DATA = n.DATA
 AND uz.nazwa = n.nazwa
WINDOW w AS (PARTITION BY uz.nazwa ORDER BY uz.Data)
QUALIFY ROW_NUMBER() OVER w > 1
 ORDER BY stopa_zwrotu_YTD_perc DESC;

/* TOP 3:

1. inPZU Akcje Rynku Zlota = 71.43%
2. Esaliens Zlota i Metali Szlachetnych = 62.41%
3. PKO Akcji Rynku Zlota = 56.8%

*/