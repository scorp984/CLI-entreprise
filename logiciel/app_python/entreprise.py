# Importation des modules nécessaires
from pathlib import Path
try:
    from .employes import employes, ajouter_employe, enlever_employe
except ImportError:
    from employes import employes, ajouter_employe, enlever_employe
from datetime import datetime

# Classe pour gérer les comptables et leurs salaires
class comptable:
    # Constructeur : initialise les attributs du comptable (nom, prénom, salaire)
    def __init__(self, nom, prenom, salaire): 
        self.nom = nom
        self.prenom = prenom
        self.salaire = salaire
   

    # Méthode pour augmenter le salaire d'un pourcentage donné
    # Le salaire est plafonné à 3200 euros maximum
    def augmenter_salaire(self, pourcentage):
        self.salaire += self.salaire * (pourcentage / 100)
        while self.salaire > 3200:
            self.salaire = 3200
            print("Le salaire ne peut pas dépasser 3200.")

    # Méthode pour calculer le salaire net après imposition
    # Prend en paramètre le taux d'imposition en pourcentage
    def salaire_net(self , taux_imposition):
        salaire_net = self.salaire*(1 - taux_imposition / 100)
        return salaire_net

    # Méthode pour calculer l'ancienneté en années
    # Prend la date d'embauche au format "JJ/MM/AAAA"
    def anciennete(self, date_embauche):
        date_embauche = datetime.strptime(date_embauche, "%d/%m/%Y")
        date_actuelle = datetime.now()
        anciennete = (date_actuelle - date_embauche).days // 365
        return anciennete
    

def main():
    nom_recherche = input("Entrez le nom de l'employé à choisir : ")
    prenom_recherche = input("Entrez le prénom de l'employé à choisir : ")

    employe_trouve = next(
        (
            employe
            for employe in employes
            if employe["nom"] == nom_recherche
            and employe["prenom"] == prenom_recherche
        ),
        None,
    )

    if employe_trouve is None:
        print("Aucun employé trouvé avec ce nom et ce prénom.")
        return

    employe = comptable(
        employe_trouve["nom"],
        employe_trouve["prenom"],
        employe_trouve["salaire"],
    )
    augmentation = float(input("Veuillez entrer le pourcentage d'augmentation : "))
    employe.augmenter_salaire(augmentation)
    nouveau_salaire = employe.salaire

    print(
        f"Le nouveau salaire de {employe_trouve['prenom']} "
        f"{employe_trouve['nom']} est : {nouveau_salaire}"
    )

    anciennete = employe.anciennete(employe_trouve["date_embauche"])
    salaire_anciennete = employe.salaire
    if anciennete >= 2:
        employe.salaire = min(employe.salaire + 200, 3200)
        salaire_anciennete = employe.salaire
        print(
            f"L'employé a {anciennete} ans d'ancienneté. "
            f"Son salaire après l'augmentation pour ancienneté est : "
            f"{salaire_anciennete}"
        )

    write_path = Path(__file__).resolve().parent.parent / "storage" / "comptable.txt"
    with write_path.open("a", encoding="utf-8") as append_file:
        append_file.write(f"Nom: {employe_trouve['nom']}\n")
        append_file.write(f"Prénom: {employe_trouve['prenom']}\n")
        append_file.write(f"Ancien salaire: {employe_trouve['salaire']}\n")
        append_file.write(f"Date d'embauche: {employe_trouve['date_embauche']}\n")
        append_file.write(f"Ancienneté: {anciennete} ans\n")
        append_file.write(f"Pourcentage d'augmentation: {augmentation}%\n")
        append_file.write(f"Nouveau salaire: {nouveau_salaire}\n")
        append_file.write(f"Salaire après ancienneté: {salaire_anciennete}\n")
        append_file.write("-" * 30 + "\n")


if __name__ == "__main__":
    main()




