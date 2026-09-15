from functools import wraps
import os
from flask import Flask, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.data import get_connection

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-a-remplacer")


def pdg_required(view):
    """Autorise uniquement un compte connecté avec le rôle PDG."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "pdg":
            return jsonify({"error": "Accès réservé au PDG"}), 403
        return view(*args, **kwargs)

    return wrapped


@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get("identifiant") or not data.get("mot_de_passe"):
        return jsonify({"error": "Identifiant et mot de passe obligatoires"}), 400

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, identifiant, mot_de_passe, role, actif "
        "FROM comptes WHERE identifiant = %s",
        (data["identifiant"],),
    )
    compte = cursor.fetchone()
    cursor.close()
    conn.close()

    if (
        compte is None
        or not compte["actif"]
        or not check_password_hash(compte["mot_de_passe"], data["mot_de_passe"])
    ):
        return jsonify({"error": "Identifiant ou mot de passe incorrect"}), 401

    session["compte_id"] = compte["id"]
    session["role"] = compte["role"]
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
    session.clear()
    return jsonify({"message": "Déconnexion réussie"}), 200


@app.route("/auth/me", methods=["GET"])
def current_account():
    if "compte_id" not in session:
        return jsonify({"error": "Vous devez être connecté"}), 401
    return jsonify({"id": session["compte_id"], "role": session["role"]}), 200


@app.route("/auth/comptes", methods=["POST"])
@pdg_required
def create_account():
    data = request.get_json(silent=True)
    roles = {"pdg", "manager", "rh", "comptable", "employe"}
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps JSON est obligatoire"}), 400
    if not data.get("identifiant") or not data.get("mot_de_passe") or data.get("role") not in roles:
        return jsonify({"error": "Identifiant, mot de passe et rôle obligatoires"}), 400

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO comptes (identifiant, mot_de_passe, role) VALUES (%s, %s, %s)",
            (
                data["identifiant"],
                generate_password_hash(data["mot_de_passe"]),
                data["role"],
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        return jsonify({"error": "Cet identifiant existe déjà ou est invalide"}), 409
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "Compte créé avec succès"}), 201


@app.route("/employes", methods=["GET"])
def get_employes():
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM employes")
    employes = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(employes), 200

@app.route("/employes", methods=["POST"])
def add_employe():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps JSON est obligatoire"}), 400

    required_fields = ("nom", "prenom", "poste", "date_embauche", "salaire")

    if any(not data.get(field) for field in required_fields):
        return jsonify({"error": "Tous les champs sont obligatoires"}), 400

    nom = data.get("nom")
    prenom = data.get("prenom")
    poste = data.get("poste")
    date_embauche = data.get("date_embauche")
    salaire = data.get("salaire")
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 400
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employes (nom, prenom, poste, date_embauche, salaire) VALUES (%s, %s, %s, %s, %s)",
        (nom, prenom, poste, date_embauche, salaire),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message": "Employé ajouté avec succès"}), 201

@app.route("/employes/<int:id>", methods=["DELETE"])
def delete_employe(id):
    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 400

    cursor = conn.cursor()
    cursor.execute("DELETE FROM employes WHERE id = %s", (id,))
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Employé introuvable"}), 404

    return jsonify({"message": "Employé supprimé avec succès"}), 200


@app.route("/employes/<int:id>", methods=["PUT"])
def update_employe(id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Le corps JSON est obligatoire"}), 400

    required_fields = ("nom", "prenom", "poste", "date_embauche", "salaire")
    if any(not data.get(field) for field in required_fields):
        return jsonify({"error": "Tous les champs sont obligatoires"}), 400

    nom = data.get("nom")
    prenom = data.get("prenom")
    poste = data.get("poste")
    date_embauche = data.get("date_embauche")
    salaire = data.get("salaire")

    conn = get_connection()
    if conn is None:
        return jsonify({"error": "Erreur de connexion à la base de données"}), 400

    cursor = conn.cursor()
    cursor.execute(
        "UPDATE employes SET nom = %s, prenom = %s, poste = %s, date_embauche = %s, salaire = %s WHERE id = %s",
        (nom, prenom, poste, date_embauche, salaire, id),
    )
    updated = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()

    if updated == 0:
        return jsonify({"error": "Employé introuvable"}), 404

    return jsonify({"message": "Employé mis à jour avec succès"}), 200


if __name__ == "__main__":
    app.run(debug=True , port = 5000)