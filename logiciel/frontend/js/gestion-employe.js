const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:5000`;

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const reponse = await fetch(`${API_BASE_URL}/employes`, {
            credentials: "include"
        });
        const employes = await reponse.json();

        if (!reponse.ok) {
            throw new Error(employes.error || "Impossible de charger les employés.");
        }

        new DataTable("#employes", {
            data: employes.map((employe) => [
                employe.nom,
                employe.prenom,
                employe.poste,
                employe.date_embauche,
                employe.salaire
            ]),
            columns: [
                { title: "Nom" },
                { title: "Prénom" },
                { title: "Poste" },
                { title: "Date d'embauche" },
                { title: "Salaire" }
            ],
            paging: true,
            searching: true,
            ordering: true,
            info: true
        });
    } catch (error) {
        const message = document.createElement("p");
        message.setAttribute("role", "alert");
        message.textContent = error.message;
        document.querySelector("#employes").after(message);
        console.error(error);
    }
});