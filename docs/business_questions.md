# Questions métier — PSG Analytics

> Ce document liste les questions analytiques auxquelles le projet doit répondre.
> Il sert de **source de vérité** pour la modélisation des données (dbt), la conception
> du dashboard Looker Studio et le périmètre de l'assistant IA.

**Auteur :** Vincent Génin
**Dernière mise à jour :** 2026-05-04
**Statut :** Validé — Phase 1

---

## 1. Vue Équipe — performance collective

- Quels sont les résultats du PSG sur les 10 derniers matchs ? (V/N/D, buts marqués/encaissés)
- Quelle est la forme actuelle du PSG comparée à la moyenne de la saison ?
- Quel est le différentiel xG (créé vs concédé) sur les derniers matchs ?
- Le PSG est-il plus performant à domicile ou à l'extérieur ?
- Combien de tirs et quelle possession moyenne par match ?

## 2. Vue Joueurs — performances individuelles

- Qui sont les meilleurs buteurs et passeurs du PSG cette saison ?
- Quels joueurs sont en forme ce mois-ci comparé à leur moyenne saison ?
- Qui a le plus de minutes jouées ? Qui est sous-utilisé ?
- Quel est l'âge moyen de l'effectif aligné ?

## 3. Vue Classement — positionnement en Ligue 1

- Quelle est la position actuelle du PSG en Ligue 1 ?
- Quel est l'écart avec le 2e ? Avec le podium ?
- Quelle projection de points en fin de saison au rythme actuel ?
- Comment le PSG se compare-t-il aux autres "gros" (OM, Monaco, Lyon) sur les indicateurs clés ?

## 4. Périmètre de l'assistant IA (Phase 4)

L'assistant Claude doit pouvoir répondre en langage naturel à des questions telles que :

- « Qui est en forme en ce moment ? »
- « Résume-moi le dernier match du PSG »
- « Compare plusieurs joueurs sur les 5 derniers matchs »
- « Quelle est la tendance du PSG ces 4 dernières semaines ? »
- « Quel est le meilleur buteur du mois ? »

---

## Implications techniques

| Question | Table cible (mart) | Source raw |
|---|---|---|
| Résultats / forme équipe | `mart_performance` | `raw_matches` |
| Stats joueurs | `mart_joueurs` | `raw_players` |
| Classement et projection | `mart_classement` | `raw_standings` |

Ces marts seront construits via dbt à partir des couches `raw_*` (API brute) et
`stg_*` (nettoyage/standardisation).
