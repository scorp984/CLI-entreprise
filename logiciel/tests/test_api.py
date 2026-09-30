import unittest
import os
import tempfile
from io import BytesIO
from datetime import date
from unittest.mock import patch
from werkzeug.datastructures import MultiDict

from api.api import app, completed_years_since

SESSION_ACCOUNT_QUERY = "SELECT id, role, actif FROM comptes WHERE id = %s"


class FakeCursor:
    def __init__(self, rows, rowcount=0, responses=None):
        self.rows = rows
        self.rowcount = rowcount
        self.responses = responses or {}
        self.lastrowid = 42
        self.executed = []

    def execute(self, query, parameters=None):
        self.query = query
        self.parameters = parameters
        self.executed.append((query, parameters))
        if (query, parameters) in self.responses:
            self.rows = self.responses[(query, parameters)]
        elif query in self.responses:
            self.rows = self.responses[query]

    def executemany(self, query, parameters):
        self.executed.append((query, parameters))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows, rowcount=0, responses=None):
        self.rows = rows
        self.rowcount = rowcount
        self.responses = responses or {}
        self.executed = []

    def cursor(self, dictionary=False):
        cursor = FakeCursor(self.rows, self.rowcount, self.responses)
        cursor.executed = self.executed
        return cursor

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class TestGetEmployes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def connecter_comme(self, role):
        with self.client.session_transaction() as session:
            session["compte_id"] = 1
            session["role"] = role

    @patch("api.api.get_connection", return_value=FakeConnection([]))
    def test_get_employes_refuse_les_visiteurs_non_connectes(self, mock_get_connection):
        response = self.client.get("/employes")

        self.assertEqual(response.status_code, 401)
        mock_get_connection.assert_not_called()

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "comptable", "actif": 1}],
    }))
    def test_get_employes_refuse_les_roles_sans_acces_lecture(self, mock_get_connection):
        self.connecter_comme("comptable")

        response = self.client.get("/employes")

        self.assertEqual(response.status_code, 403)
        mock_get_connection.assert_called_once()

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 0}],
    }))
    def test_get_employes_refuse_un_compte_desactive(self, mock_get_connection):
        self.connecter_comme("pdg")

        response = self.client.get("/employes")

        self.assertEqual(response.status_code, 401)

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "manager", "actif": 1}],
        "SELECT * FROM employes": [],
    }))
    def test_get_employes_autorise_le_manager(self, mock_get_connection):
        self.connecter_comme("manager")

        response = self.client.get("/employes")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "manager", "actif": 1}],
    }))
    def test_get_employes_retourne_du_json(self, mock_get_connection):
        self.connecter_comme("pdg")
        employes = [
            {"nom": "Dupont", "prenom": "Jean", "poste": "Développeur", "salaire": 2500},
            {"nom": "Martin", "prenom": "Claire", "poste": "Designer", "salaire": 2200},
        ]
        mock_get_connection.return_value = FakeConnection(employes, responses={
            (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}],
        })

        response = self.client.get("/employes")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), employes)

    @patch("api.api.get_connection", return_value=None)
    def test_get_employes_retourne_500_si_connexion_impossible(self, mock_get_connection):
        self.connecter_comme("pdg")
        response = self.client.get("/employes")

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.get_json(),
            {"error": "Erreur de connexion à la base de données"},
        )


class TestCreateAccount(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def connecter_comme_pdg(self):
        with self.client.session_transaction() as session:
            session["compte_id"] = 1
            session["role"] = "pdg"

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}],
    }))
    def test_inscription_publique_est_refusee(self, mock_get_connection):
        response = self.client.post("/auth/comptes", json={
            "identifiant": "nouveau-pdg",
            "mot_de_passe": "secret",
            "role": "pdg",
            "nom": "Test",
            "prenom": "Compte",
            "poste": "manager",
            "date_embauche": "2026-01-01",
            "salaire": 2500,
        })

        self.assertEqual(response.status_code, 401)
        mock_get_connection.assert_not_called()

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}],
    }))
    def test_un_pdg_ne_peut_pas_creer_un_autre_pdg_par_le_formulaire(self, mock_get_connection):
        self.connecter_comme_pdg()
        response = self.client.post("/auth/comptes", json={
            "identifiant": "nouveau-pdg",
            "mot_de_passe": "secret",
            "role": "pdg",
            "nom": "Test",
            "prenom": "Compte",
            "poste": "manager",
            "date_embauche": "2026-01-01",
            "salaire": 2500,
        })

        self.assertEqual(response.status_code, 400)
        mock_get_connection.assert_called_once()

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}],
    }))
    def test_inscription_accepte_un_salaire_nul(self, mock_get_connection):
        self.connecter_comme_pdg()
        response = self.client.post("/auth/comptes", json={
            "identifiant": "nouveau-manager",
            "mot_de_passe": "secret",
            "role": "manager",
            "nom": "Test",
            "prenom": "Compte",
            "poste": "manager",
            "date_embauche": "2026-01-01",
            "salaire": 0,
        })

        self.assertEqual(response.status_code, 201)
        self.assertTrue(any(
            query == "UPDATE comptes SET employe_id = %s WHERE id = %s"
            and parameters == (42, 42)
            for query, parameters in mock_get_connection.return_value.executed
        ))


