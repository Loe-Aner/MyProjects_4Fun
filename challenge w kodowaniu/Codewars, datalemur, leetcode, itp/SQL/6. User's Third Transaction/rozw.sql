WITH tbl1 AS (SELECT
  user_id,
  spend,
  transaction_date,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY transaction_date) AS rank
FROM transactions)

SELECT
  user_id,
  spend,
  transaction_date
FROM tbl1
WHERE rank = 3;
