employes = [ 
    {"nom": "Dupont", "prenom": "Jean", "poste": "comptable", "date_embauche": "01/01/2020", "salaire": 2500},
    {"nom": "Martin", "prenom": "Marie", "poste": "developpeur", "date_embauche": "01/01/2019", "salaire": 3000},
    {"nom": "Durand", "prenom": "Pierre", "poste": "manager", "date_embauche": "01/01/2018", "salaire": 4000},
    {"nom": "Leroy", "prenom": "Sophie", "poste": "developpeur", "date_embauche": "01/01/2021", "salaire": 2800}
    ]

def ajouter_employe(nom, prenom, poste, date_embauche, salaire):
    employe = {"nom": nom, "prenom": prenom, "poste": poste, "date_embauche": date_embauche, "salaire": salaire}
    employes.append(employe)

def enlever_employe(nom):
    employes[:] = [e for e in employes if e["nom"] != nom]

def modifier_employe(nom, prenom, poste, date_embauche, salaire):
    for e in employes:
        if  e["nom"] == nom:
            e["prenom"] = prenom
            e["poste"] = poste
            e["date_embauche"] = date_embauche
            e["salaire"] = salaire
            return
    print(f"Aucun employé nommé {nom} trouvé.")