class TestAccountManagement(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["compte_id"] = 1
            session["role"] = "pdg"

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "manager", "actif": 1}],
    }))
    def test_liste_comptes_refuse_les_visiteurs(self, mock_get_connection):
        with self.client.session_transaction() as session:
            session.clear()

        response = self.client.get("/auth/comptes")

        self.assertEqual(response.status_code, 401)
        mock_get_connection.assert_not_called()

    @patch("api.api.get_connection", return_value=FakeConnection([
        {"id": 2, "identifiant": "manager01", "role": "manager", "actif": 1,
         "date_creation": "2026-01-01"}
    ], responses={(SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}]}))
    def test_liste_comptes_ne_retourne_que_les_champs_publics(self, mock_get_connection):
        response = self.client.get("/auth/comptes")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["identifiant"], "manager01")
        self.assertNotIn("mot_de_passe", response.get_json()[0])

    @patch("api.api.get_connection", return_value=FakeConnection(
        [], responses={
            (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}],
            (SESSION_ACCOUNT_QUERY, (2,)): [
                {"id": 2, "role": "manager", "actif": 1}
            ]
        }
    ))
    def test_modification_compte_acceptee(self, mock_get_connection):
        response = self.client.put("/auth/comptes/2", json={"role": "comptable"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"message": "Compte mis à jour avec succès"})

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}],
    }))
    def test_un_pdg_ne_peut_pas_supprimer_son_propre_compte(self, mock_get_connection):
        response = self.client.delete("/auth/comptes/1")

        self.assertEqual(response.status_code, 409)
        mock_get_connection.assert_called_once()

    @patch("api.api.get_connection", return_value=FakeConnection(
        [], responses={
            (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}],
            (SESSION_ACCOUNT_QUERY, (2,)): [
                {"id": 2, "role": "manager", "actif": 1}
            ]
        }
    ))
    def test_suppression_compte(self, mock_get_connection):
        response = self.client.delete("/auth/comptes/2")

        self.assertEqual(response.status_code, 200)

    @patch("api.api.get_connection", return_value=FakeConnection(
        [], responses={
            (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}],
            (SESSION_ACCOUNT_QUERY, (2,)): [{"id": 2, "role": "pdg", "actif": 1}],
            "SELECT COUNT(*) AS total FROM comptes WHERE role = 'pdg' AND actif = TRUE": [
                {"total": 1}
            ]
        }
    ))
    def test_impossible_de_supprimer_le_dernier_pdg_actif(self, mock_get_connection):
        response = self.client.delete("/auth/comptes/2")

        self.assertEqual(response.status_code, 409)


class TestManagerRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["compte_id"] = 1
            session["role"] = "manager"

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "manager", "actif": 1}],
        ("SELECT id, poste FROM employes WHERE id IN (%s)", (7,)): [
            {"id": 7, "poste": "developpeur"}
        ],
    }))
    def test_manager_attribue_projet_et_taches_par_defaut(self, mock_get_connection):
        response = self.client.post("/manager/projets", json={
            "employe_id": 7,
            "nom": "Refonte API",
            "date_debut": "2026-09-26",
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["id"], 42)
        self.assertTrue(any(
            query.startswith("INSERT INTO projets")
            for query, _ in mock_get_connection.return_value.executed
        ))
        self.assertTrue(any(
            query.startswith("INSERT INTO taches")
            for query, _ in mock_get_connection.return_value.executed
        ))

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "manager", "actif": 1}],
        ("SELECT id, poste FROM employes WHERE id IN (%s, %s)", (7, 8)): [
            {"id": 7, "poste": "developpeur"},
            {"id": 8, "poste": "developpeur"},
        ],
    }))
    def test_manager_cree_un_projet_pour_toute_l_equipe(self, mock_get_connection):
        response = self.client.post("/manager/projets", json={
            "employe_ids": [7, 8],
            "nom": "Refonte API",
            "taches": ["Développement"],
            "date_debut": "2026-09-26",
        })

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["employe_ids"], [7, 8])
        self.assertTrue(any(
            query.startswith("INSERT INTO projet_developpeurs")
            and parameters == [(42, 7), (42, 8)]
            for query, parameters in mock_get_connection.return_value.executed
        ))
        self.assertTrue(any(
            query.startswith("INSERT INTO taches (projet_id, employe_id, description)")
            and parameters == [(42, 7, "Développement")]
            for query, parameters in mock_get_connection.return_value.executed
        ))

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "manager", "actif": 1}],
    }))
    def test_manager_refuse_une_equipe_sans_tache_pour_chaque_membre(self, mock_get_connection):
        response = self.client.post("/manager/projets", json={
            "employe_ids": [7, 8],
            "nom": "Refonte API",
            "taches": [{"employe_id": 7, "description": "Développement"}],
            "date_debut": "2026-09-26",
        })

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json()["error"],
            "Chaque développeur sélectionné doit avoir au moins une tâche",
        )
        mock_get_connection.assert_called_once()

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "comptable", "actif": 1}],
    }))
    def test_creation_projet_refuse_les_roles_non_manager(self, mock_get_connection):
        response = self.client.post("/manager/projets", json={})

        self.assertEqual(response.status_code, 403)

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "manager", "actif": 1}],
        ("SELECT id, nom, prenom, poste, date_embauche FROM employes WHERE id = %s", (7,)): [
            {
                "id": 7,
                "nom": "Martin",
                "prenom": "Camille",
                "poste": "developpeur",
                "date_embauche": date.today(),
            }
        ],
        (
            "SELECT competences, disponibilite, experience_avant_embauche "
            "FROM fiches_techniques_developpeurs WHERE employe_id = %s",
            (7,),
        ): [{
            "competences": "Python",
            "disponibilite": "Temps plein",
            "experience_avant_embauche": 3.0,
        }],
        "SELECT p.id AS projet_id, p.nom, p.date_debut, p.statut, membre.id AS membre_id, membre.nom AS membre_nom, membre.prenom AS membre_prenom, t.id AS tache_id, t.description AS tache, affecte.id AS affecte_id, affecte.nom AS affecte_nom, affecte.prenom AS affecte_prenom FROM projet_developpeurs pd JOIN projets p ON p.id = pd.projet_id JOIN projet_developpeurs equipe ON equipe.projet_id = p.id JOIN employes membre ON membre.id = equipe.employe_id LEFT JOIN taches t ON t.projet_id = p.id AND (t.employe_id = %s OR t.employe_id IS NULL) LEFT JOIN employes affecte ON affecte.id = t.employe_id WHERE pd.employe_id = %s ORDER BY p.id, t.id": [],
    }))
    def test_fiche_developpeur_retourne_ses_projets(self, mock_get_connection):
        response = self.client.get("/manager/developpeurs/7/fiche")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["prenom"], "Camille")
        self.assertEqual(response.get_json()["projets"], [])
        self.assertEqual(
            response.get_json()["fiche_technique"]["experience_totale_annees"],
            3.0,
        )

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "manager", "actif": 1}],
        (
            "SELECT e.id AS employe_id, e.nom AS nom_employe, e.prenom, "
            "p.id AS projet_id, p.nom AS nom_projet, "
            "t.id AS tache_id, t.description "
            "FROM employes e "
            "JOIN projet_developpeurs pd ON pd.employe_id = e.id "
            "JOIN projets p ON p.id = pd.projet_id "
            "JOIN taches t ON t.projet_id = p.id "
            "WHERE e.id = %s AND p.nom = %s AND t.description = %s "
            "AND e.poste = 'developpeur' "
            "AND (t.employe_id = e.id OR t.employe_id IS NULL)",
            (7, "Refonte API", "Développement"),
        ): [{
            "employe_id": 7,
            "nom_employe": "Martin",
            "prenom": "Camille",
            "projet_id": 3,
            "nom_projet": "Refonte API",
            "tache_id": 9,
            "description": "Développement",
        }],
    }))
    def test_recherche_qui_fait_quoi(self, mock_get_connection):
        response = self.client.get(
            "/manager/qui-fait-quoi?employe_id=7&projet=Refonte%20API&tache=D%C3%A9veloppement"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["projet_id"], 3)


