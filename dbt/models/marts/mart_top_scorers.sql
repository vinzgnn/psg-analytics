-- ================================================================
-- mart_top_scorers : top buteurs L1 prêts pour le dashboard
-- ================================================================
-- Source : stg_scorers
-- Matérialisation : table
-- Enrichissements :
--   - goals_open_play     : buts hors penalty
--   - goal_contributions  : buts + passes décisives
-- ================================================================

with scorers as (

    select * from {{ ref('stg_scorers') }}

)

select
    rank,
    -- Identifiants joueur
    player_id,
    player_name,
    player_first_name,
    player_last_name,
    player_position,
    player_nationality,
    player_age,
    player_date_of_birth,

    -- Identifiants équipe
    team_id,
    team_name,
    team_short_name,
    team_tla,
    is_psg_player,

    -- Stats brutes
    goals,
    assists,
    penalties,
    played_matches,

    -- Stats dérivées
    goals - penalties             as goals_open_play,
    goals + assists               as goal_contributions,
    goals_per_match,

    ingested_at

from scorers
order by rank
