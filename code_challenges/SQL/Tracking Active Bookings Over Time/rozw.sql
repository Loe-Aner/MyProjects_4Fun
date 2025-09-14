WITH course_bookings AS (
  SELECT *
  FROM read_csv('abc\sample.csv')
),

dts AS (
SELECT DISTINCT booking_date
FROM course_bookings
)

SELECT
  d.booking_date,
  COUNT(*) AS active_bookings
FROM dts AS d
JOIN course_bookings AS b
  ON b.booking_date <= d.booking_date
 AND b.course_start_date >= d.booking_date
GROUP BY d.booking_date
ORDER BY d.booking_date;

