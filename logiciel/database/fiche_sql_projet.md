# Fiche SQL - Projet CLI Entreprise

## 1. Connexion a MySQL

Le serveur MySQL utilise actuellement :

- Hote : `localhost`
- Port : `3306`
- Base : `cli_entreprise`
- Utilisateur MySQL : `patron`

Depuis PowerShell, a partir de `C:\Users\tetun\Desktop\cli entreprise` :

```powershell
& "C:\UwAmp\bin\database\mysql-5.6.20\bin\mysql.exe" -u patron -p cli_entreprise
```

Le mot de passe MySQL est demande apres la commande.

Pour executer un fichier `.sql` dans PowerShell, ne pas utiliser `<`. Utiliser :

```powershell
Get-Content -Raw ".\logiciel\database\fichier.sql" |
    & "C:\UwAmp\bin\database\mysql-5.6.20\bin\mysql.exe" -u patron -p cli_entreprise
```

## 2. Selectionner la base

A executer dans MySQL :

```sql
SHOW DATABASES;
USE cli_entreprise;
SELECT DATABASE();
```

## 3. Verifier les tables

```sql
SHOW TABLES;
DESCRIBE comptes;
DESCRIBE employes;
SHOW CREATE TABLE comptes;
SHOW CREATE TABLE employes;
```

## 4. Table des comptes de l'application

Cette table contient les comptes utilises sur la page de connexion. Elle est differente de l'utilisateur MySQL `patron`.

```sql
CREATE TABLE IF NOT EXISTS comptes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    identifiant VARCHAR(100) NOT NULL UNIQUE,
    mot_de_passe VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Les mots de passe de l'application doivent etre hashes par Python. Pour creer un compte :

```powershell
cd ".\logiciel"
python -m database.creer_compte
```

Roles acceptes : `pdg`, `manager`, `rh`, `comptable`, `employe`.

Requetes utiles :

```sql
SELECT id, identifiant, role, actif, date_creation
FROM comptes;

UPDATE comptes
SET actif = FALSE
WHERE identifiant = 'patron';

UPDATE comptes
SET actif = TRUE
WHERE identifiant = 'patron';

DELETE FROM comptes
WHERE identifiant = 'identifiant_a_supprimer';
```

Ne pas mettre un mot de passe en clair directement dans SQL : l'API utilise `generate_password_hash`.

## 5. Table des employes

La table doit contenir les colonnes utilisees par l'API :

```sql
CREATE TABLE IF NOT EXISTS employes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    poste ENUM('comptable', 'developpeur', 'manager') NOT NULL,
    date_embauche DATE NOT NULL,
    salaire DECIMAL(10, 2) NOT NULL
);
```

Postes actuellement acceptes : `comptable`, `developpeur`, `manager`.

Si la table existe deja, verifier sa structure avant de la recreer :

```sql
DESCRIBE employes;
```

## 6. Inserer des employes

Les dates utilisent le format MySQL `AAAA-MM-JJ`.

```sql
INSERT INTO employes
    (nom, prenom, poste, date_embauche, salaire)
VALUES
    ('Dupont', 'Jean', 'comptable', '2020-01-01', 2500.00),
    ('Martin', 'Marie', 'developpeur', '2019-01-01', 3000.00),
    ('Durand', 'Pierre', 'manager', '2018-01-01', 4000.00),
    ('Leroy', 'Sophie', 'developpeur', '2021-01-01', 2800.00);
```

Avant une nouvelle insertion, verifier ce qui existe deja :

```sql
SELECT * FROM employes;
SELECT COUNT(*) AS nombre_employes FROM employes;
```

## 7. Tables projets et taches

Ces tables existent deja dans la base actuelle :

```sql
CREATE TABLE IF NOT EXISTS projets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employe_id INT NOT NULL,
    nom VARCHAR(150) NOT NULL,
    date_debut DATE NOT NULL,
    statut ENUM('en cours', 'terminé') NOT NULL DEFAULT 'en cours'
);

CREATE TABLE IF NOT EXISTS taches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    projet_id INT NOT NULL,
    description VARCHAR(255) NOT NULL
);
```

Ajouter un projet et une tache :

```sql
INSERT INTO projets (employe_id, nom, date_debut, statut)
VALUES (1, 'Migration informatique', '2026-09-15', 'en cours');

