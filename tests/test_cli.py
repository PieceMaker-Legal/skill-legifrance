import io
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch


ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import legifrance as cli  # noqa: E402

from config.mcp_definitions import INITIALIZE_INSTRUCTIONS, MCP_TOOLS  # noqa: E402
from tools.handlers import TOOL_HANDLERS  # noqa: E402


def run_cli(argv):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = cli.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class CliTest(unittest.TestCase):
    def test_list_sans_identifiants(self):
        code, stdout, stderr = run_cli(["list"])
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        names = {line.split("\t", 1)[0] for line in stdout.splitlines() if line.strip()}
        announced = {tool["name"] for tool in MCP_TOOLS}
        self.assertEqual(names, announced)
        self.assertIn("Formule une seule requête", INITIALIZE_INSTRUCTIONS)

    def test_ping(self):
        code, stdout, stderr = run_cli(["ping"])
        self.assertEqual(code, 0)
        self.assertEqual(stdout, "ok\n")
        self.assertEqual(stderr, "")

    def test_aide_globale_sans_identifiants(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        parser = cli.build_parser()
        with self.assertRaises(SystemExit) as caught:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                parser.parse_args(["--help"])
        self.assertEqual(caught.exception.code, 0)
        help_text = stdout.getvalue() + stderr.getvalue()
        self.assertIn("Search_Cour_Cassation", help_text)
        self.assertIn("Formule une seule requête", help_text)
        self.assertNotIn("LEGIFRANCE_CLIENT_SECRET", help_text)

    def test_chaque_commande_annoncee_possede_un_handler(self):
        announced = {tool["name"] for tool in MCP_TOOLS}
        self.assertEqual(announced - set(TOOL_HANDLERS), set())

    def test_commande_inconnue_est_rejetee(self):
        parser = cli.build_parser()
        stderr = io.StringIO()
        with self.assertRaises(SystemExit) as caught:
            with redirect_stderr(stderr):
                parser.parse_args(["recherche_jurisprudence"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("invalid choice", stderr.getvalue())

    def test_matiere_obligatoire_sur_la_cli(self):
        parser = cli.build_parser()
        stderr = io.StringIO()
        with self.assertRaises(SystemExit) as caught:
            with redirect_stderr(stderr):
                parser.parse_args(["Search_Cour_Cassation", "--query", "révocation"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--matiere", stderr.getvalue())

    def test_tableau_accepte_une_liste_separee_par_des_virgules(self):
        parser = cli.build_parser()
        namespace = parser.parse_args([
            "Search_Cour_Cassation",
            "--query", "révocation",
            "--matiere", "CIVIL,COMMERCIAL",
        ])
        arguments = cli.arguments_from_namespace(namespace, namespace._schema)
        self.assertEqual(arguments["matiere"], ["CIVIL", "COMMERCIAL"])
        self.assertEqual(arguments["query"], "révocation")

    def test_consulter_decision_longue_rend_le_texte_integral(self):
        texte_integral = "MOYENS ANNEXES\n" + "Texte officiel intégral. " * 5_100
        with patch(
            "tools.handlers.legifrance_client.get_decision_text",
            return_value={"text": {
                "titre": "Arrêt de test",
                "nature": "REJET",
                "texte": texte_integral,
            }},
        ):
            code, stdout, stderr = run_cli([
                "consulter_decision",
                "--text_id", "JURITEXTLONGUE",
            ])

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertIn("JURITEXTLONGUE", stdout)
        self.assertIn(texte_integral, stdout)
        self.assertNotIn("blob", stdout)

    def test_json_rend_la_reponse_handler(self):
        with patch(
            "tools.handlers.justice_lexicon_client.lookup",
            return_value={"definition": "définition de test", "suggestions": None},
        ):
            code, stdout, stderr = run_cli([
                "dictionnaire_juridique",
                "--terme", "cassation",
                "--json",
            ])
        self.assertEqual(code, 0)
        payload = json.loads(stdout)
        self.assertIn("content", payload)
        self.assertFalse(payload.get("isError"))


if __name__ == "__main__":
    unittest.main()
