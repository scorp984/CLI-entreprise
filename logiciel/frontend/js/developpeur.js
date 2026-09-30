const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:5000`;
const ficheForm = document.getElementById("fiche-technique-form");
const fichePanel = document.getElementById("fiche-panel");
const editionPanel = document.getElementById("edition-panel");
const ficheMessage = document.getElementById("fiche-message");
const logoutButton = document.getElementById("logout-button");
const inputDiagramme = document.getElementById('diagramme');
const inputDossier = document.getElementById('dossier');
const inputCompteRendu = document.getElementById('compte-rendu');
const missionProjectSelect = document.getElementById("mission-projet");
const missionMessage = document.getElementById("mission-message");
const missionFilesList = document.getElementById("mission-fichiers");
const missionFileInputs = [
    {
        input: inputDiagramme,
        etape: "diagramme",
        sendButton: document.getElementById("envoyer-diagramme"),
        clearButton: document.getElementById("retirer-diagramme")
    },
    {
        input: inputDossier,
        etape: "dossier",
        sendButton: document.getElementById("envoyer-dossier"),
        clearButton: document.getElementById("retirer-dossier")
    },
    {
        input: inputCompteRendu,
        etape: "compte-rendu",
        sendButton: document.getElementById("envoyer-compte-rendu"),
        clearButton: document.getElementById("retirer-compte-rendu")
    }
];
const missionStepLabels = {
    diagramme: "Diagramme",
    dossier: "Dossier avant programmation",
    "compte-rendu": "Tests et compte rendu"
};
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

function configurerMissionProjets(projets = []) {
    const selectedProjectId = missionProjectSelect.value;
    missionProjectSelect.replaceChildren();
    const defaultOption = document.createElement("option");
    defaultOption.value = "";
    defaultOption.textContent = "Sélectionner un projet...";
    missionProjectSelect.append(defaultOption);

    projets.forEach((projet) => {
        const option = document.createElement("option");
        option.value = projet.id;
        option.textContent = projet.nom;
        missionProjectSelect.append(option);
    });

    missionProjectSelect.value = projets.some(
        (projet) => String(projet.id) === selectedProjectId
    ) ? selectedProjectId : "";
    missionProjectSelect.disabled = projets.length === 0;
    mettreAJourActionsDepot();

    if (missionProjectSelect.value) {
        void chargerFichiersMission();
    } else {
        missionFilesList.replaceChildren();
        missionMessage.textContent = projets.length
            ? "Choisissez un projet pour consulter ou déposer ses fichiers."
            : "Aucun projet ne vous est assigné.";
    }
}

function mettreAJourActionsDepot() {
    const hasProject = Boolean(missionProjectSelect.value);
    missionFileInputs.forEach(({ input, sendButton, clearButton }) => {
        const hasFile = Boolean(input.files.length);
        input.disabled = !hasProject;
        sendButton.disabled = !hasProject || !hasFile;
        clearButton.disabled = !hasFile;
    });
}

async function chargerFichiersMission() {
    const projectId = missionProjectSelect.value;
    missionFilesList.replaceChildren();
    if (!projectId) {
        return;
    }

    missionMessage.textContent = "Chargement des fichiers...";
    try {
        const result = await requestJson(`/developpeur/projets/${projectId}/fichiers`);
        if (missionProjectSelect.value !== projectId) {
            return;
        }
        if (!result.fichiers.length) {
            const emptyMessage = document.createElement("li");
            emptyMessage.textContent = "Aucun fichier déposé pour ce projet.";
            missionFilesList.append(emptyMessage);
        }

        result.fichiers.forEach((fichier) => {
            const item = document.createElement("li");
            const description = document.createElement("span");
            description.textContent = `${missionStepLabels[fichier.etape]} : ${fichier.nom_original}`;
            if (fichier.supprime_le) {
                description.textContent += " (supprimé, trace conservée)";
            }
            item.append(description);

            if (!fichier.supprime_le) {
                const downloadButton = document.createElement("button");
                downloadButton.className = "btn mission-file-action";
                downloadButton.type = "button";
                downloadButton.textContent = "Télécharger";
                downloadButton.addEventListener("click", () => {
                    void telechargerFichierMission(fichier);
                });

                const deleteButton = document.createElement("button");
                deleteButton.className = "btn mission-file-action";
                deleteButton.type = "button";
                deleteButton.textContent = "Supprimer";
                deleteButton.addEventListener("click", () => {
                    void supprimerFichierMission(fichier);
                });
                item.append(downloadButton, deleteButton);
            }
            missionFilesList.append(item);
        });
        missionMessage.textContent = "";
    } catch (error) {
        missionMessage.textContent = `Impossible de charger les fichiers : ${error.message}`;
    }
}

async function envoyerFichierMission({ input, etape, sendButton, clearButton }) {
    const fichiers = Array.from(input.files);
    const projectId = missionProjectSelect.value;
    if (!fichiers.length || !projectId) {
        return;
    }

    const formData = new FormData();
    fichiers.forEach((fichier) => formData.append("fichier", fichier));
    formData.append("etape", etape);
    missionMessage.textContent = "Envoi du fichier...";
    sendButton.disabled = true;
    clearButton.disabled = true;
    sendButton.textContent = "Envoi...";
    try {
        const result = await requestJson(`/developpeur/projets/${projectId}/fichiers`, {
            method: "POST",
            body: formData
        });
        input.value = "";
        await chargerFichiersMission();
        missionMessage.textContent = `${fichiers.length} fichier(s) envoyé(s) pour l'étape « ${missionStepLabels[etape]} ». ` + result.message;
    } catch (error) {
        missionMessage.textContent = `Impossible d'envoyer le fichier : ${error.message}`;
    } finally {
        sendButton.textContent = "Envoyer";
        mettreAJourActionsDepot();
    }
}

async function telechargerFichierMission(fichier) {
    try {
        const response = await fetch(`${API_BASE_URL}${fichier.url}`, {
            credentials: "include"
        });
        if (!response.ok) {
            throw new Error("Le téléchargement a échoué.");
        }
        const downloadUrl = URL.createObjectURL(await response.blob());
        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = fichier.nom_original;
        document.body.append(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
    } catch (error) {
        missionMessage.textContent = `Impossible de télécharger le fichier : ${error.message}`;
    }
}

async function supprimerFichierMission(fichier) {
    if (!window.confirm(`Supprimer le fichier « ${fichier.nom_original} » ?`)) {
        return;
    }
    try {
        const result = await requestJson(fichier.url, { method: "DELETE" });
        missionMessage.textContent = result.message;
        await chargerFichiersMission();
    } catch (error) {
        missionMessage.textContent = `Impossible de supprimer le fichier : ${error.message}`;
    }
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
    configurerMissionProjets(fiche.projets || []);
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
            configurerMissionProjets(fiche.projets || []);
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

missionProjectSelect.addEventListener("change", () => {
    missionFileInputs.forEach(({ input }) => {
        input.value = "";
    });
    mettreAJourActionsDepot();
    void chargerFichiersMission();
});

missionFileInputs.forEach((fileInput) => {
    fileInput.input.addEventListener("change", mettreAJourActionsDepot);
    fileInput.sendButton.addEventListener("click", () => {
        void envoyerFichierMission(fileInput);
    });
    fileInput.clearButton.addEventListener("click", () => {
        fileInput.input.value = "";
        mettreAJourActionsDepot();
        missionMessage.textContent = "Fichier retiré du champ, aucun envoi effectué.";
    });
});