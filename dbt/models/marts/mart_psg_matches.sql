-- ================================================================
-- mart_psg_matches : matchs PSG normalisés en perspective PSG
-- ================================================================
-- Source : stg_matches (filtré sur is_psg_match)
-- Matérialisation : table
-- Logique :
--   On retourne une ligne par match du PSG, en "redressant" les colonnes
--   home/away pour qu'elles soient toujours du POINT DE VUE du PSG.
--   Cela simplifie énormément l'analyse côté dashboard.
-- ================================================================

with psg_matches as (

    select *
    from {{ ref('stg_matches') }}
    where is_psg_match

),

normalized as (

    select
        match_id,
        match_date,
        utc_date,
        matchday,
        status,
        is_finished,
        psg_side,                                -- 'HOME' ou 'AWAY'

        -- Adversaire
        case
            when psg_side = 'HOME' then away_team_name
            when psg_side = 'AWAY' then home_team_name
        end as opponent_name,

        case
            when psg_side = 'HOME' then away_team_short_name
            when psg_side = 'AWAY' then home_team_short_name
        end as opponent_short_name,

        case
            when psg_side = 'HOME' then away_team_tla
            when psg_side = 'AWAY' then home_team_tla
        end as opponent_tla,

        -- Score normalisé en POV PSG
        case
            when psg_side = 'HOME' then home_score_full_time
            when psg_side = 'AWAY' then away_score_full_time
        end as psg_score,

        case
            when psg_side = 'HOME' then away_score_full_time
            when psg_side = 'AWAY' then home_score_full_time
        end as opponent_score,

        -- Résultat depuis le POV PSG
        case
            when not is_finished then null
            when (psg_side = 'HOME' and home_score_full_time > away_score_full_time)
              or (psg_side = 'AWAY' and away_score_full_time > home_score_full_time)
                then 'WIN'
            when home_score_full_time = away_score_full_time
                then 'DRAW'
            else 'LOSS'
        end as psg_result

    from psg_matches

)

select
    *,
    -- Différentiel de buts (POV PSG)
    psg_score - opponent_score as psg_goal_diff,
    -- Points gagnés sur ce match
    case psg_result
        when 'WIN'  then 3
        when 'DRAW' then 1
        when 'LOSS' then 0
        else null
    end as psg_points,
    -- Indicateur clean sheet
    case
        when not is_finished then null
        when opponent_score = 0 then true
        else false
    end as is_clean_sheet
from normalized
order by match_date desc
