import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="patron",
            password="patron",
            database="cli_entreprise"
        )
        return conn
    except Error as e:
        print(f"Erreur de connexion : {e}")
        return None