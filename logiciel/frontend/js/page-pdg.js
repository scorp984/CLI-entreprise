const API_BASE_URL = `${window.location.protocol}//${window.location.hostname}:5000`;
const logoutButton = document.querySelector("#logout-button");

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