INSERT INTO taches (projet_id, description)
VALUES (1, 'Preparer la base de donnees');
```

Afficher les projets avec le nom de l'employe :

```sql
SELECT projets.id, projets.nom, projets.date_debut, projets.statut,
       employes.prenom, employes.nom AS nom_employe
FROM projets
JOIN employes ON employes.id = projets.employe_id;
```

Afficher les taches avec leur projet :

```sql
SELECT taches.id, taches.description, projets.nom AS projet
FROM taches
JOIN projets ON projets.id = taches.projet_id;
```

## 8. Lire les employes

```sql
SELECT * FROM employes;

SELECT id, nom, prenom, poste, date_embauche, salaire
FROM employes
ORDER BY nom, prenom;

SELECT *
FROM employes
WHERE poste = 'developpeur';

SELECT *
FROM employes
WHERE salaire >= 3000;

SELECT *
FROM employes
WHERE nom LIKE 'Dup%';
```

## 9. Modifier un employe

Toujours verifier l'identifiant avant la modification :

```sql
SELECT * FROM employes WHERE id = 1;
```

Puis modifier :

```sql
UPDATE employes
SET poste = 'developpeur senior', salaire = 3500.00
WHERE id = 1;
```

Verifier le resultat :

```sql
SELECT * FROM employes WHERE id = 1;
```

## 10. Supprimer un employe

```sql
SELECT * FROM employes WHERE id = 1;

DELETE FROM employes
WHERE id = 1;
```

Pour supprimer tous les employes, utiliser cette commande avec prudence :

```sql
DELETE FROM employes;
```

Pour reinitialiser aussi l'auto-increment apres une table vide :

```sql
ALTER TABLE employes AUTO_INCREMENT = 1;
```

## 11. Requetes de statistiques

```sql
SELECT COUNT(*) AS total_employes
FROM employes;

SELECT poste, COUNT(*) AS nombre
FROM employes
GROUP BY poste
ORDER BY nombre DESC;

SELECT AVG(salaire) AS salaire_moyen,
       MIN(salaire) AS salaire_minimum,
       MAX(salaire) AS salaire_maximum
FROM employes;

SELECT SUM(salaire) AS masse_salariale
FROM employes;
```

## 12. Transactions

Pour tester plusieurs changements et pouvoir les annuler :

```sql
START TRANSACTION;

UPDATE employes
SET salaire = salaire + 100
WHERE poste = 'developpeur';

SELECT * FROM employes WHERE poste = 'developpeur';

-- Valider definitivement :
COMMIT;

-- Ou annuler a la place de COMMIT :
-- ROLLBACK;
```

## 13. Sauvegarder et restaurer la base

Depuis PowerShell :

```powershell
& "C:\UwAmp\bin\database\mysql-5.6.20\bin\mysqldump.exe" -u patron -p cli_entreprise > ".\sauvegarde_cli_entreprise.sql"
```

Restaurer une sauvegarde :

```powershell
Get-Content -Raw ".\sauvegarde_cli_entreprise.sql" |
    & "C:\UwAmp\bin\database\mysql-5.6.20\bin\mysql.exe" -u patron -p cli_entreprise
```

## 14. Controle apres une modification

```sql
SELECT COUNT(*) FROM comptes;
SELECT COUNT(*) FROM employes;
SELECT * FROM comptes;
SELECT * FROM employes;
```

## 15. Erreurs frequentes

### `Access denied for user`

Le compte MySQL ou son mot de passe est incorrect. La commande utilise l'utilisateur MySQL `patron`, pas un compte de la table `comptes`.

### `Table doesn't exist`

Verifier la base selectionnee et les tables :

```sql
SELECT DATABASE();
SHOW TABLES;
```

### `ModuleNotFoundError: No module named 'database'`

Depuis le dossier `logiciel`, lancer le script comme module :

```powershell
python -m database.creer_compte
```

### Erreur PowerShell avec `<`

PowerShell ne gere pas cette redirection comme CMD. Utiliser `Get-Content -Raw` avec un pipe, comme dans la section 1.

## 16. Regles importantes

- Toujours utiliser `WHERE` avec `UPDATE` et `DELETE`, sauf si toute la table doit etre modifiee.
- Faire un `SELECT` avant une modification ou une suppression.
- Utiliser des dates `AAAA-MM-JJ`.
- Utiliser des requetes parametrees dans Python, jamais de concatenation de valeurs utilisateur.
- Ne pas stocker les mots de passe de l'application en clair.
- Faire une sauvegarde avant une operation importante.
