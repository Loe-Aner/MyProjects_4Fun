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

-- ============================ CWICZENIA ============================

-- 1. Ile funduszy jest w zbiorze?
SELECT COUNT(DISTINCT nazwa)
FROM notowania

-- 2. Ktore fundusze funkcjonuja najdluzej?
SELECT
  nazwa,
  MIN(Data) AS start_notowan,
  MAX(Data) AS koniec_notowan,
  DATEDIFF('day', MIN(Data), MAX(Data)) AS ile_dni_funkcjonuje
FROM notowania
GROUP BY nazwa
ORDER BY ile_dni_funkcjonuje DESC;

-- 3. Jaka jest srednia wartosc jednostki uczestnictwa per fundusze wraz z odchyleniem standardowym?
SELECT
  nazwa,
  ROUND(AVG(Zamkniecie), 2) AS sr_wartosc,
  ROUND(STDDEV(Zamkniecie), 2) AS odch_st,
  DATEDIFF('day', MIN(Data), MAX(Data)) AS ile_dni_funkcjonuje,
  ROUND(AVG(Zamkniecie) / STDDEV(Zamkniecie), 2) AS procent
FROM notowania
GROUP BY nazwa
ORDER BY procent ASC;

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






