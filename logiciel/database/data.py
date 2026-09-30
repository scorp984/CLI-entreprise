import os

import mysql.connector
from mysql.connector import Error


def get_connection():
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    if not db_user or not db_password:
        print("Configurez DB_USER et DB_PASSWORD avant de lancer l'application.")
        return None

    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", "3306")),
            user=db_user,
            password=db_password,
            database=os.environ.get("DB_NAME", "cli_entreprise"),
        )
        return conn
    except (Error, ValueError) as e:
        print(f"Erreur de connexion : {e}")
        return None

