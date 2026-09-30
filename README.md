# CLI Entreprise

> ⚠️ Projet d'apprentissage personnel, pas un outil de production. Réalisé pour progresser sur Flask, MySQL, JavaScript et la structuration d'une API REST — pas destiné à un usage réel en entreprise.

Application web de gestion d'entreprise développée avec Flask, MySQL et JavaScript, dans le cadre de mon apprentissage du développement fullstack. Ce projet de portfolio explore la mise en place d'une API REST, d'une interface par rôle et de la gestion de projets et de documents.

## Objectifs d'apprentissage

Ce projet m'a permis de manipuler concrètement :
- La construction d'une API REST avec Flask (routes, authentification, gestion de session)
- La connexion et les requêtes à une base de données MySQL depuis Python
- La structuration d'une interface web par rôle (développeur, manager, PDG)
- La gestion de fichiers uploadés (dépôt de documents par étape)

## Utilisation de l'IA

Une partie du code de ce projet a été écrite avec l'aide de l'IA (notamment sur les parties les plus complexes comme l'intégration Flask/MySQL/JS), en complément de mon propre apprentissage. Je m'en sers comme d'un outil pour comprendre des concepts et débloquer des points techniques, pas comme un substitut à l'écriture du code — l'objectif reste de progresser en développement.

## Fonctionnalités

- Authentification et gestion des rôles
- Gestion des employés et des comptes
- Attribution de projets, d'équipes et de tâches
- Fiche technique développeur
- Dépôt de plusieurs documents par étape, historique et téléchargement côté manager

## Technologies

- Python 3.11+
- Flask
- MySQL
- HTML, CSS et JavaScript

## Lancer en local sous Windows

Prérequis : Python, un serveur MySQL et l'extension VS Code Live Server.

Depuis la racine du dépôt, créer l'environnement et installer les dépendances :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Préparer la base MySQL `cli_entreprise` et ses tables en suivant [la fiche SQL](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/tetun/Desktop/cli%20entreprise/logiciel/database/fiche_sql_projet.md). Appliquer ensuite, une seule fois chacune, les migrations dans cet ordre :

1. `logiciel/database/migration_fiche_technique_developpeur.sql`
2. `logiciel/database/migration_equipe_projet.sql`
3. `logiciel/database/migration_taches_developpeur.sql`
4. `logiciel/database/migration_fichiers_projets.sql`

Dans le terminal qui servira à lancer l'API, configurer les paramètres MySQL. Remplacer les valeurs d'exemple par les paramètres de sa base :

```powershell
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_NAME = "cli_entreprise"
$env:DB_USER = "votre_utilisateur_mysql"
$securePassword = Read-Host "Mot de passe MySQL" -AsSecureString
$env:DB_PASSWORD = [System.Net.NetworkCredential]::new("", $securePassword).Password
```

Ces variables restent définies uniquement dans ce terminal.

Depuis la racine du dépôt, créer le premier compte d'administration :

```powershell
Set-Location .\logiciel
..\.venv\Scripts\python.exe -m database.creer_compte
```

Dans le même terminal, lancer l'API :

```powershell
..\.venv\Scripts\python.exe -m api.api
```

Dans VS Code, ouvrir `logiciel/frontend/html/index.html` avec Live Server. L'interface locale est prévue pour `http://127.0.0.1:5500` ou `http://localhost:5500`.

## Tests

Depuis le dossier `logiciel` :

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests
```