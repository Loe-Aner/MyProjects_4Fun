WITH employees AS (
SELECT *
FROM read_csv('abc\employees.csv')
),

emplo_ranked AS (SELECT
  employee_id, full_name, team, birth_date,
  DENSE_RANK() OVER (PARTITION BY team ORDER BY birth_date DESC) AS rnk_empl
FROM employees)

SELECT
  employee_id, full_name, team, birth_date
FROM emplo_ranked
WHERE rnk_empl = 1
ORDER BY team ASC;