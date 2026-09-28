const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:5000`;
const form = document.querySelector("#creation-compte");
const editForm = document.querySelector("#edition-compte");
const editSection = document.querySelector("#edition-section");
const message = document.querySelector("#inscription-message");
const accountsBody = document.querySelector("#comptes-body");
let currentAccountId = null;



async function requestJson(url, options = {}) {
    const response = await fetch(url, {
        credentials: "include",
        ...options
    });
    const result = await response.json();
    if (!response.ok) {
        throw new Error(result.error || "La requête a échoué.");
    }
    return result;
}

function showMessage(text, isError = false) {
    message.textContent = text;
    message.classList.toggle("is-error", isError);
}

function isActive(account) {
    return account.actif === true || account.actif === 1;
}

function addActionButton(row, label, className, onClick) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = className;
    button.textContent = label;
    button.addEventListener("click", onClick);
    row.append(button);
}

function startEditing(account) {
    document.querySelector("#edit-id").value = account.id;
    document.querySelector("#edit-identifiant").value = account.identifiant;
    const roleSelect = document.querySelector("#edit-role");
    roleSelect.value = account.role;
    roleSelect.disabled = account.role === "pdg";
    document.querySelector("#edit-password").value = "";
    document.querySelector("#edit-actif").checked = isActive(account);
    editSection.hidden = false;
    editSection.scrollIntoView({ behavior: "smooth", block: "start" });
    document.querySelector("#edit-identifiant").focus();
}

function renderAccounts(accounts) {
    accountsBody.replaceChildren();
    if (!accounts.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 5;
        cell.textContent = "Aucun compte enregistré.";
        row.append(cell);
        accountsBody.append(row);
        return;
    }

    accounts.forEach((account) => {
        const row = document.createElement("tr");
        const values = [
            account.identifiant,
            account.role,
            isActive(account) ? "Actif" : "Désactivé",
            account.date_creation ? new Date(account.date_creation).toLocaleDateString("fr-FR") : "—"
        ];
        values.forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.append(cell);
        });

        const actions = document.createElement("td");
        actions.className = "row-actions";
        addActionButton(actions, "Modifier", "text-button", () => startEditing(account));
        addActionButton(
            actions,
            isActive(account) ? "Désactiver" : "Réactiver",
            "text-button",
            () => setAccountActive(account, !isActive(account))
        );
        if (account.id !== currentAccountId) {
            addActionButton(actions, "Supprimer", "text-button danger-button", () => deleteAccount(account));
        }
        row.append(actions);
        accountsBody.append(row);
    });
}

async function loadAccounts() {
    accountsBody.innerHTML = '<tr><td colspan="5">Chargement des comptes…</td></tr>';
    try {
        const [accounts, currentAccount] = await Promise.all([
            requestJson(`${API_BASE_URL}/auth/comptes`),
            requestJson(`${API_BASE_URL}/auth/me`)
        ]);
        currentAccountId = currentAccount.id;
        renderAccounts(accounts);
    } catch (error) {
        accountsBody.replaceChildren();
        showMessage(error.message, true);
    }
}

async function setAccountActive(account, actif) {
    try {
        const result = await requestJson(`${API_BASE_URL}/auth/comptes/${account.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ actif })
        });
        showMessage(result.message);
        await loadAccounts();
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function deleteAccount(account) {
    if (!window.confirm(`Supprimer le compte « ${account.identifiant} » ?`)) {
        return;
    }
    try {
        const result = await requestJson(`${API_BASE_URL}/auth/comptes/${account.id}`, {
            method: "DELETE"
        });
        showMessage(result.message);
        await loadAccounts();
    } catch (error) {
        showMessage(error.message, true);
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const nom = document.querySelector("#nom").value.trim();
    const prenom = document.querySelector("#prenom").value.trim();
    const identifiant = document.querySelector("#username").value.trim();
    const motDePasse = document.querySelector("#password").value;
    const role = document.querySelector("#role").value;
    const dateEmbauche = document.querySelector("#date-embauche").value;
    const salaireSaisi = document.querySelector("#salaire").value;
    const salaire = Number(salaireSaisi);

    if (!nom || !prenom || !identifiant || !motDePasse || !dateEmbauche
        || salaireSaisi === "" || !Number.isFinite(salaire) || salaire < 0) {
        showMessage("Tous les champs doivent être renseignés correctement.", true);
        return;
    }

    try {
        const result = await requestJson(`${API_BASE_URL}/auth/comptes`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                nom,
                prenom,
                identifiant,
                mot_de_passe: motDePasse,
                role,
                poste: role,
                date_embauche: dateEmbauche,
                salaire
            })
        });
        form.reset();
        showMessage(result.message);
        await loadAccounts();
    } catch (error) {
        showMessage(error.message, true);
    }
});

editForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const roleSelect = document.querySelector("#edit-role");
    const motDePasse = document.querySelector("#edit-password").value;
    const changes = {
        identifiant: document.querySelector("#edit-identifiant").value.trim(),
        actif: document.querySelector("#edit-actif").checked
    };
    if (!roleSelect.disabled) {
        changes.role = roleSelect.value;
    }
    if (motDePasse) {
        changes.mot_de_passe = motDePasse;
    }

    try {
        const result = await requestJson(
            `${API_BASE_URL}/auth/comptes/${document.querySelector("#edit-id").value}`,
            {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(changes)
            }
        );
        editSection.hidden = true;
        editForm.reset();
        showMessage(result.message);
        await loadAccounts();
    } catch (error) {
        showMessage(error.message, true);
    }
});


document.querySelector("#cancel-edit").addEventListener("click", () => {
    editSection.hidden = true;
    editForm.reset();
});

document.querySelector("#refresh-comptes").addEventListener("click", loadAccounts);
loadAccounts();