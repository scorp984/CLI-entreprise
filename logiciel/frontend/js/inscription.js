const form = document.querySelector("#creation-compte");
const message = document.querySelector("#inscription-message");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
});

const usernameInput = document.querySelector("#username").value;
const passwordInput = document.querySelector("#password").value;