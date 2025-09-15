WITH employee_attendance AS (SELECT *
FROM read_csv('D:\MyProjects_4Fun\code_challenges\SQL\Employee Weekend Work Counting Unique Weekends and Total Days Worked\employee_attendance.csv')),

tbl1 AS (
  SELECT
    employee_id,
    attendance_date,
    date_trunc('week', attendance_date) AS weekend_id
  FROM employee_attendance
  WHERE date_part('year', attendance_date) = 2023
    AND date_part('dow', attendance_date) IN (0, 6)
)

SELECT
  employee_id,
  count(DISTINCT weekend_id) AS weekends_worked,
  count(*) AS total_weekend_days_worked
FROM tbl1
GROUP BY employee_id
ORDER BY weekends_worked DESC, total_weekend_days_worked DESC, employee_id DESC;



