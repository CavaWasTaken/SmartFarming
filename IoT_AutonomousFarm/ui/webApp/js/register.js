function registerUser() {
    // read the values from the input fields and remove any leading/trailing whitespace
    const username = document.getElementById("username").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    // check if any of the fields are empty
    if (!username || !email || !password) {
        alert("All fields are required!");
        return;
    }

    const formData = {
        username: username,
        email: email,
        password: password
    };

    // read from the config file to get the API URL
    fetch("json/WebApp_config.json")    // this path is relative to the HTML file
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
            console.log("Registration successful:", data);
            alert("Registration successful! Please check your email for verification.");
            document.getElementById("registerForm").reset();
        })
        .catch(error => {
            console.error("Error:", error.message);
            alert("Registration failed: " + error.message);
            document.getElementById("registerForm").reset();
        });
}