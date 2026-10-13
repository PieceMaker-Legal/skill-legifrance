---
name: legifrance
description: Rechercher et consulter les sources juridiques officielles françaises (Légifrance, PISTE, BODACC, lexique justice.fr). À utiliser pour une recherche de jurisprudence, un article de code, une décision JURITEXT/CETATEXT, un corpus exhaustif, le BODACC, le dictionnaire juridique, ou /legifrance.
compatibility: Requires Python 3 and HTTPS access to PISTE (oauth.piste.gouv.fr, api.piste.gouv.fr)
metadata:
  author: PieceMaker Legal
  version: "1.0.0"
---

# Skill Legifrance

Les sources officielles passent par `scripts/legifrance.py`. Les schémas et drapeaux font autorité dans `--help` ; ne pas inventer de flag.

Le dossier de la skill est celui qui contient ce `SKILL.md`. Claude Code le fournit dans `${CLAUDE_SKILL_DIR}`. Si la variable est vide, exécuter depuis ce dossier.

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/legifrance.py setup
python3 ${CLAUDE_SKILL_DIR}/scripts/legifrance.py --help
python3 ${CLAUDE_SKILL_DIR}/scripts/legifrance.py list
```

Le script crée un `.venv` local au premier appel.

## Client PISTE

Toute recherche Légifrance exige un client OAuth PISTE. `setup` en est le contrat : guide d'inscription, fichier d'identifiants, contrôle du jeton.

1. Lancer `python3 ${CLAUDE_SKILL_DIR}/scripts/legifrance.py setup` (sans identifiants : imprime le guide officiel et l'état).
2. Faire créer le compte et l'application sur https://piste.gouv.fr/ (souscription API Légifrance, génération OAuth). Production et sandbox ont des identifiants distincts.
3. Demander à l'utilisateur le `client_id` et le `client_secret`, puis les enregistrer sans les réafficher :

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/legifrance.py setup \
  --client-id '…' --client-secret '…' --env production --check
```

Le fichier écrit est `~/.config/skill-legifrance/.env` (permissions 600), sauf si `LEGIFRANCE_ENV_FILE` pointe ailleurs. Un `~/.config/mcp-legifrance/.env` déjà présent est relu. Ne jamais imprimer le secret, un jeton OAuth ou un en-tête d'autorisation.

Si un appel Légifrance échoue pour identifiants manquants, relancer `setup`. `list`, `ping`, `--help`, `setup` et `dictionnaire_juridique` fonctionnent sans client PISTE.

## Requête

Une seule formulation par appel. Reprendre les termes de l'utilisateur. N'ajouter un synonyme qu'après `dictionnaire_juridique`. Un article cité par l'utilisateur entre dans la requête ; borner les dates à la version applicable.

- `"faute grave"` = expression exacte (guillemets droits)
- `ET` plus prioritaire que `OU` : `A OU B ET C` = `A OU (B ET C)`
- parenthèses pour regrouper : `(A OU B) ET C`
- sans opérateur, les mots non cités sont joints par `ET`
- `Search_Premiere_Instance` joint par `OU` en l'absence d'`ET`/`OU` ; écrire `ET` pour un cumul
- `L. 1235-3` est normalisé automatiquement

Au-delà de 500 résultats, l'appel est refusé : resserrer la requête.

## Quelle commande

| Besoin | Commande |
| --- | --- |
| Cassation | `Search_Cour_Cassation` (`--matiere` obligatoire : `CIVIL`, `COMMERCIAL`, `PENAL`, `SOCIAL`) |
| Cours d'appel | `Search_Cour_Appel` |
| Conseil d'État | `Search_Conseil_Etat` |
| CAA | `Search_CAA` |
| Premier degré | `Search_Premiere_Instance` (`--PREMIER_DEGRE_TYPE_JURIDICTION` obligatoire) |
| Codes | `Search_Code` puis `consulter_article --article_id LEGIARTI…` |
| Texte d'une décision | `consulter_decision --text_id JURITEXT…` ou `CETATEXT…` |
| Fil procédural + « citée par » | `Historique_Judiciaire --text_id …` |
| Procédures collectives | `Tracking_BODACC --siren …` |
| Définition d'un terme | `dictionnaire_juridique --terme …` |
| Corpus exhaustif sans RAG | `Build_Research_Corpus --question '…' --query '…'` |

Exemple :

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/legifrance.py Search_Cour_Cassation \
  --query '("faute grave" OU "faute lourde") ET licenciement' \
  --matiere SOCIAL
python3 ${CLAUDE_SKILL_DIR}/scripts/legifrance.py consulter_decision --text_id JURITEXT000007000000
```

Les tableaux et les drapeaux détaillés : `python3 ${CLAUDE_SKILL_DIR}/scripts/legifrance.py <commande> --help`.

## Conduite

1. Clarifier le fonds (judiciaire / administratif / code / BODACC) si l'utilisateur ne l'a pas dit.
2. Formuler une requête, lancer la recherche, lire le total.
3. Avant de citer une décision ou un article, consulter le texte intégral via l'identifiant officiel renvoyé.
4. Citer un sous-chaîne littérale du texte officiel et garder l'identifiant (`JURITEXT`, `CETATEXT`, `LEGIARTI`) et le lien Légifrance.
5. Pour un état de la jurisprudence, `Build_Research_Corpus` pagine, déduplique, télécharge et cartographie tout le manifeste ; un score lexical n'élimine aucune décision.

Ne jamais fabriquer un identifiant, un numéro d'arrêt ou un article. Une absence de résultat se dit comme une absence, pas comme une règle contraire. Les conclusions juridiques restent à l'appelant.
