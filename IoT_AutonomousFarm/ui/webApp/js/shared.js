
  document.addEventListener("DOMContentLoaded", () => {
    fetch("html/header.html")
      .then(response => response.text())
      .then(data => {
        document.getElementById("main-header").innerHTML = data;

        // Optional: run any header-specific logic after loading
        const token = localStorage.getItem("token");
        const username = localStorage.getItem("username");
        const profileElem = document.getElementById("userProfile");

        if (token && username) {
          profileElem.textContent = username;
        } else {
          profileElem.textContent = "Login";
          profileElem.addEventListener("click", () => {
            window.location.href = "loginform.html";
          });
        }
      });
  });

