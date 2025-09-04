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

-- 3. Jaka jest srednia wartosc jednostki uczestnictwa per fundusze wraz z odchyleniem standardowym?
SELECT
  nazwa,
  ROUND(AVG(Zamkniecie), 2) AS sr_wartosc,
  ROUND(STDDEV(Zamkniecie), 2) AS odch_st,
  DATEDIFF('day', MIN(Data), MAX(Data)) AS ile_dni_funkcjonuje,
  ROUND(AVG(Zamkniecie) / STDDEV(Zamkniecie), 2) AS procent
FROM notowania
GROUP BY nazwa
ORDER BY procent DESC;

/* TOP 3 pod kątem oplacalnosci do ryzyka (czyli posortowano malejaco po procencie powyzej):
 
1. PKO Obligacji Zielonej Transformacji, sr_wartosc = 97.16, odch = 5.91, procent = 16.45
	
2. inPZU Akcje Sektora Technologii Kosmicznych, sr_wartosc = 124.02, odch = 12.31, procent = 10.07
		   
3. inPZU Goldman Sachs ActiveBetaR Akcje Rynków Wschodzących, sr_wartosc = 96.7, odch = 10.78, procent = 8.97
*/