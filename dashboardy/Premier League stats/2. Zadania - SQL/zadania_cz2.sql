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





-- 5. Dla team, season policzyc:
--    a. team_ppg - srednie punkty/mecz zespolu,
--    b. avg_opp_ppg - srednie ppg przeciwnikow (liczone po ich calym sezonie)
--    c. nastepnie zestawic oba wskazniki 





-- 6. Znalezc mecze, w ktorych zespol zdecydowanie dominowal wzgledem wlasnych srednich a nie wygral


