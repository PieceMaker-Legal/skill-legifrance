import importlib
import os
import sys
import unittest
from unittest.mock import patch


ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

NOMS = (
    "LEGIFRANCE_CLIENT_ID",
    "LEGIFRANCE_CLIENT_SECRET",
    "LEGIFRANCE_CLIENT_ID_PLUGIN",
    "LEGIFRANCE_CLIENT_SECRET_PLUGIN",
)


def charger_settings(environnement):
    base = {nom: valeur for nom, valeur in os.environ.items() if nom not in NOMS}
    base.update(environnement)
    base["LEGIFRANCE_ENV_FILE"] = os.devnull
    with patch.dict(os.environ, base, clear=True), patch("dotenv.load_dotenv", return_value=False):
        sys.modules.pop("config.settings", None)
        return importlib.import_module("config.settings")


class IdentifiantsPluginTest(unittest.TestCase):
    def tearDown(self):
        sys.modules.pop("config.settings", None)

    def test_valeur_plugin_prioritaire(self):
        settings = charger_settings({
            "LEGIFRANCE_CLIENT_ID_PLUGIN": "id-exemple",
            "LEGIFRANCE_CLIENT_SECRET_PLUGIN": "secret-exemple",
            "LEGIFRANCE_CLIENT_ID": "id-environnement",
            "LEGIFRANCE_CLIENT_SECRET": "secret-environnement",
        })
        self.assertEqual(settings.LEGIFRANCE_CLIENT_ID, "id-exemple")
        self.assertEqual(settings.LEGIFRANCE_CLIENT_SECRET, "secret-exemple")

    def test_substitution_non_resolue_replie_sur_l_environnement(self):
        settings = charger_settings({
            "LEGIFRANCE_CLIENT_ID_PLUGIN": "${user_config.client_id}",
            "LEGIFRANCE_CLIENT_SECRET_PLUGIN": "${user_config.client_secret}",
            "LEGIFRANCE_CLIENT_ID": "id-exemple",
            "LEGIFRANCE_CLIENT_SECRET": "secret-exemple",
        })
        self.assertEqual(settings.LEGIFRANCE_CLIENT_ID, "id-exemple")
        self.assertEqual(settings.LEGIFRANCE_CLIENT_SECRET, "secret-exemple")

    def test_aucune_valeur(self):
        settings = charger_settings({})
        self.assertIsNone(settings.LEGIFRANCE_CLIENT_ID)
        self.assertIsNone(settings.LEGIFRANCE_CLIENT_SECRET)


if __name__ == "__main__":
    unittest.main()
