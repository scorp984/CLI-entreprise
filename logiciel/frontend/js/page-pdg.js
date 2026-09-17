const logoutButton = document.querySelector("#logout-button");

logoutButton.addEventListener("click", async function () {
    try {
        await fetch("http://127.0.0.1:5000/auth/logout", {
            method: "POST",
            credentials: "include"
        });
    } finally {
        window.location.href = "page-connect.html";
    }
});
