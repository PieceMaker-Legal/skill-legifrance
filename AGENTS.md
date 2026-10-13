# Skill Legifrance — consignes agents

## Périmètre

Ces instructions s'appliquent à ce dépôt et à ses descendants. Traiter
cette skill comme un projet Python autonome. Son runtime, ses tests, sa
configuration et sa documentation ne dépendent d'aucun installateur, daemon
ou arborescence tierce.

## Mission

Exposer les sources juridiques officielles françaises par un script CLI.
Préserver la fidélité des sources, la reproductibilité et le signalement
explicite des échecs. Les conclusions de droit restent à l'appelant.

## Contrat d'exécution

- Point d'entrée : `scripts/legifrance.py`.
- stdout reçoit le résultat de la commande ; tout journal va sur stderr.
- `list`, `ping`, `setup`, `--help` et `dictionnaire_juridique`
  fonctionnent sans identifiants. Seuls les appels Légifrance les exigent.
- La mise en place du client PISTE est `scripts/legifrance.py setup`
  (`tools/credentials.py`) : guide d'inscription, écriture de
  `~/.config/skill-legifrance/.env` (mode 600), contrôle OAuth `--check`.
- Configuration : variables d'environnement ou `.env` local, jamais un
  fichier d'installateur.
- Requis pour Légifrance : `LEGIFRANCE_CLIENT_ID` et
  `LEGIFRANCE_CLIENT_SECRET`.
- Optionnel : `LEGIFRANCE_ENV=production|sandbox`, `LEGIFRANCE_DEBUG=1`,
  `LEGIFRANCE_ENV_FILE=/chemin/absolu/.env`.
- Fichier d'identifiants par défaut : `~/.config/skill-legifrance/.env`.
- Ne jamais imprimer identifiants, jetons OAuth, en-têtes d'autorisation
  ou contenu confidentiel.

## Architecture

```text
skill-legifrance/              # dépôt GitHub
├── SKILL.md                   # contrat métier Agent Skills (name: legifrance)
├── references/installation.md # venv, client PISTE (renvoi depuis SKILL.md)
├── .claude-plugin/            # plugin + marketplace Claude Code
├── scripts/legifrance.py      # CLI (dont setup PISTE)
├── config/mcp_definitions.py  # schémas des commandes
├── config/settings.py         # environnement et endpoints
├── tools/credentials.py       # guide PISTE, .env, contrôle OAuth
├── tools/handlers.py          # dispatch métier
├── tools/legifrance_client.py # frontière HTTP PISTE
├── resources/                 # lexique API
└── tests/                     # tests hors réseau
```

Le champ `name` de `SKILL.md` est `legifrance` : le dossier d'installation
(`~/.claude/skills/legifrance`, `.claude/skills/legifrance`) doit porter
ce nom. Le dépôt GitHub peut s'appeler `skill-legifrance`.

Les schémas, le CLI, les handlers, les tests et `SKILL.md` restent alignés.
La logique de domaine reste dans `tools/`, pas dans la boucle CLI.

## Syntaxe des recherches

Commandes publiques : `Search_Cour_Cassation`, `Search_Cour_Appel`,
`Search_Conseil_Etat`, `Search_CAA`, `Search_Premiere_Instance`,
`Search_Code`. Ne pas rétablir `recherche_jurisprudence`.

- guillemets = expression exacte : `"faute grave"`
- `ET` plus prioritaire que `OU`
- parenthèses pour regrouper
- sans opérateur, les mots non cités sont joints par `ET`
- `Search_Premiere_Instance` joint par `OU` en l'absence d'`ET`/`OU`
- les références d'articles sont normalisées

Contrat centralisé dans `config/mcp_definitions.py`, repris par le CLI.

## Développement

- Python 3, UTF-8.
- Messages opérationnels en français ; les noms de commandes restent
  stables.
- Pas de cadre si la bibliothèque standard suffit.
- Timeouts HTTP et erreurs actionnables, sans secret.
- Identifiants officiels, dates, textes et citations non altérés.
- Pas de retry infini ; borner et consigner l'échec terminal.
- N'écrire hors d'un répertoire de sortie choisi par l'appelant.

## Vérification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/legifrance.py list
python3 scripts/legifrance.py ping
python3 scripts/legifrance.py setup
```

Pour un essai réseau : répertoire de sortie temporaire, rapporter les
appels et les totaux. Ne jamais committer identifiants, `.env`, journaux
ou rapports générés.

## Definition of done

Démarrage autonome, schémas = handlers = CLI, tests hors réseau verts,
stdout = résultat de commande, échecs explicites, aucune dépendance à un
installateur parent.
