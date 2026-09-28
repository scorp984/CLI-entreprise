const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:5000`;
const ficheForm = document.getElementById("fiche-technique-form");
const fichePanel = document.getElementById("fiche-panel");
const editionPanel = document.getElementById("edition-panel");
const ficheMessage = document.getElementById("fiche-message");
const logoutButton = document.getElementById("logout-button");
let ficheExistante = false;
let ficheActuelle = null;

async function requestJson(path, options = {}) {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        credentials: "include",
        ...options
    });
    let result = {};
    try {
        result = await response.json();
    } catch (error) {
        result = {};
    }
    if (!response.ok) {
        throw new Error(result.error || "La requête a échoué.");
    }
    return result;
}

function formatYears(years) {
    return `${Number(years).toLocaleString("fr-FR", { maximumFractionDigits: 2 })} an(s)`;
}

function formatDate(dateValue) {
    if (!dateValue) {
        return "Non renseignée";
    }
    let parsedDate;
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
        const [year, month, day] = dateValue.split("-").map(Number);
        parsedDate = new Date(year, month - 1, day);
    } else {
        parsedDate = new Date(dateValue);
    }
    if (Number.isNaN(parsedDate.getTime())) {
        return "Date invalide";
    }
    return new Intl.DateTimeFormat("fr-FR").format(parsedDate);
}

function afficherProjets(projets = []) {
    const projetsBody = document.getElementById("projets-body");
    projetsBody.replaceChildren();

    if (!projets.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.textContent = "Aucun projet ne vous est assigné pour le moment.";
        row.append(cell);
        projetsBody.append(row);
        return;
    }

    projets.forEach((projet) => {
        const row = document.createElement("tr");
        const values = [
            projet.nom,
            (projet.taches || []).map((tache) => tache.description).filter(Boolean).join(", ") || "Aucune tâche renseignée",
            formatDate(projet.date_debut),
            projet.statut || "Non renseigné"
        ];

        values.forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.append(cell);
        });
        projetsBody.append(row);
    });
}

function afficherFiche(fiche) {
    ficheActuelle = fiche;
    ficheExistante = fiche.fiche_complete;
    document.getElementById("fiche-nom").textContent = `${fiche.prenom} ${fiche.nom}`;
    document.getElementById("fiche-date-embauche").textContent = formatDate(fiche.date_embauche);
    document.getElementById("fiche-competences").textContent = fiche.competences;
    document.getElementById("fiche-disponibilite").textContent = fiche.disponibilite;
    document.getElementById("fiche-anciennete").textContent = formatYears(fiche.anciennete_annees);
    document.getElementById("fiche-experience-totale").textContent = formatYears(fiche.experience_totale_annees);
    afficherProjets(fiche.projets);
    fichePanel.classList.add("visible");
    editionPanel.classList.remove("visible");
}

function ouvrirEdition(fiche = null) {
    document.getElementById("competences").value = fiche?.competences || "";
    document.getElementById("disponibilite").value = fiche?.disponibilite || "";
    document.getElementById("experience").value = fiche?.experience_avant_embauche ?? "";
    document.getElementById("annuler-fiche").hidden = !ficheExistante;
    fichePanel.classList.remove("visible");
    editionPanel.classList.add("visible");
    ficheMessage.textContent = "";
}

async function chargerFiche() {
    ficheMessage.textContent = "Chargement de la fiche...";
    try {
        const fiche = await requestJson("/developpeur/fiche");
        ficheExistante = fiche.fiche_complete;
        if (ficheExistante) {
            afficherFiche(fiche);
        } else {
            ouvrirEdition(fiche);
        }
        ficheMessage.textContent = "";
    } catch (error) {
        ficheMessage.textContent = `Impossible de charger la fiche : ${error.message}`;
    }
}

ficheForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
        competences: document.getElementById("competences").value.trim(),
        disponibilite: document.getElementById("disponibilite").value.trim(),
        experience_avant_embauche: Number(document.getElementById("experience").value)
    };
    const method = ficheExistante ? "PUT" : "POST";
    ficheMessage.textContent = "Enregistrement...";

    try {
        const result = await requestJson("/developpeur/fiche", {
            method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        ficheMessage.textContent = result.message;
        const fiche = await requestJson("/developpeur/fiche");
        afficherFiche(fiche);
        ficheMessage.textContent = result.message;
    } catch (error) {
        ficheMessage.textContent = `Impossible d'enregistrer la fiche : ${error.message}`;
    }
});

document.getElementById("modifier-fiche").addEventListener("click", () => {
    ouvrirEdition(ficheActuelle);
});

document.getElementById("annuler-fiche").addEventListener("click", () => {
    if (ficheActuelle) {
        afficherFiche(ficheActuelle);
    }
});

chargerFiche();

logoutButton.addEventListener("click", async function () {
    try {
        await fetch(`${API_BASE_URL}/auth/logout`, {
            method: "POST",
            credentials: "include"
        });
    } finally {
        window.location.href = "index.html";
    }
});