class TestDeveloperTechnicalSheet(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["compte_id"] = 9
            session["role"] = "developpeur"

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (9,)): [
            {"id": 9, "role": "developpeur", "actif": 1}
        ],
        (
            "SELECT e.id, e.nom, e.prenom, e.date_embauche "
            "FROM comptes c JOIN employes e ON e.id = c.employe_id "
            "WHERE c.id = %s AND c.role = 'developpeur' AND e.poste = 'developpeur'",
            (9,),
        ): [{
            "id": 7,
            "nom": "Martin",
            "prenom": "Camille",
            "date_embauche": date.today(),
        }],
        (
            "SELECT competences, disponibilite, experience_avant_embauche, modifie_le "
            "FROM fiches_techniques_developpeurs WHERE employe_id = %s",
            (7,),
        ): [{
            "competences": "Python",
            "disponibilite": "Temps plein",
            "experience_avant_embauche": 2.0,
            "modifie_le": None,
        }],
        (
            "SELECT p.id AS projet_id, p.nom, p.date_debut, p.statut, "
            "membre.id AS membre_id, membre.nom AS membre_nom, "
            "membre.prenom AS membre_prenom, t.id AS tache_id, "
            "t.description AS tache, affecte.id AS affecte_id, "
            "affecte.nom AS affecte_nom, affecte.prenom AS affecte_prenom "
            "FROM projet_developpeurs pd "
            "JOIN projets p ON p.id = pd.projet_id "
            "JOIN projet_developpeurs equipe ON equipe.projet_id = p.id "
            "JOIN employes membre ON membre.id = equipe.employe_id "
            "LEFT JOIN taches t ON t.projet_id = p.id "
            "AND (t.employe_id = %s OR t.employe_id IS NULL) "
            "LEFT JOIN employes affecte ON affecte.id = t.employe_id "
            "WHERE pd.employe_id = %s ORDER BY p.id, t.id",
            (7, 7),
        ): [{
            "projet_id": 3,
            "nom": "Refonte API",
            "date_debut": date(2026, 9, 20),
            "statut": "En cours",
            "membre_id": 7,
            "membre_nom": "Martin",
            "membre_prenom": "Camille",
            "tache_id": 9,
            "tache": "Développement",
            "affecte_id": 7,
            "affecte_nom": "Martin",
            "affecte_prenom": "Camille",
        }],
    }))
    def test_get_fiche_retourne_experience_declaree_et_anciennete(self, mock_get_connection):
        response = self.client.get("/developpeur/fiche")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["fiche_complete"])
        self.assertEqual(response.get_json()["date_embauche"], date.today().isoformat())
        self.assertEqual(response.get_json()["experience_totale_annees"], 2.0)
        self.assertEqual(response.get_json()["projets"][0]["nom"], "Refonte API")
        self.assertEqual(response.get_json()["projets"][0]["date_debut"], "2026-09-20")
        self.assertEqual(response.get_json()["projets"][0]["taches"][0]["description"], "Développement")
        self.assertEqual(response.get_json()["projets"][0]["taches"][0]["assigne_a"]["id"], 7)
        self.assertEqual(response.get_json()["projets"][0]["developpeurs"][0]["id"], 7)

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (9,)): [
            {"id": 9, "role": "developpeur", "actif": 1}
        ],
        (
            "SELECT e.id, e.nom, e.prenom, e.date_embauche "
            "FROM comptes c JOIN employes e ON e.id = c.employe_id "
            "WHERE c.id = %s AND c.role = 'developpeur' AND e.poste = 'developpeur'",
            (9,),
        ): [{
            "id": 7,
            "nom": "Martin",
            "prenom": "Camille",
            "date_embauche": date.today(),
        }],
        (
            "SELECT employe_id FROM fiches_techniques_developpeurs WHERE employe_id = %s",
            (7,),
        ): [],
    }))
    def test_post_cree_la_fiche_pour_le_developpeur_connecte(self, mock_get_connection):
        response = self.client.post("/developpeur/fiche", json={
            "competences": "Python, SQL",
            "disponibilite": "Temps plein",
            "experience_avant_embauche": 2,
        })

        self.assertEqual(response.status_code, 201)
        self.assertTrue(any(
            query.startswith("INSERT INTO fiches_techniques_developpeurs")
            for query, _ in mock_get_connection.return_value.executed
        ))

    @patch("api.api.get_connection", return_value=FakeConnection([], responses={
        (SESSION_ACCOUNT_QUERY, (9,)): [
            {"id": 9, "role": "developpeur", "actif": 1}
        ],
        (
            "SELECT e.id, e.nom, e.prenom, e.date_embauche "
            "FROM comptes c JOIN employes e ON e.id = c.employe_id "
            "WHERE c.id = %s AND c.role = 'developpeur' AND e.poste = 'developpeur'",
            (9,),
        ): [{
            "id": 7,
            "nom": "Martin",
            "prenom": "Camille",
            "date_embauche": date.today(),
        }],
        (
            "SELECT employe_id FROM fiches_techniques_developpeurs WHERE employe_id = %s",
            (7,),
        ): [{"employe_id": 7}],
    }))
    def test_put_modifie_la_fiche_existante(self, mock_get_connection):
        response = self.client.put("/developpeur/fiche", json={
            "competences": "Python, SQL",
            "disponibilite": "Temps partiel",
            "experience_avant_embauche": 2,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(
            query.startswith("UPDATE fiches_techniques_developpeurs")
            for query, _ in mock_get_connection.return_value.executed
        ))

    def test_anciennete_n_augmente_qu_a_la_date_anniversaire(self):
        embauche = date(2024, 4, 15)

        self.assertEqual(completed_years_since(embauche, date(2026, 4, 14)), 1)
        self.assertEqual(completed_years_since(embauche, date(2026, 4, 15)), 2)


class TestUpdateEmploye(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["compte_id"] = 1
            session["role"] = "pdg"

    @patch("api.api.get_connection", return_value=FakeConnection([(1,)], rowcount=0, responses={
        (SESSION_ACCOUNT_QUERY, (1,)): [{"id": 1, "role": "pdg", "actif": 1}],
    }))
    def test_put_identique_ne_signale_pas_un_employe_absent(self, mock_get_connection):
        response = self.client.put("/employes/1", json={
            "nom": "Dupont",
            "prenom": "Jean",
            "poste": "manager",
            "date_embauche": "2024-01-01",
            "salaire": 2500,
        })

        self.assertEqual(response.status_code, 200)


class TestCors(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_preflight_autorise_live_server_sur_localhost(self):
        response = self.client.options("/auth/login", headers={
            "Origin": "http://localhost:5500",
            "Access-Control-Request-Method": "POST",
        })

        self.assertEqual(
            response.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:5500",
        )


class TestDeveloperProjectFiles(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["compte_id"] = 9
            session["role"] = "developpeur"

    def connection(self, extra_responses=None):
        responses = {
            (SESSION_ACCOUNT_QUERY, (9,)): [
                {"id": 9, "role": "developpeur", "actif": 1}
            ],
            (
                "SELECT e.id, e.nom, e.prenom, e.date_embauche "
                "FROM comptes c JOIN employes e ON e.id = c.employe_id "
                "WHERE c.id = %s AND c.role = 'developpeur' AND e.poste = 'developpeur'",
                (9,),
            ): [{"id": 7, "nom": "Martin", "prenom": "Camille"}],
            (
                "SELECT p.id FROM projets p "
                "JOIN projet_developpeurs pd ON pd.projet_id = p.id "
                "WHERE p.id = %s AND pd.employe_id = %s",
                (3, 7),
            ): [{"id": 3}],
        }
        responses.update(extra_responses or {})
        return FakeConnection([], responses=responses)

    def test_upload_stocke_le_fichier_hors_du_webroot_et_enregistre_ses_metadonnees(self):
        connection = self.connection()
        with tempfile.TemporaryDirectory() as storage_directory:
            with patch("api.api.PROJECT_FILES_DIRECTORY", storage_directory), \
                    patch("api.api.get_connection", return_value=connection):
                response = self.client.post(
                    "/developpeur/projets/3/fichiers",
                    data={
                        "etape": "diagramme",
                        "fichier": (BytesIO(b"contenu pdf"), "diagramme.pdf"),
                    },
                    content_type="multipart/form-data",
                )

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.get_json()["id"], 42)
            insert_query, insert_parameters = next(
                (query, parameters)
                for query, parameters in connection.executed
                if query.startswith("INSERT INTO fichiers_projets")
            )
            self.assertEqual(insert_parameters[:4], (3, 7, "diagramme", "diagramme.pdf"))
            self.assertTrue(os.path.isfile(os.path.join(storage_directory, insert_parameters[4])))

    def test_upload_enregistre_plusieurs_fichiers_dans_la_meme_etape(self):
        connection = self.connection()
        request_data = MultiDict([
            ("etape", "diagramme"),
            ("fichier", (BytesIO(b"pdf"), "diagramme.pdf")),
            ("fichier", (BytesIO(b"png"), "schema.png")),
        ])
        with tempfile.TemporaryDirectory() as storage_directory:
            with patch("api.api.PROJECT_FILES_DIRECTORY", storage_directory), \
                    patch("api.api.get_connection", return_value=connection):
                response = self.client.post(
                    "/developpeur/projets/3/fichiers",
                    data=request_data,
                    content_type="multipart/form-data",
                )

            insert_parameters = [
                parameters
                for query, parameters in connection.executed
                if query.startswith("INSERT INTO fichiers_projets")
            ]
            self.assertEqual(response.status_code, 201)
            self.assertEqual(len(insert_parameters), 2)
            self.assertEqual(
                {parameters[3] for parameters in insert_parameters},
                {"diagramme.pdf", "schema.png"},
            )
            self.assertEqual(len(os.listdir(storage_directory)), 2)

    def test_upload_refuse_un_projet_dont_le_developpeur_n_est_pas_membre(self):
        membership_query = (
            "SELECT p.id FROM projets p "
            "JOIN projet_developpeurs pd ON pd.projet_id = p.id "
            "WHERE p.id = %s AND pd.employe_id = %s"
        )
        connection = self.connection({(membership_query, (3, 7)): []})
        with patch("api.api.get_connection", return_value=connection):
            response = self.client.post(
                "/developpeur/projets/3/fichiers",
                data={
                    "etape": "diagramme",
                    "fichier": (BytesIO(b"contenu"), "diagramme.pdf"),
                },
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(any(
            query.startswith("INSERT INTO fichiers_projets")
            for query, _ in connection.executed
        ))

    def test_telechargement_est_limite_aux_membres_et_renvoie_le_fichier(self):
        storage_name = "fichier_test.pdf"
        file_query = (
            "SELECT id, projet_id, employe_id, nom_original, nom_stockage, "
            "type_mime, supprime_le FROM fichiers_projets WHERE id = %s"
        )
        connection = self.connection({
            (file_query, (12,)): [{
                "id": 12,
                "projet_id": 3,
                "employe_id": 7,
                "nom_original": "diagramme.pdf",
                "nom_stockage": storage_name,
                "type_mime": "application/pdf",
                "supprime_le": None,
            }],
        })
        with tempfile.TemporaryDirectory() as storage_directory:
            with open(os.path.join(storage_directory, storage_name), "wb") as stored_file:
                stored_file.write(b"contenu pdf")
            with patch("api.api.PROJECT_FILES_DIRECTORY", storage_directory), \
                    patch("api.api.get_connection", return_value=connection):
                response = self.client.get("/developpeur/fichiers/12")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, b"contenu pdf")
                self.assertIn("attachment", response.headers["Content-Disposition"])
                response.close()

    def test_suppression_conserve_la_trace_en_base(self):
        file_query = (
            "SELECT id, projet_id, employe_id, nom_original, nom_stockage, "
            "type_mime, supprime_le FROM fichiers_projets WHERE id = %s"
        )
        connection = self.connection({
            (file_query, (12,)): [{
                "id": 12,
                "projet_id": 3,
                "employe_id": 7,
                "nom_original": "diagramme.pdf",
                "nom_stockage": "fichier_test.pdf",
                "type_mime": "application/pdf",
                "supprime_le": None,
            }],
        })
        with patch("api.api.get_connection", return_value=connection):
            response = self.client.delete("/developpeur/fichiers/12")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(
            query.startswith("UPDATE fichiers_projets SET supprime_le")
            for query, _ in connection.executed
        ))

    def test_l_historique_retourne_les_fichiers_supprimes(self):
        list_query = (
            "SELECT id, etape, nom_original, taille, type_mime, ajoute_le, supprime_le "
            "FROM fichiers_projets WHERE projet_id = %s ORDER BY ajoute_le DESC, id DESC"
        )
        connection = self.connection({
            (list_query, (3,)): [{
                "id": 12,
                "etape": "diagramme",
                "nom_original": "diagramme.pdf",
                "taille": 120,
                "type_mime": "application/pdf",
                "ajoute_le": "2026-09-30 10:00:00",
                "supprime_le": "2026-09-30 11:00:00",
            }],
        })
        with patch("api.api.get_connection", return_value=connection):
            response = self.client.get("/developpeur/projets/3/fichiers")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["fichiers"][0]["id"], 12)
        self.assertIsNotNone(response.get_json()["fichiers"][0]["supprime_le"])

    def test_seul_l_auteur_peut_supprimer_un_fichier(self):
        file_query = (
            "SELECT id, projet_id, employe_id, nom_original, nom_stockage, "
            "type_mime, supprime_le FROM fichiers_projets WHERE id = %s"
        )
        connection = self.connection({
            (file_query, (12,)): [{
                "id": 12,
                "projet_id": 3,
                "employe_id": 11,
                "nom_original": "diagramme.pdf",
                "nom_stockage": "fichier_test.pdf",
                "type_mime": "application/pdf",
                "supprime_le": None,
            }],
        })
        with patch("api.api.get_connection", return_value=connection):
            response = self.client.delete("/developpeur/fichiers/12")

        self.assertEqual(response.status_code, 403)
        self.assertFalse(any(
            query.startswith("UPDATE fichiers_projets SET supprime_le")
            for query, _ in connection.executed
        ))


class TestManagerProjectFiles(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with self.client.session_transaction() as session:
            session["compte_id"] = 1
            session["role"] = "manager"

    def connection(self, extra_responses=None):
        responses = {
            (SESSION_ACCOUNT_QUERY, (1,)): [
                {"id": 1, "role": "manager", "actif": 1}
            ],
        }
        responses.update(extra_responses or {})
        return FakeConnection([], responses=responses)

    def test_manager_liste_les_fichiers_et_le_deposant_du_projet(self):
        project_query = "SELECT id FROM projets WHERE id = %s"
        files_query = (
            "SELECT f.id, f.etape, f.nom_original, f.taille, f.type_mime, "
            "f.ajoute_le, f.supprime_le, e.nom AS employe_nom, "
            "e.prenom AS employe_prenom "
            "FROM fichiers_projets f JOIN employes e ON e.id = f.employe_id "
            "WHERE f.projet_id = %s ORDER BY f.ajoute_le DESC, f.id DESC"
        )
        connection = self.connection({
            (project_query, (3,)): [{"id": 3}],
            (files_query, (3,)): [{
                "id": 12,
                "etape": "diagramme",
                "nom_original": "diagramme.pdf",
                "taille": 120,
                "type_mime": "application/pdf",
                "ajoute_le": "2026-09-30 10:00:00",
                "supprime_le": None,
                "employe_nom": "Martin",
                "employe_prenom": "Camille",
            }],
        })
        with patch("api.api.get_connection", return_value=connection):
            response = self.client.get("/manager/projets/3/fichiers")

        self.assertEqual(response.status_code, 200)
        fichier = response.get_json()["fichiers"][0]
        self.assertEqual(fichier["depose_par"], "Camille Martin")
        self.assertEqual(fichier["url"], "/manager/fichiers/12")

    def test_manager_telecharge_un_fichier_actif(self):
        file_query = (
            "SELECT nom_original, nom_stockage, type_mime, supprime_le "
            "FROM fichiers_projets WHERE id = %s"
        )
        connection = self.connection({
            (file_query, (12,)): [{
                "nom_original": "diagramme.pdf",
                "nom_stockage": "fichier_test.pdf",
                "type_mime": "application/pdf",
                "supprime_le": None,
            }],
        })
        with tempfile.TemporaryDirectory() as storage_directory:
            with open(os.path.join(storage_directory, "fichier_test.pdf"), "wb") as stored_file:
                stored_file.write(b"document transmis au manager")
            with patch("api.api.PROJECT_FILES_DIRECTORY", storage_directory), \
                    patch("api.api.get_connection", return_value=connection):
                response = self.client.get("/manager/fichiers/12")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, b"document transmis au manager")
                response.close()


if __name__ == "__main__":
    unittest.main()
