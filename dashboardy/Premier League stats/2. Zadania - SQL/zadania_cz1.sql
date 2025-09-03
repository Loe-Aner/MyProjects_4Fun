WITH src AS (
    SELECT
        * ,
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
        Day_of_Week               AS weekday,
        Last5_Avg_Goals           AS avg_goals_last5,
        Last5_Win_Rate            AS win_rate_last5
    FROM src
)


-- 1. Podzial goli na stracone/strzelone po sezonach i klubach

SELECT
    team,
    season,
    'Gole strzelone' AS typ,
    SUM(goals_for) AS gole
FROM tbl
GROUP BY team, season

UNION ALL

SELECT
    team,
    season,
    'Gole stracone' AS typ,
    SUM(goals_against) * -1.0 AS gole
FROM tbl
GROUP BY team, season;


-- 2. Pozostale statystyki do sekcji po prawej stronie w dashboardzie
SELECT
  team,
  season,
  ROUND(SUM(goals_for) * 1.0 / COUNT(*), 2) AS sr_goli_strzelonych_na_mecz,
  ROUND(SUM(goals_for) * 1.0 / NULLIF(SUM(shots), 0), 4) AS skutecznosc_strzelecka,
  ROUND(SUM(shots_on_target) * 1.0 / NULLIF(SUM(shots), 0), 4) AS celnosc_strzalow,
  ROUND(SUM(goals_against) * 1.0 / COUNT(*), 2) AS sr_straconych_goli,
  ROUND(COUNT(*) FILTER (WHERE goals_against = 0) * 1.0 / COUNT(*), 4) AS proc_czystych_kont,
  ROUND(COUNT(*) FILTER (WHERE outcome = 1) * 1.0 / COUNT(*), 4) AS win_rate,
  ROUND(SUM(CASE WHEN outcome = 1 THEN 3 WHEN outcome = 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*), 2) AS sr_liczba_pkt_na_mecz,
  ROUND(AVG(poss_pct) / 100, 4) AS sr_posiadanie_pilki,
  ROUND(AVG(pass_accuracy_pct) / 100, 4) AS sr_dokladnosc_podan
FROM tbl
GROUP BY team, season
ORDER BY team DESC, season DESC;






