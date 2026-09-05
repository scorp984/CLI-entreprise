# Importation des modules nécessaires
from datetime import datetime


class developpeur:
    def __init__(self, nom, prenom):
        self.nom = nom
        self.prenom = prenom
        self.projets = []

    def ajouter_projet(self, nom_projet, date_debut):
        projet = {
            "nom": nom_projet,
            "date_debut": date_debut,
            "statut": "en cours",
            "taches": []
        }
        self.projets.append(projet)
        print(f"{self.prenom} {self.nom} a reçu le projet {nom_projet}.")

    def ajouter_tache(self, nom_projet, tache):
        for p in self.projets:
            if p["nom"] == nom_projet:
                p["taches"].append(tache)
                break

    def fiche_technique(self):
        print(f"Fiche technique de {self.prenom} {self.nom}")
        for p in self.projets:
            print("Projet:", p["nom"])
            print("Date de début:", p["date_debut"])
            print("Statut:", p["statut"])
            print("Tâches:", p["taches"])

    def debut_projet(self, nom_projet, date_debut_projet):
        date_debut_projet = datetime.strptime(date_debut_projet, "%d/%m/%Y")
        date_actuelle = datetime.now()

        if date_debut_projet > date_actuelle:
            print(f"Le projet {nom_projet} commencera le {date_debut_projet.strftime('%d/%m/%Y')}.")
        else:
            print(f"Le projet {nom_projet} a déjà commencé le {date_debut_projet.strftime('%d/%m/%Y')}.")

    def projet(self, nom_projet):
        print(f"Le développeur travaille sur le projet : {nom_projet}")

        if nom_projet == "final":
            date_fin_projet = input("Entrez la date de fin du projet (format JJ/MM/AAAA) : ")
            date_fin_projet = datetime.strptime(date_fin_projet, "%d/%m/%Y")
            date_actuelle = datetime.now()
            print(f"Le projet {nom_projet} est terminé depuis le {date_actuelle.strftime('%d/%m/%Y')}.")









