document.addEventListener("DOMContentLoaded", () => {
    const employes = [
        ["Dupont", "Jean", "comptable", "01/01/2020", 2500],
        ["Martin", "Marie", "developpeur", "01/01/2019", 3000],
        ["Durand", "Pierre", "manager", "01/01/2018", 4000],
        ["Leroy", "Sophie", "developpeur", "01/01/2021", 2800]
    ];

    new DataTable("#employes", {
        data: employes,
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
});