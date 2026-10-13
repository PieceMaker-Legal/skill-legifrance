# Skill Legifrance

Skill autonome pour rechercher et consulter les sources juridiques
officielles françaises (Légifrance/PISTE, BODACC, lexique justice.fr) via
un script CLI. Les conclusions de droit restent à l'appelant.

Ce dépôt reprend le cœur métier de
[mcp-legifrance](https://github.com/PieceMaker-Legal/mcp-legifrance) et
remplace le transport MCP stdio par `scripts/legifrance.py`.

Le format suit la [spécification Agent Skills](https://agentskills.io/specification)
et le packaging [plugin Claude Code](https://code.claude.com/docs/en/skills) :
`SKILL.md` à la racine (`name: legifrance`), scripts dans `scripts/`,
manifestes dans `.claude-plugin/`.

## Installation Claude Code

Le dossier de la skill doit s'appeler `legifrance` (le champ `name` du
`SKILL.md`). Le dépôt GitHub s'appelle `skill-legifrance` ; cloner dans
un répertoire nommé `legifrance`.

### Plugin (recommandé)

Dans Claude Code :

```text
/plugin marketplace add PieceMaker-Legal/skill-legifrance
/plugin install legifrance@skill-legifrance
```

La commande est alors `/legifrance`.

### Skill personnelle

```sh
git clone https://github.com/PieceMaker-Legal/skill-legifrance.git \
  ~/.claude/skills/legifrance
```

Pour un projet : même clone dans `.claude/skills/legifrance`.

## Autres agents (Grok, etc.)

```sh
git clone https://github.com/PieceMaker-Legal/skill-legifrance.git \
  ~/.grok/skills/legifrance
```

## Client PISTE

Au premier appel, le script crée un `.venv` local et installe
`requirements.txt`. La mise en place du client PISTE est une commande
de la skill :

```sh
python3 scripts/legifrance.py setup
```

Le guide d'inscription PISTE s'affiche (compte, application, souscription
API Légifrance, client OAuth). Ensuite, avec les identifiants obtenus :

```sh
python3 scripts/legifrance.py setup \
  --client-id '…' --client-secret '…' --env production --check
```

Les identifiants sont écrits dans `~/.config/skill-legifrance/.env`
(permissions 600). On peut aussi exporter `LEGIFRANCE_CLIENT_ID` /
`LEGIFRANCE_CLIENT_SECRET`, ou poser `LEGIFRANCE_ENV_FILE`. Un fichier
`~/.config/mcp-legifrance/.env` déjà présent est relu. `list`, `ping`,
`--help`, `setup` et `dictionnaire_juridique` n'exigent pas d'identifiants.

Dans Claude Code, le dossier de la skill est `${CLAUDE_SKILL_DIR}` :

```sh
python3 ${CLAUDE_SKILL_DIR}/scripts/legifrance.py setup
```

## Usage

```sh
python3 scripts/legifrance.py Search_Cour_Cassation \
  --query '("faute grave" OU "faute lourde") ET licenciement' \
  --matiere SOCIAL
python3 scripts/legifrance.py consulter_decision --text_id JURITEXT000007000000
python3 scripts/legifrance.py Search_Code --query 'L. 1235-3'
```

La syntaxe des requêtes et le choix de commande sont dans `SKILL.md`.
Chaque commande reprend le schéma de `config/mcp_definitions.py` ;
`python3 scripts/legifrance.py <commande> --help` en est le contrat.

## Développement

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
python3 scripts/legifrance.py list
```

Les tests sont hors réseau. Ne jamais versionner `.env`, jetons, corpus
téléchargés, journaux ou rapports juridiques générés.
