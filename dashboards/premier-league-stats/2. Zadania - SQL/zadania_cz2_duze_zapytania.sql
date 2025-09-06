WITH src AS (
    SELECT
        *,
        REPLACE(
            LIST_EXTRACT(
                STRING_SPLIT(REPLACE(filename, '\', '/'), '/'),
                -1
            ),
            '.csv', ''
        ) AS Team
    FROM read_csv(
        'abc/*.csv',
        AUTO_DETECT = TRUE,
        HEADER = TRUE,
        HIVE_PARTITIONING = TRUE,
        FILENAME = TRUE
    )
),
tbl AS (
    SELECT
        Date                      AS date,
        Team                      AS team,
        Opponent                  AS opponent,
        Is_Home                   AS home_game,          -- 1=home, 0=away
        Result                    AS outcome,            -- 1=win, 0=draw, -1=loss
        Goals                     AS goals_for,
        Opponent_Goals            AS goals_against,
        Possession                AS poss_pct,
        Shots                     AS shots,
        Shots_On_Target           AS shots_on_target,
        Passes_Completed          AS passes_completed,
        Pass_Accuracy             AS pass_accuracy_pct,
        Corners                   AS corners,
        Crosses                   AS crosses,
        Fouls                     AS fouls,
        Offsides                  AS offsides,
        Opponent_Possession       AS opp_poss_pct,
        Opponent_Shots            AS opp_shots,
        Opponent_Shots_On_Target  AS opp_shots_on_target,
        Opponent_Passes_Completed AS opp_passes_completed,
        Opponent_Pass_Accuracy    AS opp_pass_accuracy_pct,
        Opponent_Corners          AS opp_corners,
        Opponent_Crosses          AS opp_crosses,
        Opponent_Fouls            AS opp_fouls,
        Opponent_Offsides         AS opp_offsides,
        Shot_Efficiency           AS goals_per_shot,
        Season                    AS season,
        Month                     AS month,
        Day_of_Week               AS weekday
    FROM src
),

--SELECT *
--FROM tbl


-- 3. Najlepsze 3 miesiace druzyn w ostatnich 3 sezonach (posortowane po sumie pkt, roznicy bramek, skutecznosci strzeleckiej)
best_3_m AS (
  SELECT
    team,
    season,
    EXTRACT(MONTH FROM date) AS month,
    COUNT(*) AS games,
    SUM(CASE 
      WHEN outcome = 1 THEN 3
      WHEN outcome = 0 THEN 1
      ELSE 0
    END) AS points,
    SUM(goals_for - goals_against) AS gd,
    1.0 * SUM(shots_on_target) / NULLIF(SUM(shots), 0) AS sot_rate,
    1.0 * SUM(goals_for) / NULLIF(SUM(shots), 0) AS conv_rate
  FROM tbl
  WHERE season <= 2024
  GROUP BY team, season, EXTRACT(MONTH FROM date)
  HAVING COUNT(*) >= 3
)

SELECT
  *,
  ROW_NUMBER() OVER (
    PARTITION BY team, season
    ORDER BY points DESC, gd DESC, conv_rate DESC
  ) AS rnk
FROM best_3_m
QUALIFY rnk <= 3
ORDER BY team, season, rnk;

-- 4. Dla kazdego team, season, policzyc PPG u siebie vs na wyjezdzie oraz roznice home_edge = ppg_home - ppg_away
SELECT 
  team,
  season,
  ROUND(AVG(CASE 
  	WHEN outcome = 1 AND home_game = 1 THEN 3
  	WHEN outcome = 0 AND home_game = 1 THEN 1
  	ELSE 0
  END) FILTER (WHERE home_game = 1), 2) AS ppg_home,
  ROUND(AVG(CASE 
  	WHEN outcome = 1 AND home_game = 0 THEN 3
  	WHEN outcome = 0 AND home_game = 0 THEN 1
  	ELSE 0
  END) FILTER (WHERE home_game = 0), 2) AS ppg_away,
  ppg_home - ppg_away AS diff 							-- dziala w duckdb :)
FROM tbl
WHERE season BETWEEN 2022 AND 2024
GROUP BY team, season
ORDER BY team, season DESC, diff DESC


-- 5. Znalezc mecze, w ktorych zespol dominowal wzgledem wlasnych srednich a nie wygral (ostatni sezon)
--    a. suma punktow w totalu,
--    b. strzaly na bramke,
--    c. liczba roznych,
--    d. liczba goli

-- ======================== PIERWSZE ROZWIAZANIE, NAJEFEKTYWNIEJSZE ========================
base AS (
    SELECT
        t.team,
        t.opponent,
        t.outcome,
        t.shots,
        t.shots_on_target,
        t.corners,
        t.crosses,
        CASE
            WHEN t.outcome = 1 THEN 3
            WHEN t.outcome = 0 THEN 1
            ELSE 0
        END AS points,
        AVG(t.shots)             OVER (PARTITION BY t.team) AS shots_avg,
        AVG(t.shots_on_target)   OVER (PARTITION BY t.team) AS shots_on_target_avg,
        AVG(t.corners)           OVER (PARTITION BY t.team) AS corners_avg,
        AVG(t.crosses)           OVER (PARTITION BY t.team) AS crosses_avg,
        SUM(CASE
                WHEN t.outcome = 1 THEN 3
                WHEN t.outcome = 0 THEN 1
                ELSE 0
            END) OVER (PARTITION BY t.team) AS season_points_total
    FROM tbl AS t
    WHERE t.season = 2024
)
SELECT
    team,
    opponent,
    outcome,
    ROUND(shots - shots_avg, 2)            AS shots_diff,
    ROUND(shots_on_target - shots_on_target_avg, 2) AS shots_on_target_diff,
    ROUND(corners - corners_avg, 2)        AS corners_diff,
    ROUND(crosses - crosses_avg, 2)        AS crosses_diff,
    season_points_total
FROM base
WHERE outcome IN (0, -1)
  AND shots            > shots_avg
  AND shots_on_target  > shots_on_target_avg
  AND corners          > corners_avg
  AND crosses          > crosses_avg
ORDER BY shots_on_target_diff DESC;


-- ======================== DRUGIE ROZWIAZANIE, Z JOINEM (MNIEJ EFEKTYWNE) ========================
srednie AS (
    SELECT
        team,
        AVG(CASE WHEN outcome = 1 THEN 3
                 WHEN outcome = 0 THEN 1
                 ELSE 0 END)   AS points_avg,
        AVG(shots)             AS shots_avg,
        AVG(shots_on_target)   AS shots_on_target_avg,
        AVG(corners)           AS corners_avg,
        AVG(crosses)           AS crosses_avg
    FROM tbl
    WHERE season = 2024
    GROUP BY team
),
porownanie AS (
    SELECT
        t1.team,
        t1.opponent,
        t1.outcome,
        t1.shots           - s.shots_avg            AS shots_diff,
        t1.shots_on_target - s.shots_on_target_avg  AS shots_on_target_diff,
        t1.corners         - s.corners_avg          AS corners_diff,
        t1.crosses         - s.crosses_avg          AS crosses_diff,
        SUM(CASE
                WHEN t1.outcome = 1 THEN 3
                WHEN t1.outcome = 0 THEN 1
                ELSE 0
            END) OVER (PARTITION BY t1.team) AS season_points_total
    FROM tbl AS t1
    INNER JOIN srednie AS s
        ON t1.team = s.team
    WHERE t1.season = 2024
)
SELECT
    team,
    opponent,
    outcome,
    ROUND(shots_diff, 2)             AS shots_diff,
    ROUND(shots_on_target_diff, 2)   AS shots_on_target_diff,
    ROUND(corners_diff, 2)           AS corners_diff,
    ROUND(crosses_diff, 2)           AS crosses_diff,
    season_points_total
FROM porownanie
WHERE outcome IN (0, -1)
  AND shots_diff > 0
  AND shots_on_target_diff > 0
  AND corners_diff > 0
  AND crosses_diff > 0
ORDER BY shots_on_target_diff DESC;



