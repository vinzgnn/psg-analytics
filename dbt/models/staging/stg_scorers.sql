-- ================================================================
-- stg_scorers : top buteurs Ligue 1 nettoyés et enrichis
-- ================================================================
-- Source : raw_scorers (couche raw)
-- Matérialisation : view
-- Enrichissement : calcul de l'âge actuel du joueur
-- ================================================================

with source as (

    select * from {{ source('raw', 'raw_scorers') }}

),

cleaned as (

    select
        -- Identifiants saison/compétition
        season_id,
        season_start_date,
        season_end_date,
        competition_code,
        competition_name,

        -- Rang dans le top scoreurs
        rank,

        -- Identifiants joueur
        player_id,
        player_name,
        player_first_name,
        player_last_name,
        player_nationality,
        player_position,
        player_date_of_birth,
        date_diff(current_date(), player_date_of_birth, year) as player_age,

        -- Identifiants équipe
        team_id,
        team_name,
        team_short_name,
        team_tla,

        -- Statistiques offensives
        goals,
        coalesce(assists, 0) as assists,
        coalesce(penalties, 0) as penalties,
        played_matches,

        -- Ratios calculés
        case
            when played_matches > 0 then round(goals / played_matches, 2)
            else null
        end as goals_per_match,

        -- Flag joueur PSG
        team_id = 524 as is_psg_player,

        -- Trace d'ingestion
        ingested_at

    from source

)

select * from cleaned
