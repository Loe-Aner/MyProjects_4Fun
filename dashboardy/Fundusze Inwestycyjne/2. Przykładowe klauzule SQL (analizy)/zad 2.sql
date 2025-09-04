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

-- 2. Ktore fundusze funkcjonuja najdluzej?
SELECT
  nazwa,
  MIN(Data) AS start_notowan,
  MAX(Data) AS koniec_notowan,
  age(MAX(Data), MIN(Data)) AS ile_lat_miesiecy
FROM notowania
GROUP BY nazwa
ORDER BY MAX(Data) - MIN(Data) DESC;

/* ODPOWIEDZ:
Z racji, że jest 48 funduszy, wymienię top 3:
  1. Pekao Stabilnego Wzrostu - od 1996-09-18 ----> 28 lat i 11 miesiecy
  2. Goldman Sachs Parasol FIO Akcji - od 1998-03-11 ----> 27 lat i 5 miesiecy
  3. Goldman Sachs Parasol FIO Zrownowazony - od 1998-11-03 ----> 26 lat i 9 miesiecy
*/