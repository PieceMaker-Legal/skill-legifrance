# Skill Legifrance

Skill autonome pour rechercher et consulter les sources juridiques
officielles françaises (Légifrance/PISTE, BODACC, lexique justice.fr) via
un script CLI. Les conclusions de droit restent à l'appelant.

Ce dépôt reprend le cœur métier de
[mcp-legifrance](https://github.com/PieceMaker-Legal/mcp-legifrance) et
remplace le transport MCP stdio par `scripts/legifrance.py`.

## Installation

Cloner le dépôt dans un répertoire de skills, par exemple :

```sh
git clone https://github.com/PieceMaker-Legal/skill-legifrance.git \
  ~/.grok/skills/legifrance
```

Au premier appel, le script crée un `.venv` local et installe
`requirements.txt` :

```sh
python3 scripts/legifrance.py ping
python3 scripts/legifrance.py list
```

## Configuration

Créer `~/.config/skill-legifrance/.env` (permissions utilisateur) :

```dotenv
LEGIFRANCE_CLIENT_ID=...
LEGIFRANCE_CLIENT_SECRET=...
LEGIFRANCE_ENV=production
```

On peut aussi exporter ces variables, ou poser
`LEGIFRANCE_ENV_FILE=/chemin/absolu/.env`. Un fichier
`~/.config/mcp-legifrance/.env` déjà présent est relu. `list`, `ping`,
`--help` et `dictionnaire_juridique` n'exigent pas d'identifiants.

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
