from flask import Flask, jsonify, request
import sys ,os 
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.data import get_connection

app = Flask(__name__)


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