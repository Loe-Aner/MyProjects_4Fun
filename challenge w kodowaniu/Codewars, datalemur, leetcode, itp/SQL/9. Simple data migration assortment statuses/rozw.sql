WITH store_and_statuses AS (
  SELECT 
    pss.product_id,
    s.cluster_id,
    pss.status_id
  FROM product_store_statuses AS pss
  INNER JOIN stores AS s
    ON s.id = pss.store_id
  WHERE s.cluster_id IS NOT NULL
),
cnt AS (
  SELECT
    product_id,
    cluster_id,
    status_id,
    COUNT(*) AS cnt
  FROM store_and_statuses
  GROUP BY
    product_id,
    cluster_id,
    status_id
),
rnk AS (
  SELECT
    c.product_id,
    c.cluster_id,
    c.status_id,
    ROW_NUMBER() OVER (
      PARTITION BY c.product_id, c.cluster_id
      ORDER BY c.cnt DESC, st.priority ASC
    ) AS rn
  FROM cnt AS c
  JOIN statuses AS st
    ON st.id = c.status_id
)
INSERT INTO product_cluster_statuses (product_id, cluster_id, status_id)
SELECT
  product_id,
  cluster_id,
  status_id
FROM rnk
WHERE rn = 1;

DELETE FROM product_store_statuses AS pss
USING stores AS s, product_cluster_statuses AS pcs
WHERE pss.store_id = s.id
  AND s.cluster_id IS NOT NULL
  AND pcs.cluster_id = s.cluster_id
  AND pcs.product_id = pss.product_id
  AND pss.status_id = pcs.status_id;
