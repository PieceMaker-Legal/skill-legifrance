# Skill Legifrance — consignes agents

## Périmètre

Ces instructions s'appliquent à ce dépôt et à ses descendants. Traiter
cette skill comme un projet Python autonome. Son runtime, ses tests, sa
configuration et sa documentation ne dépendent d'aucun installateur, daemon
ou arborescence tierce.

## Mission

Exposer les sources juridiques officielles françaises par un script CLI.
Préserver la fidélité des sources, la reproductibilité, la télémétrie des
recherches exhaustives et le signalement explicite des échecs. Les
conclusions de droit restent à l'appelant.

## Contrat d'exécution

- Point d'entrée : `scripts/legifrance.py`.
- stdout reçoit le résultat de la commande ; tout journal va sur stderr.
- `list`, `ping`, `--help` et `dictionnaire_juridique` fonctionnent sans
  identifiants. Seuls les appels réseau peuvent échouer pour ce motif.
- Configuration : variables d'environnement ou `.env` local, jamais un
  fichier d'installateur.
- Requis pour Légifrance : `LEGIFRANCE_CLIENT_ID` et
  `LEGIFRANCE_CLIENT_SECRET`.
- Optionnel : `LEGIFRANCE_ENV=production|sandbox`, `LEGIFRANCE_DEBUG=1`,
  `LEGIFRANCE_ENV_FILE=/chemin/absolu/.env`.
- Fichiers d'identifiants acceptés, dans cet ordre si
  `LEGIFRANCE_ENV_FILE` est absent : `~/.config/skill-legifrance/.env`
  puis `~/.config/mcp-legifrance/.env`.
- Ne jamais imprimer identifiants, jetons OAuth, en-têtes d'autorisation
  ou contenu confidentiel.

## Architecture

```text
skill-legifrance/
├── SKILL.md                   # contrat agent
├── scripts/legifrance.py      # CLI
├── config/mcp_definitions.py  # schémas des commandes
├── config/settings.py         # environnement et endpoints
├── tools/handlers.py          # dispatch métier
├── tools/legifrance_client.py # frontière HTTP PISTE
├── tools/research_corpus.py   # parcours exhaustif sans RAG
├── resources/                 # lexique API
└── tests/                     # tests hors réseau
```

Les schémas, le CLI, les handlers, les tests et `SKILL.md` restent alignés.
La logique de domaine reste dans `tools/`, pas dans la boucle CLI.

## Syntaxe des recherches

Commandes publiques : `Search_Cour_Cassation`, `Search_Cour_Appel`,
`Search_Conseil_Etat`, `Search_CAA`, `Search_Premiere_Instance`,
`Search_Code`, `Build_Research_Corpus`. Ne pas rétablir
`recherche_jurisprudence`.

- guillemets = expression exacte : `"faute grave"`
- `ET` plus prioritaire que `OU`
- parenthèses pour regrouper
- sans opérateur, les mots non cités sont joints par `ET`
- `Search_Premiere_Instance` joint par `OU` en l'absence d'`ET`/`OU`
- les références d'articles sont normalisées

Contrat centralisé dans `config/mcp_definitions.py`, repris par le CLI.

## Recherche exhaustive

`Build_Research_Corpus` implémente un parcours sans RAG :

- pas d'embeddings, de base vectorielle, de top-k sémantique ni de
  présélection cachée ;
- pagination de chaque requête jusqu'aux plafonds déclarés ;
- déduplication par identifiant officiel Légifrance ;
- téléchargement et scan de chaque décision disponible du manifeste ;
- conservation de chaque échec de téléchargement et de chaque troncature ;
- une fiche par décision téléchargée ; le code ne clôt que les textes qui
  échouent un test booléen documenté, chaque candidat va au modèle ;
- tous les contextes d'ancre des candidats, jamais un top-k de similarité ;
- citations = sous-chaînes littérales de la source ;
- validation statique des identifiants, de la cardinalité, du schéma et
  des citations ;
- les comptes de tokens par caractères sont des estimations, jamais un
  usage fournisseur.

Un score lexical peut ordonner un index d'audit ; il n'ôte aucune décision
des lots ni du jeu de validation.

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
```

Pour un essai réseau : répertoire de sortie temporaire, rapporter les
appels, les décisions identifiées/téléchargées/scannées/en échec, les
plafonds et la méthode de tokens. Ne jamais committer identifiants,
`.env`, corpus, journaux ou rapports générés.

## Definition of done

Démarrage autonome, schémas = handlers = CLI, tests hors réseau verts,
stdout = résultat de commande, échecs explicites, aucune dépendance à un
installateur parent.
