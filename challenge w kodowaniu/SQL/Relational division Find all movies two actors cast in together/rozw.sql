WITH actor AS (
SELECT *
FROM read_csv('abc\actor.csv')
),

film AS (
SELECT *
FROM read_csv('abc\film.csv')
),

film_actor AS (
SELECT *
FROM read_csv('abc\film_actor.csv')
),

tbl1 AS (
  SELECT
    f.title,
    f.film_id,
    fa.actor_id
  FROM film AS f
  INNER JOIN film_actor AS fa
    ON f.film_id = fa.film_id
   AND fa.actor_id IN (105, 122)
)
SELECT
  title
FROM tbl1
GROUP BY film_id, title
HAVING COUNT(DISTINCT actor_id) = 2
ORDER BY title;
