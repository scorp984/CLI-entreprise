# Documentation API — Gestion des Employés

Projet **CLI-entreprise** — API REST développée avec Flask (Python) et MySQL.

## Informations générales

| | |
|---|---|
| **Base URL** | `http://127.0.0.1:5000` |
| **Format** | JSON |
| **Authentification** | Aucune (à ajouter en production) |

Toutes les requêtes et réponses utilisent le format JSON. Le header `Content-Type: application/json` doit être envoyé pour les requêtes `POST` et `PUT`.

---

## Table des routes

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/employes` | Récupère la liste de tous les employés |
| `POST` | `/employes` | Ajoute un nouvel employé |
| `PUT` | `/employes/<id>` | Met à jour un employé existant |
| `DELETE` | `/employes/<id>` | Supprime un employé |

---

## GET /employes

Récupère la liste complète des employés enregistrés en base de données.

### Requête

```http
GET /employes HTTP/1.1
Host: 127.0.0.1:5000
```

### Réponse — succès (200)

```json
[
  {
    "id": 1,
    "nom": "Dupont",
    "prenom": "Marie",
    "poste": "Développeuse",
    "date_embauche": "2023-05-12",
    "salaire": 2800
  },
  {
    "id": 2,
    "nom": "Martin",
    "prenom": "Léo",
    "poste": "Comptable",
    "date_embauche": "2021-09-01",
    "salaire": 2500
  }
]
```

### Réponse — erreur (400)

```json
{
  "error": "Erreur de connexion à la base de données"
}
```

---

## POST /employes

Ajoute un nouvel employé à la base de données.

### Champs requis

| Champ | Type | Description |
|---|---|---|
| `nom` | string | Nom de famille |
| `prenom` | string | Prénom |
| `poste` | string | Intitulé du poste |
| `date_embauche` | string (`YYYY-MM-DD`) | Date d'embauche |
| `salaire` | number | Salaire mensuel |

Tous les champs sont **obligatoires**. Si un champ est manquant ou vide, la requête est rejetée.

### Requête

```http
POST /employes HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json

{
  "nom": "Dupont",
  "prenom": "Marie",
  "poste": "Développeuse",
  "date_embauche": "2023-05-12",
  "salaire": 2800
}
```

### Réponse — succès (201)

```json
{
  "message": "Employé ajouté avec succès"
}
```

### Réponse — erreur (400)

Corps manquant ou non conforme :

```json
{
  "error": "Le corps JSON est obligatoire"
}
```

Champ(s) manquant(s) :

```json
{
  "error": "Tous les champs sont obligatoires"
}
```

Connexion base de données échouée :

```json
{
  "error": "Erreur de connexion à la base de données"
}
```

---

## PUT /employes/{id}

Met à jour les informations d'un employé existant. Tous les champs doivent être renvoyés (mise à jour complète, pas partielle).

### Paramètre d'URL

| Paramètre | Type | Description |
|---|---|---|
| `id` | integer | Identifiant de l'employé à modifier |

### Champs requis

Identiques à `POST /employes` : `nom`, `prenom`, `poste`, `date_embauche`, `salaire`.

### Requête

```http
PUT /employes/1 HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/json

{
  "nom": "Dupont",
  "prenom": "Marie",
  "poste": "Lead Développeuse",
  "date_embauche": "2023-05-12",
  "salaire": 3200
}
```

### Réponse — succès (200)

```json
{
  "message": "Employé mis à jour avec succès"
}
```

### Réponse — erreur (404)

L'`id` fourni ne correspond à aucun employé :

```json
{
  "error": "Employé introuvable"
}
```

### Réponse — erreur (400)

```json
{
  "error": "Le corps JSON est obligatoire"
}
```

```json
{
  "error": "Tous les champs sont obligatoires"
}
```

---

## DELETE /employes/{id}

Supprime un employé de la base de données.

### Paramètre d'URL

| Paramètre | Type | Description |
|---|---|---|
| `id` | integer | Identifiant de l'employé à supprimer |

### Requête

```http
DELETE /employes/1 HTTP/1.1
Host: 127.0.0.1:5000
```

### Réponse — succès (200)

```json
{
  "message": "Employé supprimé avec succès"
}
```

### Réponse — erreur (404)

```json
{
  "error": "Employé introuvable"
}
```

---

## Codes de statut HTTP utilisés

| Code | Signification | Utilisé quand |
|---|---|---|
| `200` | OK | Lecture, mise à jour ou suppression réussie |
| `201` | Created | Création réussie |
| `400` | Bad Request | JSON manquant/invalide, champ requis manquant, erreur de connexion DB |
| `404` | Not Found | L'employé demandé n'existe pas |

> **Note technique** : les erreurs de connexion à la base de données renvoient actuellement un code `400`. D'un point de vue strict, ce type d'erreur est plutôt côté serveur et devrait renvoyer un `500 Internal Server Error`. Point d'amélioration possible.

---

## Sécurité

- Toutes les requêtes SQL utilisent des **requêtes paramétrées** (`%s` + tuple de valeurs) plutôt que de la concaténation de chaînes, ce qui protège contre les **injections SQL**.
- Aucune authentification n'est actuellement en place : n'importe qui ayant accès au serveur peut lire, créer, modifier ou supprimer des employés. À ajouter avant tout déploiement public (ex. clé API, JWT, ou authentification basique).
- L'option `debug=True` du serveur Flask ne doit **jamais** être activée en production : elle expose des informations sensibles en cas d'erreur.

---

## Exemples avec `curl`

```bash
# Lister tous les employés
curl http://127.0.0.1:5000/employes

# Ajouter un employé
curl -X POST http://127.0.0.1:5000/employes \
  -H "Content-Type: application/json" \
  -d '{"nom":"Dupont","prenom":"Marie","poste":"Développeuse","date_embauche":"2023-05-12","salaire":2800}'

# Mettre à jour un employé (id = 1)
curl -X PUT http://127.0.0.1:5000/employes/1 \
  -H "Content-Type: application/json" \
  -d '{"nom":"Dupont","prenom":"Marie","poste":"Lead Développeuse","date_embauche":"2023-05-12","salaire":3200}'

# Supprimer un employé (id = 1)
curl -X DELETE http://127.0.0.1:5000/employes/1
```
