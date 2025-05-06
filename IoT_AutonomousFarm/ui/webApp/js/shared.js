
  document.addEventListener("DOMContentLoaded", () => {
    fetch("partialheader.html")
    .then(res => res.text())
    .then(data => {
      document.getElementById("header-container").innerHTML = data;

      const token = localStorage.getItem("token");
      const username = localStorage.getItem("username");
      const userProfile = document.getElementById("userProfile");
  
      if (userProfile) {
        if (token && username) {
          userProfile.textContent = `Welcome, ${username}`;
          userProfile.style.cursor = "pointer";
          userProfile.onclick = () => {
            const confirmLogout = confirm("Log out?");
            if (confirmLogout) {
              
              localStorage.removeItem("token");
              localStorage.removeItem("user_id");
              localStorage.removeItem("username");
              localStorage.removeItem("greenhouse_id");
              localStorage.removeItem("greenhouse_name");
              localStorage.removeItem("greenhouse_location");
              window.location.href = "loginform.html";
            }
          };
        } else {
          userProfile.textContent = "Login";
          userProfile.style.cursor = "pointer";
          userProfile.onclick = () => {
            window.location.href = "./loginform.html";
          };
        }
      }
    });
   
  });
