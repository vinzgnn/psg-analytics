-- ================================================================
-- stg_standings : classement Ligue 1 nettoyé
-- ================================================================
-- Source : raw_standings (couche raw)
-- Matérialisation : view
-- Note : conserve toutes les vues (TOTAL/HOME/AWAY) — le filtrage
--        se fait dans les marts selon le besoin métier.
-- ================================================================

with source as (

    select * from {{ source('raw', 'raw_standings') }}

),

cleaned as (

    select
        -- Identifiants
        season_id,
        competition_code,
        competition_name,

        -- Dates de saison
        season_start_date,
        season_end_date,

        -- Type de classement (TOTAL / HOME / AWAY)
        standings_type,

        -- Position et équipe
        position,
        team_id,
        team_name,
        team_short_name,
        team_tla,

        -- Statistiques
        played_games,
        form,
        won,
        draw,
        lost,
        points,
        goals_for,
        goals_against,
        goal_difference,

        -- Flag PSG
        team_id = 524 as is_psg,

        -- Trace d'ingestion
        ingested_at

    from source

)

select * from cleaned
