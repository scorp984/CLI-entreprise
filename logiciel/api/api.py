"""API Flask de gestion des comptes et des employés.

Ce fichier contient les routes HTTP utilisées par le frontend : connexion,
déconnexion, gestion du compte courant et gestion des employés.
"""

from functools import wraps  # Conserve le nom de la fonction quand on crée un décorateur.
from datetime import date, datetime
import mimetypes
import math
import os  # Permet de lire les variables de configuration du système.
import uuid

# Flask fournit le serveur web et les outils pour créer des routes HTTP.
# jsonify transforme automatiquement des dictionnaires Python en réponses JSON.
# request contient les données envoyées par le frontend.
# session conserve temporairement l'identité de l'utilisateur connecté.
from flask import Flask, jsonify, request, send_file, session
from werkzeug.utils import secure_filename

# Ces fonctions servent à protéger les mots de passe dans la base de données.
from werkzeug.security import check_password_hash, generate_password_hash
from mysql.connector.errors import IntegrityError

import sys  # Donne accès à la liste des chemins où Python cherche les modules.

# Ajoute le dossier parent pour pouvoir importer le module database.data.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Fonction du projet qui ouvre une connexion avec la base de données.
from database.data import get_connection

# La clé secrète sert à signer les cookies de session Flask.
# En production, elle doit être définie dans une variable d'environnement.
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-a-remplacer")
PROJECT_FILES_DIRECTORY = os.path.abspath(os.environ.get(
    "PROJECT_FILES_DIRECTORY",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "fichiers_projets"),
))
PROJECT_FILE_MAX_BYTES = 25 * 1024 * 1024
PROJECT_FILE_EXTENSIONS = {
    "diagramme": {".png", ".jpg", ".jpeg", ".pdf"},
    "dossier": {".zip", ".rar", ".7z"},
    "compte-rendu": {".pdf", ".docx"},
}
app.config["MAX_CONTENT_LENGTH"] = PROJECT_FILE_MAX_BYTES


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"error": "Le fichier dépasse la limite de 25 Mo"}), 413


def get_session_account():
    """Recharge le compte courant pour appliquer immédiatement ses changements d'état."""
    conn = get_connection()
    if conn is None:
        return None, True

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, role, actif FROM comptes WHERE id = %s",
            (session["compte_id"],),
        )
        return cursor.fetchone(), False
    except Exception:
        app.logger.exception("Erreur lors de la vérification de la session")
        return None, True
    finally:
        cursor.close()
        conn.close()


def completed_years_since(start_date, today=None):
    """Retourne le nombre d'anniversaires d'embauche déjà atteints."""
    if isinstance(start_date, str):
        start_date = date.fromisoformat(start_date)
    today = today or date.today()
    return today.year - start_date.year - (
        (today.month, today.day) < (start_date.month, start_date.day)
    )


def iso_date(value):
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(str(value)).isoformat()


def pdg_required(view):
    """Autorise uniquement un compte connecté avec le rôle PDG."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        # Le rôle est enregistré dans la session après une connexion réussie.
        if "compte_id" not in session:
            return jsonify({"error": "Vous devez être connecté"}), 401
        compte, erreur_connexion = get_session_account()
        if erreur_connexion:
            return jsonify({"error": "Erreur de connexion à la base de données"}), 500
        if compte is None or not compte["actif"]:
            session.clear()
            return jsonify({"error": "Vous devez être connecté"}), 401
        session["role"] = compte["role"]
        if compte["role"] != "pdg":
            return jsonify({"error": "Accès réservé au PDG"}), 403
        return view(*args, **kwargs)

    return wrapped


def pdg_or_manager_required(view):
    """Autorise la lecture des données aux comptes PDG et manager."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "compte_id" not in session:
            return jsonify({"error": "Vous devez être connecté"}), 401
        compte, erreur_connexion = get_session_account()
        if erreur_connexion:
            return jsonify({"error": "Erreur de connexion à la base de données"}), 500
        if compte is None or not compte["actif"]:
            session.clear()
            return jsonify({"error": "Vous devez être connecté"}), 401
        session["role"] = compte["role"]
        if compte["role"] not in {"pdg", "manager"}:
            return jsonify({"error": "Accès réservé au PDG ou au manager"}), 403
        return view(*args, **kwargs)

    return wrapped


