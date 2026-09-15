import unittest
from unittest.mock import patch

from api.api import app


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, query, parameters=None):
        self.query = query
        self.parameters = parameters

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows

    def cursor(self, dictionary=False):
        return FakeCursor(self.rows)

    def close(self):
        pass


class TestGetEmployes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @patch("api.api.get_connection")
    def test_get_employes_retourne_du_json(self, mock_get_connection):
        employes = [
            {"nom": "Dupont", "prenom": "Jean", "poste": "Développeur", "salaire": 2500},
            {"nom": "Martin", "prenom": "Claire", "poste": "Designer", "salaire": 2200},
        ]
        mock_get_connection.return_value = FakeConnection(employes)

        response = self.client.get("/employes")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), employes)

    @patch("api.api.get_connection", return_value=None)
    def test_get_employes_retourne_500_si_connexion_impossible(self, mock_get_connection):
        response = self.client.get("/employes")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json(),
            {"error": "Erreur de connexion à la base de données"},
        )


if __name__ == "__main__":
    unittest.main()
