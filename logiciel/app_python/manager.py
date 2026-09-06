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

    def qui_fais_quoi(self, employe, nom_projet, tache):
        if employe["poste"] == "developpeur":
            print(
                f"Le développeur {employe['prenom']} {employe['nom']}"
                f"réalise la tâche « {tache} » sur le projet « {nom_projet} »."
            )
        else:
            print("Ce salarié n'est pas un développeur.")

    def equipe_projet(self, nom_projet, employes, tache):
        # On garde uniquement les employés qui ont le poste de développeur.
        developpeurs = [e for e in employes if e["poste"] == "developpeur"]

        # Il est impossible de créer une équipe s'il n'y a aucun développeur.
        if not developpeurs:
            print("Aucun développeur n'est disponible pour ce projet.")
            return

        # On redemande une valeur tant que le nombre saisi n'est pas valide.
        while True:
            try:
                # input() renvoie du texte : int() le transforme en nombre entier.
                nombre_developpeurs = int(
                    input(
                        f"Combien de développeurs voulez-vous pour le projet "
                        f"{nom_projet} (1-{len(developpeurs)}) ? "
                    )
                )

                # Le nombre doit être au moins 1 et ne pas dépasser les disponibles.
                if 1 <= nombre_developpeurs <= len(developpeurs):
                    break
                print(f"Veuillez choisir un nombre entre 1 et {len(developpeurs)}.")
            except ValueError:
                # Cette erreur arrive si l'utilisateur saisit autre chose qu'un nombre.
                print("Veuillez entrer un nombre entier.")

        print(f"Équipe travaillant sur le projet {nom_projet} :")

        # [:nombre_developpeurs] sélectionne seulement le nombre de personnes demandé.
        for developpeur in developpeurs[:nombre_developpeurs]:
            # La tâche est affichée pour chaque membre choisi dans l'équipe.
            print(f"- {developpeur['prenom']} {developpeur['nom']} : {tache}")