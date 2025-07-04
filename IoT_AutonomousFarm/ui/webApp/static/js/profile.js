document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("user_id");
  
    if (!token || !userId) {
      alert("You are not logged in.");
      window.location.href = "loginform.html";
      return;
    }
  
    fetch("./json/WebApp_config.json")
      .then(res => res.json())
      .then(config => {
        const catalog_url = config.catalog_url;
  
        return fetch(`${catalog_url}/get_user_info?user_id=${userId}`, {
          headers: {
            "Authorization": `Bearer ${token}`
          }
        });
      })
      .then(res => res.json())
      .then(data => {
        if (data && data.username) {
          document.getElementById("username").value = data.username;
          document.getElementById("email").value = data.email || "";
            document.getElementById("password").value = data.phone || "";
            document.getElementById("repassword").value = data.phone || "";
          // passwords are not returned from backend for security
        }
      })
      .catch(err => {
        console.error("Failed to load user info:", err);
        alert("Failed to load user info.");
      });
  });
  


//   submit changes 

document.getElementById("profileForm").addEventListener("submit", function(event) {
    event.preventDefault();
  
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("user_id");
  
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const repassword = document.getElementById("repassword").value;
    const email = document.getElementById("email").value;
  
    if (password !== repassword) {
      alert("Passwords do not match.");
      return;
    }
  
    fetch("./json/WebApp_config.json")
      .then(res => res.json())
      .then(config => {
        const catalog_url = config.catalog_url;
  
        return fetch(`${catalog_url}/update_user_info`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({
            user_id: userId,
            username: username,
            new_password: password,
            email: email
          })
        });
      })
      .then(res => res.json())
      .then(data => {
        alert(data.message || "User updated successfully.")
        location.reload();
        // change the username stored in localStorage
        localStorage.setItem("username", username);
      })
      .catch(err => {
        console.error("Error updating user info:", err);
        alert("Failed to update user.");
      });
  });

// document.getElementById("telegramForm").addEventListener("submit", function(event) {
//   event.preventDefault();

//   const token = localStorage.getItem("token");
//   const userId = localStorage.getItem("user_id");
//   const otp = document.getElementById("otp").value;

//   if (!otp) {
//     alert("Please enter the OTP.");
//     return;
//   }

//   fetch("./json/WebApp_config.json")
//     .then(res => res.json())
//     .then(config => {
//       const catalog_url = config.catalog_url;

//       return fetch(`${catalog_url}/verify_telegram_otp`, {
//         method: "POST",
//         headers: {
//           "Content-Type": "application/json",
//           "Authorization": `Bearer ${token}`
//         },
//         body: JSON.stringify({
//           user_id: userId,
//           otp: otp
//         })
//       });
//     })
//     .then(async response => {
//       if (!response.ok) {
//           const err = await response.json();
//           throw new Error(err.error);
//       }
//       return response.json();
//     })
//     .then(data => {
//       if (data) {
//         alert("OTP verified successfully!");
//         document.getElementById("otp").value = ""; // clear the OTP input
//       } else {
//         alert("Failed to verify OTP.");
//       }
//     })
//     .catch(err => {
//       console.error("Error verifying OTP:", err);
//       alert(err.message || "Failed to verify OTP.");
//       document.getElementById("otp").value = ""; // clear the OTP input
//     });
// });