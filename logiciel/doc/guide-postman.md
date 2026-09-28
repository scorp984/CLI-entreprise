# Guide Postman - API CLI entreprise

## Avant de commencer

1. Démarre MySQL et vérifie que la base `cli_entreprise` existe.
2. Depuis le dossier `logiciel`, démarre Flask :

```powershell
python api/api.py
```

L'API est disponible à `http://127.0.0.1:5000`.

Dans Postman, tu peux créer un environnement avec la variable :

| Variable | Valeur initiale |
| --- | --- |
| `base_url` | `http://127.0.0.1:5000` |

Les exemples ci-dessous utilisent `{{base_url}}`.

## Se connecter

Crée une requête `POST {{base_url}}/auth/login`.

Dans **Body**, choisis **raw**, puis **JSON**, et envoie :

```json
{
  "identifiant": "pdg",
  "mot_de_passe": "TON_MOT_DE_PASSE"
}
```

Postman conserve normalement le cookie de session reçu après la connexion. Garde le même hôte (`127.0.0.1`) pour les autres requêtes afin de réutiliser ce cookie.

Réponses habituelles : `200` si la connexion réussit, `400` si un champ manque et `401` si les identifiants sont incorrects.

## Vérifier la session

Crée `GET {{base_url}}/auth/me`. Après une connexion réussie, la réponse doit ressembler à :

```json
{
  "id": 1,
  "role": "pdg"
}
```

Sans session, l'API répond `401`.

## Consulter les employés

Crée `GET {{base_url}}/employes` après t'être connecté avec un compte PDG. Cette route renvoie la liste des employés. Un visiteur reçoit `401`; un compte connecté qui n'est pas PDG reçoit `403`.

## Administrer les comptes

Toutes ces requêtes nécessitent une session PDG. L'inscription anonyme est désactivée.

Pour lister les comptes, crée `GET {{base_url}}/auth/comptes`. La réponse ne contient jamais les mots de passe hashes.

Pour créer un compte et sa fiche employé, crée `POST {{base_url}}/auth/comptes`. Dans **Body > raw > JSON**, envoie par exemple :

```json
{
  "identifiant": "manager01",
  "mot_de_passe": "mot-de-passe-test",
  "role": "manager",
  "nom": "Dupont",
  "prenom": "Camille",
  "poste": "manager",
  "date_embauche": "2026-09-26",
  "salaire": 2500
}
```

Les rôles de création acceptés sont `manager`, `comptable` et `developpeur`. Le salaire doit être un nombre positif ou nul. Le compte PDG initial reste créé côté serveur avec `database/creer_compte.py`.

Réponses habituelles : `201` si la création réussit, `400` si les données sont invalides, `401` sans session et `409` si l'identifiant existe déjà.

Pour modifier un compte, crée `PUT {{base_url}}/auth/comptes/2`, avec un ou plusieurs champs parmi `identifiant`, `role`, `mot_de_passe` et `actif` :

```json
{
  "role": "comptable",
  "actif": true
}
```

Le champ `mot_de_passe` est facultatif; s'il est omis, le mot de passe reste inchangé. Pour désactiver un compte, envoie `{"actif": false}`. Pour supprimer un compte, crée `DELETE {{base_url}}/auth/comptes/2`. Il est impossible de supprimer son propre compte ou de retirer le dernier PDG actif.

## Gérer les projets comme manager

Connecte-toi avec un compte `manager` ou `pdg`, puis crée `POST {{base_url}}/manager/projets` avec :

```json
{
  "employe_id": 7,
  "nom": "Refonte API",
  "date_debut": "2026-09-26"
}
```

Le projet est attribué au développeur et reçoit les tâches « Analyse du projet » et « Développement ».

- Liste des projets : `GET {{base_url}}/manager/projets`
- Projets d'un développeur : `GET {{base_url}}/manager/projets?employe_id=7`
- Fiche d'un développeur : `GET {{base_url}}/manager/developpeurs/7/fiche`
- Recherche d'une tâche : `GET {{base_url}}/manager/qui-fait-quoi?employe_id=7&projet=Refonte%20API&tache=Développement`

Le schéma actuel ne permet d'attribuer un projet qu'à un seul développeur; les équipes multi-développeurs nécessiteront une table dédiée.

## Ajouter, modifier ou supprimer un employé

Ces routes nécessitent une session PDG. Pour modifier ou ajouter, utilise **Body > raw > JSON** et les champs suivants :

```json
{
  "nom": "Dupont",
  "prenom": "Camille",
  "poste": "manager",
  "date_embauche": "2026-09-26",
  "salaire": 2500
}
```

| Action | Méthode et URL |
| --- | --- |
| Ajouter | `POST {{base_url}}/employes` |
| Modifier l'employé 1 | `PUT {{base_url}}/employes/1` |
| Supprimer l'employé 1 | `DELETE {{base_url}}/employes/1` |

Une réponse `404` signifie que l'employé demandé n'existe pas.

## Se déconnecter

Crée `POST {{base_url}}/auth/logout`. La session est supprimée; les routes réservées au PDG doivent ensuite répondre `401`.

## À savoir

- Pour envoyer du JSON, choisis **Body > raw > JSON**. Postman ajoute alors l'en-tête `Content-Type: application/json`.
- Postman n'est pas soumis au blocage CORS du navigateur.
- Une erreur `500` indiquant une erreur de connexion à la base signifie que MySQL n'est pas joignable ou que la configuration de connexion est incorrecte.
- Pour la première connexion PDG, crée ce compte avec le script `database/creer_compte.py` avant d'appeler `/auth/login`.