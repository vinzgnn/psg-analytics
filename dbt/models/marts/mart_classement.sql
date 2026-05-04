-- ================================================================
-- mart_classement : classement Ligue 1 prêt pour le dashboard
-- ================================================================
-- Source : stg_standings (filtré sur standings_type = 'TOTAL')
-- Matérialisation : table
-- Enrichissements :
--   - points_ahead_of_next : écart de points avec l'équipe suivante
--   - points_behind_prev   : écart de points avec l'équipe précédente
-- ================================================================

with standings as (

    select *
    from {{ ref('stg_standings') }}
    where standings_type = 'TOTAL'

),

with_gaps as (

    select
        *,
        lead(points) over (order by position)     as next_team_points,
        lag(points) over (order by position)      as prev_team_points,
        lead(team_name) over (order by position)  as next_team_name,
        lag(team_name) over (order by position)   as prev_team_name
    from standings

)

select
    position,
    team_id,
    team_name,
    team_short_name,
    team_tla,
    played_games,
    won,
    draw,
    lost,
    points,
    goals_for,
    goals_against,
    goal_difference,
    form,
    is_psg,
    -- Écarts de points (NULL si bord du classement)
    points - coalesce(next_team_points, points) as points_ahead_of_next,
    coalesce(prev_team_points, points) - points as points_behind_prev,
    next_team_name,
    prev_team_name,
    ingested_at

from with_gaps
order by position
