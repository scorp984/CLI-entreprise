from dev import developpeur
from employes import employes


class manager:
    def attribuer_projet(self, employe, nom_projet, date_debut):
        if employe["poste"] == "developpeur":
            dev = developpeur(employe["nom"], employe["prenom"])
            dev.ajouter_projet(nom_projet, date_debut)
            dev.ajouter_tache(nom_projet, "Analyse du projet")
            dev.ajouter_tache(nom_projet, "Développement")
            return dev
        else:
            print("Ce salarié n'est pas un développeur.")
            return None

    def gerer_les_developpeurs(self, employe, nom_projet, date_debut):
        dev = self.attribuer_projet(employe, nom_projet, date_debut)
        if dev is not None:
            print(f"Le manager gère le développeur {employe['prenom']} {employe['nom']}.")
            dev.fiche_technique()