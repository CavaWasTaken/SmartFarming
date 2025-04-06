function registerUser() {
    // read the values from the input fields and remove any leading/trailing whitespace
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const confirmPassword = document.getElementById("confirmPassword").value.trim();

    // check if any of the fields are empty
    if (!username || !email || !password || !confirmPassword) {
        alert("Registration failed: All fields are required!");
        return;
    }

    // check if the password and confirm password match
    if (password !== confirmPassword) {
        alert("Registration failed: Passwords do not match!");
        return;
    }
    // check if the password is at least 8 characters long
    if (password.length < 8) {
        alert("Registration failed: Password must be at least 8 characters long!");
        return;
    }
    // check if the username is valid (only alphanumeric characters and underscores)
    const usernamePattern = /^[a-zA-Z0-9_]+$/;
    if (!usernamePattern.test(username)) {
        alert("Registration failed: Username can only contain letters, numbers, and underscores!");
        return;
    }
    // check if the username is at least 3 characters long
    if (username.length < 3) {
        alert("Registration failed: Username must be at least 3 characters long!");
        return;
    }

    const formData = {
        username: username,
        email: email,
        password: password
    };

    // read from the config file to get the API URL
    fetch("../json/WebApp_config.json")    // this path is relative to the HTML file
    .then(response => response.json())
    .then(config => {
        const catalog_url = config.catalog_url; // read the catalog URL from the config file

        // use the catalog URL to do the HTTP request
        return fetch(`${catalog_url}/register`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(formData)
        });
    })
    .then(async response => {
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error);
        }
        return response.json();
    })
    .then(data => {
        if (data && data.user_id != null) {
            console.log("Registration successful:", data);
            alert("Registration successful!");
            document.getElementById("registerForm").reset();
            // redirect to the login page
            window.location.href = "loginform.html";
        } else {
            console.error("Registration failed:", data.error);
            alert("An error occurred during registration");
            document.getElementById("registerForm").reset();
        }
    })
    .catch(error => {
        console.error("Error:", error.message);
        alert("An error occurred during registration");
        document.getElementById("registerForm").reset();
    });
}