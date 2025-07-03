document.addEventListener("DOMContentLoaded", () => {
  fetch("partialheader.html")
    .then(res => res.text())
    .then(data => {
      document.getElementById("header-container").innerHTML = data;

      const token = localStorage.getItem("token");
      const username = localStorage.getItem("username");

      const userInfoLink = document.getElementById("userinfo");
      const userProfile = document.getElementById("userProfile");
      const greenhouseLink = document.getElementById("greenhouse");

      if (token && username) {
        //  Show profile name
        if (userProfile) {
          userProfile.textContent = `Welcome, ${username}`;
          userProfile.style.cursor = "pointer";
          userProfile.onclick = () => {
            const confirmLogout = confirm("Log out?");
            if (confirmLogout) {
              localStorage.clear();
              window.location.href = "loginform.html";
            }
          };
        }

        // Show User Profile menu item
        if (userInfoLink) {
          userInfoLink.style.display = "inline-block";
        }
      } else {
        // hide User Profile menu item
        if (userInfoLink) {
          userInfoLink.style.display = "none";
        }

        // hide Greenhouse menu item
        if (greenhouseLink) {
          greenhouseLink.style.display = "none";
        }

        // set the login link
        if (userProfile) {
          userProfile.textContent = "Login";
          userProfile.style.cursor = "pointer";
          userProfile.onclick = () => {
            window.location.href = "loginform.html";
          };
        }
      }
    });
});

