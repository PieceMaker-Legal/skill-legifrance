# Installation

Le dossier de la skill est celui qui contient `SKILL.md`. Claude Code le fournit dans `${CLAUDE_SKILL_DIR}`. Si la variable est vide, exécuter depuis ce dossier.

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

Le fichier écrit est `~/.config/skill-legifrance/.env` (permissions 600), sauf si `LEGIFRANCE_ENV_FILE` pointe ailleurs. Ne jamais imprimer le secret, un jeton OAuth ou un en-tête d'autorisation.

Si un appel Légifrance échoue pour identifiants manquants, relancer `setup`. `list`, `ping`, `--help`, `setup` et `dictionnaire_juridique` fonctionnent sans client PISTE.