def developer_required(view):
    """Autorise uniquement un compte développeur actif et connecté."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "compte_id" not in session:
            return jsonify({"error": "Vous devez être connecté"}), 401
        compte, erreur_connexion = get_session_account()
        if erreur_connexion:
            return jsonify({"error": "Erreur de connexion à la base de données"}), 500
        if compte is None or not compte["actif"]:
            session.clear()
            return jsonify({"error": "Vous devez être connecté"}), 401
        session["role"] = compte["role"]
        if compte["role"] != "developpeur":
            return jsonify({"error": "Accès réservé au développeur"}), 403
        return view(*args, **kwargs)

    return wrapped


# Cette route reçoit les identifiants envoyés par le frontend.
# POST signifie que le frontend envoie des données au serveur.
@app.route("/auth/login", methods=["POST"])
def login():
    """Vérifie les identifiants et ouvre une session utilisateur."""
    # Lit le corps JSON de la requête, par exemple :
    # {"identifiant": "alice", "mot_de_passe": "secret"}.
    # silent=True évite une erreur Flask si le JSON est absent ou invalide.
    data = request.get_json(silent=True)

    # Vérifie que nous avons bien reçu un objet JSON et deux champs non vides.
    # Le code 400 signifie : la requête envoyée par le client est incorrecte.
    if not isinstance(data, dict) or not data.get("identifiant") or not data.get("mot_de_passe"):
        return jsonify({"error": "Identifiant et mot de passe obligatoires"}), 400

    # On ouvre une connexion uniquement après avoir validé les données reçues.
    conn = get_connection()
    # Si la connexion échoue, inutile de continuer la requête SQL.
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    # dictionary=True permet d'accéder aux résultats avec des noms de colonnes,
    # par exemple compte["role"], plutôt qu'avec des positions numériques.
    cursor = conn.cursor(dictionary=True)
    # Les paramètres SQL sont séparés de la requête pour éviter l'injection SQL.
    cursor.execute(
        "SELECT id, identifiant, mot_de_passe, role, actif "
        "FROM comptes WHERE identifiant = %s",
        (data["identifiant"],),
    )
    # Récupère un seul compte correspondant à l'identifiant.
    compte = cursor.fetchone()

    # Il est important de fermer le curseur et la connexion après utilisation.
    cursor.close()
    conn.close()

    # On refuse aussi les comptes désactivés, même si le mot de passe est correct.
    if (
        compte is None
        or not compte["actif"]
        or not check_password_hash(compte["mot_de_passe"], data["mot_de_passe"])
    ):
        # 401 signifie : l'utilisateur n'est pas authentifié correctement.
        return jsonify({"error": "Identifiant ou mot de passe incorrect"}), 401

    # Flask stocke ces informations dans une session associée au navigateur.
    session["compte_id"] = compte["id"]
    session["role"] = compte["role"]
    # Envoie une réponse JSON au frontend.
    # 200 signifie que l'opération s'est déroulée correctement.
    return jsonify({
        "message": "Connexion réussie",
        "compte": {
            "id": compte["id"],
            "identifiant": compte["identifiant"],
            "role": compte["role"],
        },
    }), 200


@app.route("/auth/logout", methods=["POST"])
def logout():
    """Ferme la session de l'utilisateur actuellement connecté."""
    # Supprime toutes les informations de connexion enregistrées par Flask.
    session.clear()
    return jsonify({"message": "Déconnexion réussie"}), 200


@app.route("/auth/me", methods=["GET"])
def current_account():
    """Retourne les informations minimales du compte connecté."""
    # L'absence de compte_id signifie qu'aucune connexion n'est active.
    if "compte_id" not in session:
        return jsonify({"error": "Vous devez être connecté"}), 401

    compte, erreur_connexion = get_session_account()
    if erreur_connexion:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    if compte is None or not compte["actif"]:
        session.clear()
        return jsonify({"error": "Vous devez être connecté"}), 401

    # Retourne uniquement les informations utiles, sans envoyer le mot de passe.
    session["role"] = compte["role"]
    return jsonify({"id": compte["id"], "role": compte["role"]}), 200


