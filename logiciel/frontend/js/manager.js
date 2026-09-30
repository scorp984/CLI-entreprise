  const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:5000`;
  let developpeurs = [];
  const documentsProjetSelect = document.getElementById("documents-projet");
  const documentsResultat = document.getElementById("resultat-documents");
  const documentsList = document.getElementById("documents-list");
  const libellesEtapes = {
    diagramme: "Diagramme",
    dossier: "Dossier avant programmation",
    "compte-rendu": "Tests et compte rendu"
  };

  async function requeteApi(path, options = {}) {
    const reponse = await fetch(`${API_BASE_URL}${path}`, {
      credentials: "include",
      ...options
    });
    let resultat = {};
    try {
      resultat = await reponse.json();
    } catch (error) {
      resultat = {};
    }
    if (!reponse.ok) {
      throw new Error(resultat.error || "La requête API a échoué.");
    }
    return resultat;
  }

  async function chargerProjetsDocuments() {
    try {
      const projets = await requeteApi("/manager/projets");
      documentsProjetSelect.replaceChildren();
      projets.forEach(projet => {
        const option = document.createElement("option");
        option.value = projet.id;
        const membres = (projet.developpeurs || [])
          .map(membre => `${membre.prenom} ${membre.nom}`)
          .join(", ");
        option.textContent = membres ? `${projet.nom} — ${membres}` : projet.nom;
        documentsProjetSelect.append(option);
      });

      documentsProjetSelect.disabled = projets.length === 0;
      if (!projets.length) {
        documentsResultat.textContent = "Aucun projet disponible.";
        documentsList.replaceChildren();
        return;
      }
      documentsProjetSelect.value = String(projets[0].id);
      await chargerDocumentsProjet();
    } catch (error) {
      documentsResultat.textContent = `Impossible de charger les projets : ${error.message}`;
    }
  }

  async function chargerDocumentsProjet() {
    const projetId = documentsProjetSelect.value;
    documentsList.replaceChildren();
    if (!projetId) return;

    documentsResultat.textContent = "Chargement des documents...";
    try {
      const resultat = await requeteApi(`/manager/projets/${projetId}/fichiers`);
      if (documentsProjetSelect.value !== projetId) return;
      if (!resultat.fichiers.length) {
        const emptyItem = document.createElement("li");
        emptyItem.textContent = "Aucun document déposé pour ce projet.";
        documentsList.append(emptyItem);
      }

      resultat.fichiers.forEach(fichier => {
        const item = document.createElement("li");
        const description = document.createElement("span");
        const etape = libellesEtapes[fichier.etape] || fichier.etape;
        const auteur = fichier.depose_par ? `, déposé par ${fichier.depose_par}` : "";
        const statut = fichier.supprime_le ? " (supprimé)" : "";
        description.textContent = `${etape} : ${fichier.nom_original}${auteur}${statut}`;
        item.append(description);

        if (!fichier.supprime_le) {
          const downloadButton = document.createElement("button");
          downloadButton.className = "btn document-download";
          downloadButton.type = "button";
          downloadButton.textContent = "Télécharger";
          downloadButton.addEventListener("click", () => {
            void telechargerDocumentProjet(fichier);
          });
          item.append(downloadButton);
        }
        documentsList.append(item);
      });
      documentsResultat.textContent = "";
    } catch (error) {
      documentsResultat.textContent = `Impossible de charger les documents : ${error.message}`;
    }
  }

  async function telechargerDocumentProjet(fichier) {
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
      documentsResultat.textContent = `Impossible de télécharger le document : ${error.message}`;
    }
  }
 
  function remplirSelects() {
    document.querySelectorAll("#attribuer-employe, #gerer-employe, #qfq-employe").forEach(select => {
      select.replaceChildren();
      if (developpeurs.length) {
        developpeurs.forEach(developpeur => {
          const option = document.createElement("option");
          option.value = developpeur.id;
          option.textContent = `${developpeur.prenom} ${developpeur.nom}`;
          select.append(option);
        });
      } else {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "Aucun développeur disponible";
        select.append(option);
      }
      select.disabled = developpeurs.length === 0;
    });

    const equipeSelect = document.getElementById("equipe-developpeurs");
    equipeSelect.replaceChildren();
    developpeurs.forEach(developpeur => {
      const option = document.createElement("option");
      option.value = developpeur.id;
      option.textContent = `${developpeur.prenom} ${developpeur.nom}`;
      equipeSelect.append(option);
    });
    equipeSelect.disabled = developpeurs.length === 0;
    afficherChampsTachesEquipe();
  }

  function afficherChampsTachesEquipe() {
    const selection = document.getElementById("equipe-developpeurs");
    const zone = document.getElementById("equipe-taches");
    zone.replaceChildren();

    Array.from(selection.selectedOptions).forEach(option => {
      const developpeur = developpeurs.find(item => String(item.id) === option.value);
      if (!developpeur) return;

      const bloc = document.createElement("div");
      bloc.className = "equipe-tache";
      const label = document.createElement("label");
      label.htmlFor = `taches-dev-${developpeur.id}`;
      label.textContent = `Tâches de ${developpeur.prenom} ${developpeur.nom}`;
      const textarea = document.createElement("textarea");
      textarea.id = `taches-dev-${developpeur.id}`;
      textarea.dataset.employeId = developpeur.id;
      textarea.placeholder = "Une tâche par ligne";
      textarea.rows = 3;
      bloc.append(label, textarea);
      zone.append(bloc);
    });
  }

  async function chargerDeveloppeurs() {
    try {
      const employes = await requeteApi("/employes");
      developpeurs = employes.filter(e => e.poste === "developpeur");
      remplirSelects();
    } catch (error) {
      document.querySelectorAll(".resultat").forEach(zone => {
        zone.textContent = `Impossible de charger les développeurs : ${error.message}`;
      });
      console.error(error);
    }
  }

  remplirSelects();
  document.getElementById("equipe-developpeurs").addEventListener("change", afficherChampsTachesEquipe);
  chargerDeveloppeurs();
  chargerProjetsDocuments();
  documentsProjetSelect.addEventListener("change", chargerDocumentsProjet);
 
  // Navigation entre panneaux
  const cards = document.querySelectorAll(".card[data-target]");
  const panels = document.querySelectorAll(".panel");
  cards.forEach(card => {
    card.addEventListener("click", () => {
      cards.forEach(c => c.classList.remove("active"));
      panels.forEach(p => p.classList.remove("visible"));
      card.classList.add("active");
      document.getElementById(card.dataset.target).classList.add("visible");
    });
  });
 
  document.getElementById("logout-card").addEventListener("click", async () => {
    if (!confirm("Se déconnecter ?"))return;
    
    try{
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        credentials: "include"
      });
    } catch (error) {
      console.error("Erreur lors de la déconnexion :", error);
    } finally {
      window.location.href = "index.html";
    }
  });
 
  async function attribuerProjet() {
    const employeId = document.getElementById("attribuer-employe").value;
    const projet = document.getElementById("attribuer-projet").value.trim();
    const taches = document.getElementById("attribuer-taches").value.trim();
    const date = document.getElementById("attribuer-date").value;
    const dev = developpeurs.find(developpeur => String(developpeur.id) === employeId);
    const zone = document.getElementById("resultat-attribuer");
 
    if (!dev || !projet || !taches || !date) {
      zone.textContent = "Merci de choisir un développeur et de renseigner le projet, les tâches et la date de début.";
      return;
    }
 
    zone.textContent = "Attribution du projet en cours...";
    try {
      await requeteApi("/manager/projets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employe_id: Number(employeId),
          nom: projet,
          taches: taches.split(",").map(t => t.trim()).filter(Boolean).map(description => ({
            employe_id: Number(employeId),
            description
          })),
          date_debut: date
        })
      });
      zone.textContent = `Projet « ${projet} » enregistré pour ${dev.prenom} ${dev.nom} (début : ${date}). Les tâches par défaut ont été créées.`;
    } catch (error) {
      zone.textContent = `Impossible d'attribuer le projet : ${error.message}`;
    }
  }
 
  async function gererDeveloppeur() {
    const employeId = document.getElementById("gerer-employe").value;
    const dev = developpeurs.find(developpeur => String(developpeur.id) === employeId);
    const zone = document.getElementById("resultat-gerer");
 
    if (!dev) {
      zone.textContent = "Veuillez choisir un développeur.";
      return;
    }

    zone.textContent = "Chargement de la fiche...";
    try {
      const fiche = await requeteApi(`/manager/developpeurs/${encodeURIComponent(employeId)}/fiche`);
      const projets = fiche.projets || [];
      let texte = `Fiche technique — ${fiche.prenom} ${fiche.nom}\n\n`;
      if (fiche.fiche_technique) {
        const profil = fiche.fiche_technique;
        texte += `Compétences : ${profil.competences}\n`;
        texte += `Disponibilité : ${profil.disponibilite}\n`;
        texte += `Ancienneté : ${profil.anciennete_annees} an(s)\n`;
        texte += `Expérience totale : ${profil.experience_totale_annees} an(s)\n\n`;
      } else {
        texte += "Fiche technique personnelle non renseignée.\n\n";
      }
      texte += projets.length
        ? "Projets et tâches :\n" + projets.map(projet => {
          const equipe = (projet.developpeurs || [])
            .map(membre => `${membre.prenom} ${membre.nom}`)
            .join(", ");
          const taches = projet.taches.map(tache =>
            `  - ${tache.description}${tache.assigne_a ? ` (assignée à ${tache.assigne_a.prenom} ${tache.assigne_a.nom})` : " (tâche commune)"}`
          ).join("\n");
          return `- ${projet.nom} (début : ${projet.date_debut}, statut : ${projet.statut})\n  Équipe : ${equipe || "Non renseignée"}${taches ? `\n${taches}` : "\n  Aucune tâche"}`;
        }).join("\n")
        : "Aucun projet attribué pour l'instant.";
      zone.textContent = texte;
    } catch (error) {
      zone.textContent = `Impossible de charger la fiche : ${error.message}`;
    }
  }
 
  async function quiFaitQuoi() {
    const employeId = document.getElementById("qfq-employe").value;
    const dev = developpeurs.find(developpeur => String(developpeur.id) === employeId);
    const zone = document.getElementById("resultat-qfq");
 
    if (!dev) {
      zone.textContent = "Veuillez choisir un développeur.";
      return;
    }
 
    zone.textContent = "Chargement de ses projets et tâches...";
    try {
      const fiche = await requeteApi(`/manager/developpeurs/${encodeURIComponent(employeId)}/fiche`);
      const projets = fiche.projets || [];
      let texte = `Fiche de ${fiche.prenom} ${fiche.nom}\n`;
      texte += `Embauche : ${fiche.date_embauche}\n`;
      if (fiche.fiche_technique) {
        texte += `Compétences : ${fiche.fiche_technique.competences}\n`;
        texte += `Disponibilité : ${fiche.fiche_technique.disponibilite}\n`;
        texte += `Expérience totale : ${fiche.fiche_technique.experience_totale_annees} an(s)\n`;
      } else {
        texte += "Fiche technique non renseignée.\n";
      }
      texte += projets.length
        ? "\nProjets :\n" + projets.map(projet => {
          const equipe = (projet.developpeurs || [])
            .map(membre => `${membre.prenom} ${membre.nom}`)
            .join(", ");
          const taches = (projet.taches || []).map(tache =>
            `  - ${tache.description}${tache.assigne_a ? ` (assignée à ${tache.assigne_a.prenom} ${tache.assigne_a.nom})` : " (tâche commune)"}`
          ).join("\n");
          return `\n${projet.nom} | ${projet.date_debut} | ${projet.statut}\nÉquipe : ${equipe || "Non renseignée"}\n${taches || "Aucune tâche enregistrée."}`;
        }).join("\n")
        : "\nAucun projet attribué pour l'instant.";
      zone.textContent = texte;
    } catch (error) {
      zone.textContent = `Aucune affectation trouvée : ${error.message}`;
    }
  }
 
  async function equipeProjet() {
    const projet = document.getElementById("equipe-projet").value.trim();
    const date = document.getElementById("equipe-date").value;
    const equipeSelect = document.getElementById("equipe-developpeurs");
    const employeIds = Array.from(equipeSelect.selectedOptions, option => Number(option.value));
    const membres = developpeurs.filter(developpeur => employeIds.includes(developpeur.id));
    const zone = document.getElementById("resultat-equipe");
 
    if (!projet || !date) {
      zone.textContent = "Merci de renseigner le projet et la date de début.";
      return;
    }
    if (!developpeurs.length || equipeSelect.disabled) {
      zone.textContent = "Aucun développeur n'est disponible pour ce projet.";
      return;
    }
    if (!employeIds.length || membres.length !== employeIds.length) {
      zone.textContent = "Sélectionnez au moins un développeur valide pour l'équipe.";
      return;
    }

    const taches = Array.from(document.querySelectorAll("#equipe-taches textarea"))
      .flatMap(textarea => textarea.value.split(/\r?\n/)
        .map(description => description.trim())
        .filter(Boolean)
        .map(description => ({
          employe_id: Number(textarea.dataset.employeId),
          description
        })));
    const membresAvecTaches = new Set(taches.map(tache => tache.employe_id));
    if (membres.some(membre => !membresAvecTaches.has(membre.id))) {
      zone.textContent = "Ajoutez au moins une tâche pour chaque développeur sélectionné.";
      return;
    }
 
    zone.textContent = "Enregistrement de l'équipe...";
    try {
      await requeteApi("/manager/projets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employe_ids: employeIds,
          nom: projet,
          taches,
          date_debut: date
        })
      });
      zone.textContent = `Projet « ${projet} » attribué à ${membres.map(membre => `${membre.prenom} ${membre.nom}`).join(", ")} (début : ${date}).`;
    } catch (error) {
      zone.textContent = `Impossible de constituer l'équipe : ${error.message}`;
    }
  }

  