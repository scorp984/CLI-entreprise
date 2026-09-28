const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:5000`;
const form = document.querySelector("#login-form");
const message = document.querySelector("#login-message");

form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const identifiant = document.querySelector("#username").value.trim();
    const motDePasse = document.querySelector("#password").value;

    try {
        const reponse = await fetch(`${API_BASE_URL}/auth/login`, {
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

        if (resultat.compte.role === "pdg") {
            window.location.href = "page-pdg.html";
            return;
        }

        if (resultat.compte.role === "manager") {
            window.location.href = "manager.html";
            return;
        }

        if (resultat.compte.role === "developpeur") {
            window.location.href = "developpeur.html";
            return;
        }

        message.textContent = "Connexion réussie, mais aucune page n'est encore disponible pour ce rôle.";
    } catch (error) {
        message.textContent = "Erreur lors de la connexion : " + error.message;
        console.error("Erreur lors de la connexion :", error);
    }
});

