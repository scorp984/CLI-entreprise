# Importation des modules nécessaires
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
    

# ===== PROGRAMME PRINCIPAL =====

# Demander à l'utilisateur le nom et le prénom de l'employé à rechercher
nom_recherche = input("Entrez le nom de l'employé à choisir : ")
prenom_recherche = input("Entrez le prénom de l'employé à choisir : ")

# Variable pour stocker l'employé trouvé
employe_trouve = None

# Parcourir la liste des employés pour trouver celui recherché
for e in employes:
    if e["nom"] == nom_recherche and e["prenom"] == prenom_recherche:
        employe_trouve = e
        break

# Vérifier si l'employé a été trouvé
if employe_trouve is None:
    print("Aucun employé trouvé avec ce nom et ce prénom.")
else:
    # Créer une instance de comptable avec les données de l'employé
    employe = comptable("Nom", "Prenom", employe_trouve["salaire"])
    
    # Demander le pourcentage d'augmentation à l'utilisateur
    augmentation = float(input("Veuillez entrer le pourcentage d'augmentation : "))
    
    # Appliquer l'augmentation au salaire
    employe.augmenter_salaire(augmentation)
    nouveau_salaire = employe.salaire

# Afficher le nouveau salaire après augmentation
print(f"Le nouveau salaire de {employe_trouve['prenom']} {employe_trouve['nom']} est : {nouveau_salaire}")

# Calculer l'ancienneté de l'employé
anciennete = employe.anciennete(employe_trouve["date_embauche"])

# Vérifier si l'employé a au moins 2 ans d'ancienneté
if anciennete >= 2:
    employe.salaire += 200
    if employe.salaire > 3200:
        employe.salaire = 3200
    salaire_anciennete = employe.salaire
    print(f"L'employé a {anciennete} ans d'ancienneté. Son salaire après l'augmentation pour ancienneté est : {salaire_anciennete}")


# Chemin du fichier où sauvegarder les données du comptable
write_path = "./comptable.txt"

# Ouvrir le fichier en mode ajout (ne pas écraser les anciennes données)
append_file = open(write_path, "a")

# Écrire les informations de l'employé dans le fichier
append_file.write(f"Nom: {employe_trouve['nom']}\n")
append_file.write(f"Prénom: {employe_trouve['prenom']}\n")
append_file.write(f"Ancien salaire: {employe_trouve['salaire']}\n")
append_file.write(f"Date d'embauche: {employe_trouve['date_embauche']}\n")
append_file.write(f"Ancienneté: {anciennete} ans\n")
append_file.write(f"Pourcentage d'augmentation: {augmentation}%\n")
append_file.write(f"Nouveau salaire: {nouveau_salaire}\n")
append_file.write(f"Salaire après ancienneté: {salaire_anciennete}\n")
append_file.write("-" * 30 + "\n")  # séparateur entre chaque entrée

# Fermer le fichier
append_file.close()




