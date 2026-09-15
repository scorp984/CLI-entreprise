const form = document.querySelector("#login-form");
const message = document.querySelector("#login-message");


form.addEventListener("submit", function (event) {
    event.preventDefault();
});

const identifiant = document.querySelector("#usurname").value;
const motDePasse = document.querySelector("#password").value;

try{
const reponse = await fetch("https://127.0.0.1:5000/auth/login", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    credentials: "include",
    body: JSON.stringify({
        identifiant: identifiant,
        motDePasse: motDePasse
    })
});

const resultat = await reponse.json();

    if(!reponse.ok) {
        message.textContent = resultat.error;
        return;
    }

message.textContent = "Connexion réussie . Role : "+ resultat.compte.role;

console.log(resultat); 

}catch (error) {
    message.textContent = "Erreur lors de la connexion : " + error.message;
    console.error("Erreur lors de la connexion :", error);
}

