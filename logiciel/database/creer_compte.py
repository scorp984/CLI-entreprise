from getpass import getpass

from werkzeug.security import generate_password_hash
from database.data import get_connection


identifiant = input("Identifiant du compte : ").strip()
role = input("Rôle (pdg, manager, rh, comptable, employe) : ").strip().lower()
mot_de_passe = getpass("Mot de passe : ")

roles = {"pdg", "manager", "rh", "comptable", "employe"}
if not identifiant or not mot_de_passe or role not in roles:
	raise SystemExit("Identifiant, mot de passe ou rôle invalide.")

conn = get_connection()
if conn is None:
	raise SystemExit("Connexion à la base de données impossible.")

cursor = conn.cursor()
try:
	cursor.execute(
		"INSERT INTO comptes (identifiant, mot_de_passe, role) VALUES (%s, %s, %s)",
		(identifiant, generate_password_hash(mot_de_passe), role),
	)
	conn.commit()
except Exception as error:
	conn.rollback()
	raise SystemExit(f"Création impossible : {error}") from error
finally:
	cursor.close()
	conn.close()

print(f"Compte {identifiant!r} créé avec le rôle {role!r}.")