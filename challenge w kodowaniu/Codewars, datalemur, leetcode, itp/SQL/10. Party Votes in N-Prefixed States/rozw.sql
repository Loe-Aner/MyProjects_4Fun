SELECT
  p.name AS party_name,
  s.name AS state_name,
  COUNT(v.id) AS voter_count
FROM parties AS p
INNER JOIN voters AS v
  ON p.id = v.party_id
INNER JOIN states AS s
  ON v.state_id = s.id
WHERE s.name ILIKE 'N%'
GROUP BY p.name, s.name
ORDER BY party_name DESC, state_name ASC;