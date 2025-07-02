function loginUser() {        
    // read the values from the input fields and remove any leading/trailing whitespace
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    // check if any of the fields are empty
    if (!username || !password) {
        alert("All fields are required!");
        return;
    }

    const formData = {
        username: username,
        password: password
    };

    // read from the config file to get the API URL
    fetch("./json/WebApp_config.json")    // this path is relative to the HTML file
    .then(response => response.json())
    .then(config => {
        console.log("Config loaded:", config);
        const catalog_url = config.catalog_url; // read the catalog URL from the config file
        console.log("Using catalog URL:", catalog_url);
        console.log("Full login URL:", `${catalog_url}/login`);

        // use the catalog URL to do the HTTP request
        return fetch(`${catalog_url}/login`, {
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
            console.log("Logged In successful!");
            alert("Logged In successful!");

            // save the logged-id user info and token in local storage
            localStorage.setItem("user_id", data.user_id);
            localStorage.setItem("username", data.username);
            localStorage.setItem("token", data.token);

            document.getElementById("loginForm").reset(); // reset the form
            window.location.href = "greenhouses.html"; // redirect to another page
        } else {
            console.error("Login failed:", data.error);
            alert("An error occurred during login");
            document.getElementById("loginForm").reset(); // reset the form
        }
    })
    .catch(error => {
        console.error("Full error:", error);
        alert(`An error occurred during login`);
        document.getElementById("loginForm").reset(); // reset the form
    });
}