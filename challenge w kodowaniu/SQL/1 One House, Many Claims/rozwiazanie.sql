/*
 REZULTAT
 OSTATNI KOD NIE ZADZIALA RACZEJ NA DUCKDB (problem z %s), ale platforma codewars przyjmuje to
| audit_note                                                                   |
+------------------------------------------------------------------------------+
| 3 applications (applicant_ids: 101, 107, 112) already filed at 12 Elm St     |
| 2 applications (applicant_ids: 1021, 1097) already filed at 6 Mc Gill Crst   |
| 2 applications (applicant_ids: 1300, 1402) already filed at 195 Mc Gill Crst |

*/


WITH energy_rebate_applications AS (
SELECT *
FROM read_csv('abc\applicants.csv')
),

tbl1 AS (
  SELECT
    house_no,
    street_name,
    COUNT(*) AS n,
    STRING_AGG(applicant_id::TEXT, ', ' ORDER BY applicant_id) AS ids
  FROM energy_rebate_applications
  GROUP BY house_no, street_name
  HAVING COUNT(*) > 1
)
SELECT
  FORMAT('%s applications (applicant_ids: %s) already filed at %s %s',
         n, ids, house_no, street_name) AS audit_note
FROM tbl1
ORDER BY n DESC, street_name ASC, house_no ASC;



