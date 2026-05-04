-- ================================================================
-- stg_matches : matchs de Ligue 1 nettoyés et enrichis
-- ================================================================
-- Source : raw_matches (couche raw)
-- Matérialisation : view (configurée dans dbt_project.yml)
-- Conventions :
--   - Pattern CTE pour lisibilité
--   - Ajout de flags dérivés (is_psg_match, psg_side, is_finished)
--   - PSG team_id = 524 (référence football-data.org)
-- ================================================================

with source as (

    select * from {{ source('raw', 'raw_matches') }}

),

cleaned as (

    select
        -- Identifiants
        match_id,
        season_id,
        competition_code,
        competition_name,

        -- Dates
        utc_date,
        date(utc_date) as match_date,
        season_start_date,
        season_end_date,

        -- Méta-match
        status,
        matchday,
        stage,
        duration,

        -- Équipe à domicile
        home_team_id,
        home_team_name,
        home_team_short_name,
        home_team_tla,

        -- Équipe à l'extérieur
        away_team_id,
        away_team_name,
        away_team_short_name,
        away_team_tla,

        -- Score
        home_score_full_time,
        away_score_full_time,
        home_score_half_time,
        away_score_half_time,
        winner,

        -- Flags dérivés (simplifient les marts en aval)
        status = 'FINISHED' as is_finished,
        home_team_id = 524 or away_team_id = 524 as is_psg_match,
        case
            when home_team_id = 524 then 'HOME'
            when away_team_id = 524 then 'AWAY'
            else null
        end as psg_side,

        -- Trace d'ingestion
        ingested_at

    from source

)

select * from cleaned
