import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import legifrance as cli  # noqa: E402
from test_cli import run_cli  # noqa: E402
from tools import credentials  # noqa: E402


NOMS = (
    "LEGIFRANCE_CLIENT_ID",
    "LEGIFRANCE_CLIENT_SECRET",
    "LEGIFRANCE_CLIENT_ID_PLUGIN",
    "LEGIFRANCE_CLIENT_SECRET_PLUGIN",
    "LEGIFRANCE_ENV",
    "LEGIFRANCE_ENV_FILE",
)


class CredentialsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env_file = Path(self.tmp.name) / ".env"
        self.env_patch = patch.dict(
            os.environ,
            {nom: "" for nom in NOMS} | {"LEGIFRANCE_ENV_FILE": str(self.env_file)},
            clear=False,
        )
        self.env_patch.start()
        for nom in NOMS:
            if nom != "LEGIFRANCE_ENV_FILE":
                os.environ.pop(nom, None)

    def tearDown(self):
        self.env_patch.stop()
        self.tmp.cleanup()

    def test_setup_sans_identifiants_imprime_le_guide_et_echoue(self):
        code, stdout, stderr = run_cli(["setup"])
        self.assertEqual(code, 1)
        self.assertIn("https://piste.gouv.fr/registration", stdout)
        self.assertIn("client_id: manquant", stdout)
        self.assertIn("action: python3 scripts/legifrance.py setup", stdout)
        self.assertEqual(stderr, "")
        self.assertFalse(self.env_file.exists())

    def test_setup_enregistre_sans_afficher_le_secret(self):
        secret = "s3cret-valeur-unique"
        code, stdout, stderr = run_cli([
            "setup",
            "--client-id", "id-exemple",
            "--client-secret", secret,
            "--env", "production",
        ])
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertNotIn(secret, stdout)
        self.assertIn("permissions 600", stdout)
        self.assertIn("client_id: configuré", stdout)
        self.assertTrue(self.env_file.is_file())
        self.assertEqual(stat.S_IMODE(self.env_file.stat().st_mode), 0o600)
        text = self.env_file.read_text(encoding="utf-8")
        self.assertIn("LEGIFRANCE_CLIENT_ID=id-exemple", text)
        self.assertIn(f"LEGIFRANCE_CLIENT_SECRET={secret}", text)
        self.assertIn("LEGIFRANCE_ENV=production", text)

    def test_setup_refuse_un_secret_seul(self):
        code, stdout, stderr = run_cli(["setup", "--client-secret", "abc"])
        self.assertEqual(code, 2)
        self.assertIn("--client-id et --client-secret", stderr)
        self.assertFalse(self.env_file.exists())

    def test_setup_check_reussit_sans_exposer_le_jeton(self):
        class FakeResponse:
            ok = True
            status_code = 200
            reason = "OK"

            def json(self):
                return {"access_token": "jeton-secret", "expires_in": 3600}

        with patch("requests.post", return_value=FakeResponse()) as mocked:
            code, stdout, stderr = run_cli([
                "setup",
                "--client-id", "id-exemple",
                "--client-secret", "secret-exemple",
                "--check",
            ])
        self.assertEqual(code, 0)
        self.assertIn("Jeton OAuth obtenu", stdout)
        self.assertNotIn("jeton-secret", stdout)
        self.assertNotIn("secret-exemple", stdout)
        self.assertEqual(stderr, "")
        mocked.assert_called_once()
        self.assertEqual(
            mocked.call_args.args[0],
            "https://oauth.piste.gouv.fr/api/oauth/token",
        )

    def test_write_preserve_les_autres_cles(self):
        self.env_file.write_text("AUTRE=valeur\nLEGIFRANCE_CLIENT_ID=ancien\n", encoding="utf-8")
        credentials.write_credentials("nouveau", "secret", path=self.env_file)
        text = self.env_file.read_text(encoding="utf-8")
        self.assertIn("AUTRE=valeur", text)
        self.assertIn("LEGIFRANCE_CLIENT_ID=nouveau", text)
        self.assertNotIn("ancien", text)

    def test_aucun_fichier_mcp_n_est_relu(self):
        self.assertFalse(hasattr(credentials, "MCP_ENV_FILE"))
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "skill-legifrance"
            mcp_env = Path(tmp) / "mcp-legifrance" / ".env"
            skill_dir.mkdir()
            mcp_env.parent.mkdir()
            mcp_env.write_text(
                "LEGIFRANCE_CLIENT_ID=mcp-id\nLEGIFRANCE_CLIENT_SECRET=mcp-secret\n",
                encoding="utf-8",
            )
            skill_env = skill_dir / ".env"
            with patch.object(credentials, "DEFAULT_ENV_DIR", skill_dir), patch.object(
                credentials, "DEFAULT_ENV_FILE", skill_env
            ):
                os.environ.pop("LEGIFRANCE_ENV_FILE", None)
                os.environ.pop("LEGIFRANCE_CLIENT_ID", None)
                os.environ.pop("LEGIFRANCE_CLIENT_SECRET", None)
                self.assertEqual(credentials.env_file_candidates(), [skill_env])
                self.assertIsNone(credentials.resolved_env_file())
                self.assertEqual(credentials.target_env_file(), skill_env)
                self.assertEqual(credentials.read_env_file(), {})
                self.assertFalse(credentials.credentials_configured())


if __name__ == "__main__":
    unittest.main()