@app.route("/auth/comptes", methods=["GET"])
@pdg_required
def get_comptes():
    """Retourne les comptes sans exposer leurs mots de passe hashes."""
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, identifiant, role, actif, date_creation "
            "FROM comptes ORDER BY identifiant"
        )
        return jsonify(cursor.fetchall()), 200
    except Exception:
        app.logger.exception("Erreur lors de la récupération des comptes")
        return jsonify({"error": "Erreur lors de la récupération des comptes"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/auth/comptes", methods=["POST"])
@pdg_required
def create_account():
    """Crée un compte et l'employé associé dans une même opération."""
    # Cette route reprend le même principe : le frontend envoie un objet JSON.
    data = request.get_json(silent=True)
    # Cette liste limite les rôles acceptés par l'API.
    roles = {"manager", "comptable", "developpeur"}
    # Un corps JSON est obligatoire pour créer un compte.
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps JSON est obligatoire"}), 400

    # Les rôles autorisés correspondent aux rôles connus par l'application.
    employee_fields = ("nom", "prenom", "poste", "date_embauche", "salaire")
    # any(...) renvoie True dès qu'un champ obligatoire est absent ou vide.
    if (
        not data.get("identifiant")
        or not data.get("mot_de_passe")
        or not isinstance(data.get("role"), str)
        or data.get("role") not in roles
        or any(data.get(field) is None or data.get(field) == "" for field in employee_fields)
        or not isinstance(data.get("salaire"), (int, float))
        or isinstance(data.get("salaire"), bool)
        or not math.isfinite(data.get("salaire"))
        or data.get("salaire") < 0
    ):
        return jsonify({"error": "Tous les champs du compte et de l'employé sont obligatoires"}), 400
    # Un rôle de compte et un poste d'employé sont deux notions différentes.
    # Ici, on vérifie que le poste métier est compatible avec l'application.
    if (
        not isinstance(data.get("poste"), str)
        or data["poste"] not in {"comptable", "developpeur", "manager"}
    ):
        return jsonify({"error": "Poste d'employé invalide"}), 400

    conn = get_connection()
    # Ouverture de la connexion seulement après validation des champs.
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    # Le curseur exécute les commandes SQL envoyées à la base.
    cursor = conn.cursor()
    try:
        # Le mot de passe est haché : on ne stocke jamais le mot de passe en clair.
        cursor.execute(
            "INSERT INTO comptes (identifiant, mot_de_passe, role) VALUES (%s, %s, %s)",
            (
                data["identifiant"],
                generate_password_hash(data["mot_de_passe"]),
                data["role"],
            ),
        )
        compte_id = cursor.lastrowid
        # Les deux insertions sont validées ensemble grâce à la transaction.
        cursor.execute(
            "INSERT INTO employes (nom, prenom, poste, date_embauche, salaire) VALUES (%s, %s, %s, %s, %s)",
            (
                data["nom"],
                data["prenom"],
                data["poste"],
                data["date_embauche"],
                data["salaire"],
            ),
        )
        employe_id = cursor.lastrowid
        cursor.execute(
            "UPDATE comptes SET employe_id = %s WHERE id = %s",
            (employe_id, compte_id),
        )
        # commit confirme définitivement les deux INSERT dans la base.
        conn.commit()
    except IntegrityError:
        # Si une insertion échoue, on annule aussi l'autre insertion.
        conn.rollback()
        return jsonify({"error": "Cet identifiant existe déjà"}), 409
    except Exception:
        conn.rollback()
        app.logger.exception("Erreur lors de la création du compte et de l'employé")
        return jsonify({"error": "Erreur lors de la création du compte"}), 500
    finally:
        # finally est exécuté même lorsqu'une erreur est rencontrée.
        # Cela garantit la fermeture des ressources de la base de données.
        cursor.close()
        conn.close()

    # 201 signifie qu'une nouvelle ressource a été créée.
    return jsonify({"message": "Compte créé avec succès"}), 201


@app.route("/auth/comptes/<int:compte_id>", methods=["PUT"])
@pdg_required
def update_account(compte_id):
    """Modifie l'identifiant, le rôle, le mot de passe ou l'état d'un compte."""
    data = request.get_json(silent=True)
    editable_fields = {"identifiant", "role", "mot_de_passe", "actif"}
    roles = {"manager", "comptable", "developpeur", "rh", "employe"}
    if not isinstance(data, dict) or not data or set(data) - editable_fields:
        return jsonify({"error": "Aucune modification valide fournie"}), 400
    if "identifiant" in data and (
        not isinstance(data["identifiant"], str) or not data["identifiant"].strip()
    ):
        return jsonify({"error": "L'identifiant est obligatoire"}), 400
    if "role" in data and (
        not isinstance(data["role"], str) or data["role"] not in roles
    ):
        return jsonify({"error": "Rôle invalide"}), 400
    if "mot_de_passe" in data and (
        not isinstance(data["mot_de_passe"], str) or not data["mot_de_passe"]
    ):
        return jsonify({"error": "Le mot de passe ne peut pas être vide"}), 400
    if "actif" in data and not isinstance(data["actif"], bool):
        return jsonify({"error": "L'état actif doit être un booléen"}), 400

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, role, actif FROM comptes WHERE id = %s",
            (compte_id,),
        )
        compte = cursor.fetchone()
        if compte is None:
            return jsonify({"error": "Compte introuvable"}), 404

        if compte_id == session["compte_id"] and (
            data.get("role", compte["role"]) != compte["role"]
            or data.get("actif") is False
        ):
            return jsonify({"error": "Vous ne pouvez pas désactiver ou changer votre propre rôle"}), 409

        nouveau_role = data.get("role", compte["role"])
        nouvel_etat = data.get("actif", bool(compte["actif"]))
        if compte["role"] == "pdg" and compte["actif"] and (
            nouveau_role != "pdg" or not nouvel_etat
        ):
            cursor.execute(
                "SELECT COUNT(*) AS total FROM comptes "
                "WHERE role = 'pdg' AND actif = TRUE"
            )
            nombre_pdgs_actifs = cursor.fetchone()["total"]
            if nombre_pdgs_actifs <= 1:
                return jsonify({"error": "Impossible de retirer le dernier compte PDG actif"}), 409

        updates = []
        parameters = []
        if "identifiant" in data:
            updates.append("identifiant = %s")
            parameters.append(data["identifiant"].strip())
        if "role" in data:
            updates.append("role = %s")
            parameters.append(data["role"])
        if "mot_de_passe" in data:
            updates.append("mot_de_passe = %s")
            parameters.append(generate_password_hash(data["mot_de_passe"]))
        if "actif" in data:
            updates.append("actif = %s")
            parameters.append(data["actif"])

        cursor.execute(
            f"UPDATE comptes SET {', '.join(updates)} WHERE id = %s",
            (*parameters, compte_id),
        )
        conn.commit()
    except IntegrityError:
        conn.rollback()
        return jsonify({"error": "Cet identifiant existe déjà"}), 409
    except Exception:
        conn.rollback()
        app.logger.exception("Erreur lors de la modification du compte")
        return jsonify({"error": "Erreur lors de la modification du compte"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Compte mis à jour avec succès"}), 200


@app.route("/auth/comptes/<int:compte_id>", methods=["DELETE"])
@pdg_required
def delete_account(compte_id):
    """Supprime un compte, sans toucher aux fiches employés non reliées."""
    if compte_id == session["compte_id"]:
        return jsonify({"error": "Vous ne pouvez pas supprimer votre propre compte"}), 409

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, role, actif FROM comptes WHERE id = %s",
            (compte_id,),
        )
        compte = cursor.fetchone()
        if compte is None:
            return jsonify({"error": "Compte introuvable"}), 404

        if compte["role"] == "pdg" and compte["actif"]:
            cursor.execute(
                "SELECT COUNT(*) AS total FROM comptes "
                "WHERE role = 'pdg' AND actif = TRUE"
            )
            if cursor.fetchone()["total"] <= 1:
                return jsonify({"error": "Impossible de supprimer le dernier compte PDG actif"}), 409

        cursor.execute("DELETE FROM comptes WHERE id = %s", (compte_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        app.logger.exception("Erreur lors de la suppression du compte")
        return jsonify({"error": "Erreur lors de la suppression du compte"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Compte supprimé avec succès"}), 200


# GET sert à demander des informations sans les modifier.
@app.route("/employes", methods=["GET"])
@pdg_or_manager_required
def get_employes():
    """Retourne la liste de tous les employés."""
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    # On demande des dictionnaires pour obtenir des objets JSON lisibles.
    cursor = conn.cursor(dictionary=True)
    # SELECT récupère les lignes de la table employes.
    cursor.execute("SELECT * FROM employes")
    # fetchall récupère toutes les lignes trouvées.
    employes = cursor.fetchall()
    cursor.close()
    conn.close()

    # Flask convertit la liste Python en tableau JSON.
    return jsonify(employes), 200


def get_linked_developer(cursor):
    cursor.execute(
        "SELECT e.id, e.nom, e.prenom, e.date_embauche "
        "FROM comptes c JOIN employes e ON e.id = c.employe_id "
        "WHERE c.id = %s AND c.role = 'developpeur' AND e.poste = 'developpeur'",
        (session["compte_id"],),
    )
    return cursor.fetchone()


@app.route("/developpeur/fiche", methods=["GET", "POST", "PUT"])
@developer_required
def developer_technical_sheet():
    """Lit ou enregistre la fiche du développeur associé à la session."""
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        developer = get_linked_developer(cursor)
        if developer is None:
            return jsonify({
                "error": "Ce compte développeur n'est pas encore associé à une fiche employé"
            }), 409

        if request.method == "GET":
            cursor.execute(
                "SELECT competences, disponibilite, experience_avant_embauche, modifie_le "
                "FROM fiches_techniques_developpeurs WHERE employe_id = %s",
                (developer["id"],),
            )
            profile = cursor.fetchone()
            experience_before_hire = (
                float(profile["experience_avant_embauche"])
                if profile is not None else None
            )
            tenure = completed_years_since(developer["date_embauche"])
            return jsonify({
                "employe_id": developer["id"],
                "nom": developer["nom"],
                "prenom": developer["prenom"],
                "date_embauche": iso_date(developer["date_embauche"]),
                "fiche_complete": profile is not None,
                "competences": profile["competences"] if profile else "",
                "disponibilite": profile["disponibilite"] if profile else "",
                "experience_avant_embauche": experience_before_hire,
                "anciennete_annees": tenure,
                "experience_totale_annees": (
                    experience_before_hire + tenure
                    if experience_before_hire is not None else None
                ),
                "modifie_le": profile["modifie_le"] if profile else None,
                "projets": fetch_developer_projects(cursor, developer["id"]),
            }), 200

        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "Le corps JSON est obligatoire"}), 400
        competences = data.get("competences")
        disponibilite = data.get("disponibilite")
        experience_before_hire = data.get("experience_avant_embauche")
        if (
            not isinstance(competences, str) or not competences.strip()
            or not isinstance(disponibilite, str) or not disponibilite.strip()
            or not isinstance(experience_before_hire, (int, float))
            or isinstance(experience_before_hire, bool)
            or not math.isfinite(experience_before_hire)
            or experience_before_hire < 0
        ):
            return jsonify({
                "error": "Compétences, disponibilité et expérience valide obligatoires"
            }), 400

        cursor.execute(
            "SELECT employe_id FROM fiches_techniques_developpeurs WHERE employe_id = %s",
            (developer["id"],),
        )
        profile_exists = cursor.fetchone() is not None
        if request.method == "POST" and profile_exists:
            return jsonify({"error": "La fiche existe déjà; utilisez PUT pour la modifier"}), 409
        if request.method == "PUT" and not profile_exists:
            return jsonify({"error": "Aucune fiche à modifier; utilisez POST pour la créer"}), 404

        if request.method == "POST":
            cursor.execute(
                "INSERT INTO fiches_techniques_developpeurs "
                "(employe_id, competences, disponibilite, experience_avant_embauche) "
                "VALUES (%s, %s, %s, %s)",
                (
                    developer["id"], competences.strip(), disponibilite.strip(),
                    experience_before_hire,
                ),
            )
        else:
            cursor.execute(
                "UPDATE fiches_techniques_developpeurs "
                "SET competences = %s, disponibilite = %s, experience_avant_embauche = %s "
                "WHERE employe_id = %s",
                (
                    competences.strip(), disponibilite.strip(),
                    experience_before_hire, developer["id"],
                ),
            )
        conn.commit()
        message = "Fiche technique enregistrée" if request.method == "POST" else "Fiche technique mise à jour"
        return jsonify({"message": message}), 201 if request.method == "POST" else 200
    except Exception:
        conn.rollback()
        app.logger.exception("Erreur lors de l'enregistrement de la fiche développeur")
        return jsonify({"error": "Erreur lors de l'enregistrement de la fiche développeur"}), 500
    finally:
        cursor.close()
        conn.close()


def developer_has_project_access(cursor, employe_id, projet_id):
    cursor.execute(
        "SELECT p.id FROM projets p "
        "JOIN projet_developpeurs pd ON pd.projet_id = p.id "
        "WHERE p.id = %s AND pd.employe_id = %s",
        (projet_id, employe_id),
    )
    return cursor.fetchone() is not None


def project_file_payload(fichier, download_path="/developpeur/fichiers"):
    payload = {
        "id": fichier["id"],
        "etape": fichier["etape"],
        "nom_original": fichier["nom_original"],
        "taille": fichier["taille"],
        "type_mime": fichier["type_mime"],
        "ajoute_le": fichier["ajoute_le"],
        "supprime_le": fichier["supprime_le"],
        "url": f"{download_path}/{fichier['id']}",
    }
    if "employe_nom" in fichier and "employe_prenom" in fichier:
        payload["depose_par"] = f"{fichier['employe_prenom']} {fichier['employe_nom']}"
    return payload


@app.route("/developpeur/projets/<int:projet_id>/fichiers", methods=["GET", "POST"])
@developer_required
def developer_project_files(projet_id):
    """Liste ou ajoute les fichiers d'un projet accessible au développeur."""
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    stored_paths = []
    try:
        developer = get_linked_developer(cursor)
        if developer is None:
            return jsonify({
                "error": "Ce compte développeur n'est pas encore associé à une fiche employé"
            }), 409
        if not developer_has_project_access(cursor, developer["id"], projet_id):
            return jsonify({"error": "Projet introuvable ou accès refusé"}), 404

        if request.method == "GET":
            cursor.execute(
                "SELECT id, etape, nom_original, taille, type_mime, ajoute_le, supprime_le "
                "FROM fichiers_projets WHERE projet_id = %s ORDER BY ajoute_le DESC, id DESC",
                (projet_id,),
            )
            return jsonify({
                "fichiers": [project_file_payload(row) for row in cursor.fetchall()]
            }), 200

        uploaded_files = request.files.getlist("fichier")
        etape = request.form.get("etape", "")
        if etape not in PROJECT_FILE_EXTENSIONS:
            return jsonify({"error": "Étape de dépôt invalide"}), 400
        if not uploaded_files or any(not fichier.filename for fichier in uploaded_files):
            return jsonify({"error": "Aucun fichier reçu"}), 400

        validated_files = []
        for uploaded_file in uploaded_files:
            original_name = secure_filename(uploaded_file.filename)
            extension = os.path.splitext(original_name)[1].lower()
            if not original_name or extension not in PROJECT_FILE_EXTENSIONS[etape]:
                return jsonify({"error": "Type de fichier non autorisé pour cette étape"}), 400

            uploaded_file.stream.seek(0, os.SEEK_END)
            file_size = uploaded_file.stream.tell()
            uploaded_file.stream.seek(0)
            if file_size == 0:
                return jsonify({"error": f"Le fichier {original_name} est vide"}), 400
            if file_size > PROJECT_FILE_MAX_BYTES:
                return jsonify({"error": f"Le fichier {original_name} dépasse la limite de 25 Mo"}), 413

            mime_type = mimetypes.guess_type(original_name)[0] or "application/octet-stream"
            validated_files.append((uploaded_file, original_name, extension, file_size, mime_type))

        os.makedirs(PROJECT_FILES_DIRECTORY, exist_ok=True)
        created_ids = []
        for uploaded_file, original_name, extension, file_size, mime_type in validated_files:
            stored_name = f"{uuid.uuid4().hex}{extension}"
            stored_path = os.path.join(PROJECT_FILES_DIRECTORY, stored_name)
            stored_paths.append(stored_path)
            uploaded_file.save(stored_path)
            cursor.execute(
                "INSERT INTO fichiers_projets "
                "(projet_id, employe_id, etape, nom_original, nom_stockage, type_mime, taille) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    projet_id, developer["id"], etape, original_name,
                    stored_name, mime_type, file_size,
                ),
            )
            created_ids.append(cursor.lastrowid)

        conn.commit()
        return jsonify({
            "message": f"{len(created_ids)} fichier(s) ajouté(s) au projet",
            "id": created_ids[0],
            "ids": created_ids,
        }), 201
    except Exception:
        conn.rollback()
        for stored_path in stored_paths:
            if os.path.isfile(stored_path):
                try:
                    os.remove(stored_path)
                except OSError:
                    app.logger.exception("Impossible de nettoyer un fichier après échec d'enregistrement")
        app.logger.exception("Erreur lors de la gestion des fichiers du projet")
        return jsonify({"error": "Erreur lors de l'enregistrement du fichier"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/developpeur/fichiers/<int:fichier_id>", methods=["GET", "DELETE"])
@developer_required
def developer_project_file(fichier_id):
    """Télécharge ou supprime logiquement un fichier de projet."""
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        developer = get_linked_developer(cursor)
        if developer is None:
            return jsonify({
                "error": "Ce compte développeur n'est pas encore associé à une fiche employé"
            }), 409

        cursor.execute(
            "SELECT id, projet_id, employe_id, nom_original, nom_stockage, "
            "type_mime, supprime_le FROM fichiers_projets WHERE id = %s",
            (fichier_id,),
        )
        fichier = cursor.fetchone()
        if fichier is None or not developer_has_project_access(
            cursor, developer["id"], fichier["projet_id"]
        ):
            return jsonify({"error": "Fichier introuvable ou accès refusé"}), 404

        if request.method == "DELETE":
            if fichier["employe_id"] != developer["id"]:
                return jsonify({"error": "Seul l'auteur du dépôt peut supprimer ce fichier"}), 403
            if fichier["supprime_le"] is not None:
                return jsonify({"error": "Ce fichier est déjà supprimé"}), 409
            cursor.execute(
                "UPDATE fichiers_projets SET supprime_le = CURRENT_TIMESTAMP "
                "WHERE id = %s AND supprime_le IS NULL",
                (fichier_id,),
            )
            conn.commit()
            return jsonify({"message": "Fichier supprimé; sa trace est conservée"}), 200

        if fichier["supprime_le"] is not None:
            return jsonify({"error": "Ce fichier a été supprimé"}), 410
        stored_path = os.path.join(PROJECT_FILES_DIRECTORY, fichier["nom_stockage"])
        if not os.path.isfile(stored_path):
            return jsonify({"error": "Fichier introuvable sur le stockage"}), 404
        return send_file(
            stored_path,
            mimetype=fichier["type_mime"],
            as_attachment=True,
            download_name=fichier["nom_original"],
        )
    except Exception:
        conn.rollback()
        app.logger.exception("Erreur lors de la gestion du fichier de projet")
        return jsonify({"error": "Erreur lors de la gestion du fichier"}), 500
    finally:
        cursor.close()
        conn.close()


def fetch_developer_projects(cursor, employe_id):
    cursor.execute(
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
        (employe_id, employe_id),
    )
    projects_by_id = {}
    for row in cursor.fetchall():
        project = projects_by_id.setdefault(row["projet_id"], {
            "id": row["projet_id"],
            "nom": row["nom"],
            "date_debut": iso_date(row["date_debut"]),
            "statut": row["statut"],
            "developpeurs": [],
            "taches": [],
        })
        if not any(member["id"] == row["membre_id"] for member in project["developpeurs"]):
            project["developpeurs"].append({
                "id": row["membre_id"],
                "nom": row["membre_nom"],
                "prenom": row["membre_prenom"],
            })
        if row["tache_id"] is not None and not any(
            task["id"] == row["tache_id"] for task in project["taches"]
        ):
            project["taches"].append({
                "id": row["tache_id"],
                "description": row["tache"],
                "assigne_a": ({
                    "id": row["affecte_id"],
                    "nom": row["affecte_nom"],
                    "prenom": row["affecte_prenom"],
                } if row["affecte_id"] is not None else None),
            })
    return list(projects_by_id.values())


@app.route("/manager/projets", methods=["GET"])
@pdg_or_manager_required
def get_manager_projects():
    """Liste les projets assignés, avec les développeurs et leurs tâches."""
    employe_id = request.args.get("employe_id", type=int)
    if request.args.get("employe_id") and employe_id is None:
        return jsonify({"error": "L'identifiant du développeur doit être un entier"}), 400

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        query = (
            "SELECT p.id AS projet_id, p.nom, p.date_debut, p.statut, "
            "e.id AS employe_id, e.nom AS nom_employe, e.prenom, "
            "responsable.id AS responsable_id, responsable.nom AS responsable_nom, "
            "responsable.prenom AS responsable_prenom, "
            "t.id AS tache_id, t.description AS tache, "
            "affecte.id AS affecte_id, affecte.nom AS affecte_nom, "
            "affecte.prenom AS affecte_prenom "
            "FROM projets p "
            "JOIN projet_developpeurs pd ON pd.projet_id = p.id "
            "JOIN employes e ON e.id = pd.employe_id "
            "JOIN employes responsable ON responsable.id = p.employe_id "
            "LEFT JOIN taches t ON t.projet_id = p.id "
            "LEFT JOIN employes affecte ON affecte.id = t.employe_id"
        )
        parameters = ()
        if employe_id is not None:
            query += " WHERE pd.employe_id = %s"
            parameters = (employe_id,)
        query += " ORDER BY p.id, t.id"
        cursor.execute(query, parameters)

        projects_by_id = {}
        for row in cursor.fetchall():
            project = projects_by_id.setdefault(row["projet_id"], {
                "id": row["projet_id"],
                "nom": row["nom"],
                "date_debut": iso_date(row["date_debut"]),
                "statut": row["statut"],
                "developpeur": {
                    "id": row["responsable_id"],
                    "nom": row["responsable_nom"],
                    "prenom": row["responsable_prenom"],
                },
                "developpeurs": [],
                "taches": [],
            })
            if not any(
                developer["id"] == row["employe_id"]
                for developer in project["developpeurs"]
            ):
                project["developpeurs"].append({
                    "id": row["employe_id"],
                    "nom": row["nom_employe"],
                    "prenom": row["prenom"],
                })
            if row["tache_id"] is not None and not any(
                task["id"] == row["tache_id"] for task in project["taches"]
            ):
                project["taches"].append({
                    "id": row["tache_id"],
                    "description": row["tache"],
                    "assigne_a": ({
                        "id": row["affecte_id"],
                        "nom": row["affecte_nom"],
                        "prenom": row["affecte_prenom"],
                    } if row["affecte_id"] is not None else None),
                })
        return jsonify(list(projects_by_id.values())), 200
    except Exception:
        app.logger.exception("Erreur lors de la récupération des projets")
        return jsonify({"error": "Erreur lors de la récupération des projets"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/manager/projets/<int:projet_id>/fichiers", methods=["GET"])
@pdg_or_manager_required
def manager_project_files(projet_id):
    """Liste les fichiers et leur historique pour un projet."""
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM projets WHERE id = %s", (projet_id,))
        if cursor.fetchone() is None:
            return jsonify({"error": "Projet introuvable"}), 404

        cursor.execute(
            "SELECT f.id, f.etape, f.nom_original, f.taille, f.type_mime, "
            "f.ajoute_le, f.supprime_le, e.nom AS employe_nom, "
            "e.prenom AS employe_prenom "
            "FROM fichiers_projets f JOIN employes e ON e.id = f.employe_id "
            "WHERE f.projet_id = %s ORDER BY f.ajoute_le DESC, f.id DESC",
            (projet_id,),
        )
        return jsonify({
            "fichiers": [
                project_file_payload(row, "/manager/fichiers")
                for row in cursor.fetchall()
            ]
        }), 200
    except Exception:
        app.logger.exception("Erreur lors de la récupération des fichiers du projet")
        return jsonify({"error": "Erreur lors de la récupération des fichiers"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/manager/fichiers/<int:fichier_id>", methods=["GET"])
@pdg_or_manager_required
def manager_project_file(fichier_id):
    """Télécharge un fichier actif d'un projet consultable par le manager."""
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT nom_original, nom_stockage, type_mime, supprime_le "
            "FROM fichiers_projets WHERE id = %s",
            (fichier_id,),
        )
        fichier = cursor.fetchone()
        if fichier is None:
            return jsonify({"error": "Fichier introuvable"}), 404
        if fichier["supprime_le"] is not None:
            return jsonify({"error": "Ce fichier a été supprimé"}), 410

        stored_path = os.path.join(PROJECT_FILES_DIRECTORY, fichier["nom_stockage"])
        if not os.path.isfile(stored_path):
            return jsonify({"error": "Fichier introuvable sur le stockage"}), 404
        return send_file(
            stored_path,
            mimetype=fichier["type_mime"],
            as_attachment=True,
            download_name=fichier["nom_original"],
        )
    except Exception:
        app.logger.exception("Erreur lors du téléchargement d'un fichier du projet")
        return jsonify({"error": "Erreur lors du téléchargement du fichier"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/manager/developpeurs/<int:employe_id>/fiche", methods=["GET"])
@pdg_or_manager_required
def get_developer_sheet(employe_id):
    """Retourne la fiche d'un développeur avec ses projets et tâches."""
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT id, nom, prenom, poste, date_embauche FROM employes WHERE id = %s",
            (employe_id,),
        )
        developer = cursor.fetchone()
        if developer is None:
            return jsonify({"error": "Développeur introuvable"}), 404
        if developer["poste"] != "developpeur":
            return jsonify({"error": "Cet employé n'est pas un développeur"}), 400

        cursor.execute(
            "SELECT competences, disponibilite, experience_avant_embauche "
            "FROM fiches_techniques_developpeurs WHERE employe_id = %s",
            (employe_id,),
        )
        technical_profile = cursor.fetchone()
        if technical_profile is None:
            developer["fiche_technique"] = None
        else:
            experience_before_hire = float(technical_profile["experience_avant_embauche"])
            tenure = completed_years_since(developer["date_embauche"])
            developer["fiche_technique"] = {
                "competences": technical_profile["competences"],
                "disponibilite": technical_profile["disponibilite"],
                "experience_avant_embauche": experience_before_hire,
                "anciennete_annees": tenure,
                "experience_totale_annees": experience_before_hire + tenure,
            }
        developer["date_embauche"] = iso_date(developer["date_embauche"])
        developer["projets"] = fetch_developer_projects(cursor, employe_id)
        return jsonify(developer), 200
    except Exception:
        app.logger.exception("Erreur lors de la récupération de la fiche développeur")
        return jsonify({"error": "Erreur lors de la récupération de la fiche développeur"}), 500
    finally:
        cursor.close()
        conn.close()


@app.route("/manager/projets", methods=["POST"])
@pdg_or_manager_required
def create_manager_project():
    """Attribue un projet à un développeur et crée ses tâches initiales."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps JSON est obligatoire"}), 400

    employe_ids = data.get("employe_ids")
    if employe_ids is None:
        employe_ids = [data.get("employe_id")]
    nom = data.get("nom")
    date_debut = data.get("date_debut")
    tasks = data.get("taches")
    if tasks is None:
        tasks = [
            {"employe_id": employe_ids[0], "description": "Analyse du projet"},
            {"employe_id": employe_ids[0], "description": "Développement"},
        ]
    if (
        not isinstance(employe_ids, list)
        or not employe_ids
        or any(
            not isinstance(employe_id, int)
            or isinstance(employe_id, bool)
            or employe_id < 1
            for employe_id in employe_ids
        )
        or len(set(employe_ids)) != len(employe_ids)
        or not isinstance(nom, str)
        or not nom.strip()
        or not isinstance(date_debut, str)
    ):
        return jsonify({"error": "Au moins un développeur, un nom de projet et une date de début sont obligatoires"}), 400
    if (
        not isinstance(tasks, list)
        or not tasks
        or any(
            not isinstance(task, (str, dict))
            or (isinstance(task, str) and not task.strip())
            or (
                isinstance(task, dict)
                and (
                    not isinstance(task.get("employe_id"), int)
                    or isinstance(task.get("employe_id"), bool)
                    or task.get("employe_id") not in employe_ids
                    or not isinstance(task.get("description"), str)
                    or not task["description"].strip()
                )
            )
            for task in tasks
        )
    ):
        return jsonify({"error": "La liste des tâches doit contenir au moins une tâche valide"}), 400
    if any(isinstance(task, dict) for task in tasks):
        assigned_ids = {
            task["employe_id"] for task in tasks if isinstance(task, dict)
        }
        if not set(employe_ids).issubset(assigned_ids):
            return jsonify({"error": "Chaque développeur sélectionné doit avoir au moins une tâche"}), 400
    try:
        date.fromisoformat(date_debut)
    except ValueError:
        return jsonify({"error": "La date de début doit respecter le format AAAA-MM-JJ"}), 400

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        placeholders = ", ".join(["%s"] * len(employe_ids))
        cursor.execute(
            f"SELECT id, poste FROM employes WHERE id IN ({placeholders})",
            tuple(employe_ids),
        )
        developers = cursor.fetchall()
        developers_by_id = {
            developer["id"]: developer
            for developer in developers
            if developer["poste"] == "developpeur"
        }
        if len(developers_by_id) != len(employe_ids):
            return jsonify({"error": "Tous les identifiants doivent correspondre à des développeurs"}), 400

        cursor.execute(
            "INSERT INTO projets (employe_id, nom, date_debut) VALUES (%s, %s, %s)",
            (employe_ids[0], nom.strip(), date_debut),
        )
        project_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO projet_developpeurs (projet_id, employe_id) VALUES (%s, %s)",
            [(project_id, employe_id) for employe_id in employe_ids],
        )
        cursor.executemany(
            "INSERT INTO taches (projet_id, employe_id, description) VALUES (%s, %s, %s)",
            [
                (
                    project_id,
                    task["employe_id"] if isinstance(task, dict) else employe_ids[0],
                    task["description"].strip() if isinstance(task, dict) else task.strip(),
                )
                for task in tasks
            ],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        app.logger.exception("Erreur lors de l'attribution du projet")
        return jsonify({"error": "Erreur lors de l'attribution du projet"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({
        "id": project_id,
        "employe_ids": employe_ids,
        "message": "Projet attribué avec succès",
    }), 201


@app.route("/manager/qui-fait-quoi", methods=["GET"])
@pdg_or_manager_required
def get_who_does_what():
    """Recherche une tâche attribuée à un développeur sur un projet."""
    employe_id = request.args.get("employe_id", type=int)
    nom_projet = request.args.get("projet", "").strip()
    description = request.args.get("tache", "").strip()
    if not employe_id or not nom_projet or not description:
        return jsonify({"error": "Développeur, projet et tâche sont obligatoires"}), 400

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
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
            (employe_id, nom_projet, description),
        )
        assignment = cursor.fetchone()
        if assignment is None:
            return jsonify({"error": "Aucune tâche correspondante"}), 404
        return jsonify(assignment), 200
    except Exception:
        app.logger.exception("Erreur lors de la recherche de tâche")
        return jsonify({"error": "Erreur lors de la recherche de tâche"}), 500
    finally:
        cursor.close()
        conn.close()

# POST sert à envoyer de nouvelles données au serveur.
@app.route("/employes", methods=["POST"])
@pdg_required
def add_employe():
    """Ajoute un nouvel employé à la base de données."""
    # Récupère les informations du nouvel employé envoyées en JSON.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps JSON est obligatoire"}), 400

    # Tous ces champs sont nécessaires pour créer un employé complet.
    required_fields = ("nom", "prenom", "poste", "date_embauche", "salaire")

    # On refuse la création si au moins un champ obligatoire est vide.
    if any(data.get(field) is None or data.get(field) == "" for field in required_fields):
        return jsonify({"error": "Tous les champs sont obligatoires"}), 400
    salaire = data.get("salaire")
    if (
        not isinstance(salaire, (int, float))
        or isinstance(salaire, bool)
        or not math.isfinite(salaire)
        or salaire < 0
    ):
        return jsonify({"error": "Le salaire doit être un nombre positif ou nul"}), 400

    # Copie chaque valeur dans une variable pour rendre la requête SQL lisible.
    nom = data.get("nom")
    prenom = data.get("prenom")
    poste = data.get("poste")
    date_embauche = data.get("date_embauche")
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500
    cursor = conn.cursor()
    # Les %s sont des paramètres SQL, pas une concaténation de texte.
    # Cette méthode protège contre les injections SQL.
    cursor.execute(
        "INSERT INTO employes (nom, prenom, poste, date_embauche, salaire) VALUES (%s, %s, %s, %s, %s)",
        (nom, prenom, poste, date_embauche, salaire),
    )
    # Valide l'ajout dans la base de données.
    conn.commit()
    cursor.close()
    conn.close()

    # 201 indique que l'employé a bien été créé.
    return jsonify({"message": "Employé ajouté avec succès"}), 201

# <int:id> signifie que Flask attend un identifiant entier dans l'URL,
# par exemple DELETE /employes/12.
@app.route("/employes/<int:id>", methods=["DELETE"])
@pdg_required
def delete_employe(id):
    """Supprime un employé grâce à son identifiant numérique."""
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor()
    # Supprime uniquement la ligne dont l'identifiant correspond à l'URL.
    cursor.execute("DELETE FROM employes WHERE id = %s", (id,))
    # rowcount permet de savoir si un employé correspondant existait.
    deleted = cursor.rowcount
    # La suppression n'est définitive qu'après commit.
    conn.commit()
    cursor.close()
    conn.close()

    # Si aucune ligne n'a été supprimée, l'identifiant n'existe pas.
    if deleted == 0:
        return jsonify({"error": "Employé introuvable"}), 404

    # 200 indique que la suppression a réussi.
    return jsonify({"message": "Employé supprimé avec succès"}), 200


# PUT sert à remplacer les informations d'une ressource existante.
@app.route("/employes/<int:id>", methods=["PUT"])
@pdg_required
def update_employe(id):
    """Remplace les informations d'un employé existant."""
    # Le frontend doit envoyer les nouvelles informations au format JSON.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps JSON est obligatoire"}), 400

    # Cette route remplace toutes les informations : tous les champs sont donc requis.
    required_fields = ("nom", "prenom", "poste", "date_embauche", "salaire")
    if any(data.get(field) is None or data.get(field) == "" for field in required_fields):
        return jsonify({"error": "Tous les champs sont obligatoires"}), 400
    salaire = data.get("salaire")
    if (
        not isinstance(salaire, (int, float))
        or isinstance(salaire, bool)
        or not math.isfinite(salaire)
        or salaire < 0
    ):
        return jsonify({"error": "Le salaire doit être un nombre positif ou nul"}), 400

    nom = data.get("nom")
    prenom = data.get("prenom")
    poste = data.get("poste")
    date_embauche = data.get("date_embauche")
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor()
    # UPDATE modifie uniquement l'employé correspondant à l'identifiant fourni.
    cursor.execute(
        "UPDATE employes SET nom = %s, prenom = %s, poste = %s, date_embauche = %s, salaire = %s WHERE id = %s",
        (nom, prenom, poste, date_embauche, salaire, id),
    )
    # rowcount vaut normalement 1 si une ligne a été modifiée, sinon 0.
    updated = cursor.rowcount
    exists = updated > 0
    if not exists:
        cursor.execute("SELECT id FROM employes WHERE id = %s", (id,))
        exists = cursor.fetchone() is not None
    conn.commit()
    cursor.close()
    conn.close()

    # 404 signifie que l'employé demandé n'a pas été trouvé.
    if not exists:
        return jsonify({"error": "Employé introuvable"}), 404

    return jsonify({"message": "Employé mis à jour avec succès"}), 200

@app.after_request
def after_request(response):
    """Ajoute les en-têtes CORS nécessaires au frontend local.

    CORS autorise une application web exécutée sur le port 5500 à appeler
    cette API exécutée sur le port 5000.
    """
    origin = request.headers.get("Origin")
    allowed_origins = {
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    }
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


if __name__ == "__main__":
    # Ce bloc est exécuté uniquement lorsque ce fichier est lancé directement.
    # debug=True recharge le serveur après une modification et affiche les erreurs.
    # Il faut désactiver debug=True en production pour des raisons de sécurité.
    # Le serveur sera accessible sur http://127.0.0.1:5000.
    app.run(debug=True , port = 5000)