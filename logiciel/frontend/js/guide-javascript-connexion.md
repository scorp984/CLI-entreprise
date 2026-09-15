# Guide JavaScript - Page de connexion

Ce guide explique comment connecter le formulaire HTML a l'API Flask.

## 1. Les fichiers utilises

- Page HTML : `frontend/html/page-connect.html`
- JavaScript : `frontend/js/connextion.js`
- API Flask : `api/api.py`

Dans la page HTML, cette ligne charge le JavaScript :

```html
<script src="../js/connextion.js"></script>
```

Le nom du fichier doit etre exactement le meme partout. Ici, le fichier s'appelle `connextion.js`.

## 2. Les elements HTML importants

La page HTML contient :

```html
<form id="login-form">
    <label for="username">Nom d'utilisateur:</label>
    <input type="text" id="username" name="identifiant" required>

    <label for="password">Mot de passe:</label>
    <input type="password" id="password" name="mot_de_passe" required>

    <input type="submit" value="Se connecter">
    <p id="login-message" role="alert" aria-live="polite"></p>
</form>
```

Les identifiants importants sont :

- `login-form` : le formulaire complet ;
- `username` : le champ identifiant ;
- `password` : le champ mot de passe ;
- `login-message` : la zone qui affiche le resultat.

## 3. Recuperer les elements avec JavaScript

Dans `connextion.js` :

```javascript
const formulaire = document.querySelector("#login-form");
const message = document.querySelector("#login-message");
```

Le symbole `#` signifie que l'on cherche un element avec un `id`.

Attention :

```javascript
// Correct
 document.querySelector("#login-message");

// Incorrect : il manque le #
 document.querySelector("login-message");
```

## 4. Detecter l'envoi du formulaire

```javascript
formulaire.addEventListener("submit", function (event) {
    event.preventDefault();
});
```

- `addEventListener` ecoute une action ;
- `submit` correspond a l'envoi du formulaire ;
- `event.preventDefault()` empeche le rechargement de la page.

## 5. Lire les champs

```javascript
const identifiant = document.querySelector("#username").value;
const motDePasse = document.querySelector("#password").value;
```

`.value` recupere ce que l'utilisateur a tape.

## 6. Envoyer les donnees a l'API

L'API Flask possede cette route :

```text
POST http://127.0.0.1:5000/auth/login
```

Les donnees envoyees doivent avoir cette forme :

```json
{
    "identifiant": "pdg",
    "mot_de_passe": "mot_de_passe_du_pdg"
}
```

On utilise `fetch` pour envoyer la requete :

```javascript
const reponse = await fetch("http://127.0.0.1:5000/auth/login", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    credentials: "include",
    body: JSON.stringify({
        identifiant: identifiant,
        mot_de_passe: motDePasse
    })
});
```

Explications :

- `fetch` contacte l'API ;
- `method: "POST"` envoie des donnees ;
- `Content-Type` indique que les donnees sont du JSON ;
- `JSON.stringify` transforme l'objet JavaScript en texte JSON ;
- `credentials: "include"` conserve la session Flask.

## 7. Lire la reponse de l'API

```javascript
const resultat = await reponse.json();

if (!reponse.ok) {
    message.textContent = resultat.error;
    return;
}

message.textContent =
    "Connexion reussie. Role : " + resultat.compte.role;
```

`reponse.ok` vaut `true` si le statut HTTP est correct, par exemple `200`.

Si le mot de passe est incorrect, l'API renvoie une erreur `401` et le message est affiche dans la page.

## 8. Gerer les erreurs de connexion

```javascript
try {
    // Code qui contacte l'API
} catch (erreur) {
    message.textContent = "Impossible de contacter le serveur.";
    console.error(erreur);
}
```

Le bloc `try` essaie le code. Le bloc `catch` s'execute si le serveur est arrete ou inaccessible.

## 9. Code complet de connextion.js

Remplace le contenu de `connextion.js` par ce code :

```javascript
const formulaire = document.querySelector("#login-form");
const message = document.querySelector("#login-message");

formulaire.addEventListener("submit", async function (event) {
    event.preventDefault();

    const identifiant = document.querySelector("#username").value;
    const motDePasse = document.querySelector("#password").value;

    message.textContent = "Connexion en cours...";

    try {
        const reponse = await fetch("http://127.0.0.1:5000/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify({
                identifiant: identifiant,
                mot_de_passe: motDePasse
            })
        });

        const resultat = await reponse.json();

        if (!reponse.ok) {
            message.textContent = resultat.error;
            return;
        }

        message.textContent =
            "Connexion reussie. Role : " + resultat.compte.role;

        console.log(resultat);
    } catch (erreur) {
        message.textContent = "Impossible de contacter le serveur.";
        console.error(erreur);
    }
});
```

## 10. Lancer l'API

Ouvre PowerShell et execute :

```powershell
cd "C:\Users\tetun\Desktop\cli entreprise\logiciel"
python api/api.py
```

L'API doit etre disponible a cette adresse :

```text
http://127.0.0.1:5000
```

Ensuite, ouvre `page-connect.html` avec Live Server.

## 11. Tester la connexion

Utilise un compte qui existe dans la table MySQL `comptes`.

Exemple :

```text
Identifiant : pdg
Mot de passe : le mot de passe choisi lors de la creation du compte
```

En cas de succes, la page affiche le role du compte.

## 12. Erreurs frequentes

### Le message reste vide

Verifier que le paragraphe HTML possede bien :

```html
<p id="login-message"></p>
```

Et que JavaScript utilise :

```javascript
document.querySelector("#login-message");
```

### Impossible de contacter le serveur

Verifier que cette commande est toujours active :

```powershell
python api/api.py
```

### Erreur CORS

Le navigateur bloque parfois une page Live Server qui contacte Flask. Il faudra alors autoriser l'origine du frontend dans `api.py`.

### Connexion refusee

Verifier :

- que le compte existe dans MySQL ;
- que l'identifiant est correct ;
- que le mot de passe est correct ;
- que la table `comptes` a bien ete creee.
