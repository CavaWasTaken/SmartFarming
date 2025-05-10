function addGreenhouse() {        
    // Read the values from the input fields and remove any leading/trailing whitespace
    const greenhouseName = document.getElementById("greenhouse-name").value.trim();
    const greenhouseLocation = document.getElementById("greenhouse-location").value.trim();

    // Check if any of the fields are empty
    if (!greenhouseName || !greenhouseLocation) {
        alert("Both name and location are required!");
        return;
    }

    // Get the logged-in user's ID from localStorage
    const userId = localStorage.getItem("user_id");
    if (!userId) {
         alert("User is not logged in. Please log in to add a greenhouse.");
        return;
    }
    // Example JSON data for thingspeak_config
    const thingspeak_config = {
        api_key: "",
        channel_id: ""
    };

    const formData = {
        name: greenhouseName,
        location: greenhouseLocation,
        user_id: userId,
        thingspeak_config: thingspeak_config,
    };

    // Read from the config file to get the API URL
    fetch("../json/WebApp_config.json")    // This path is relative to the HTML file
    .then(response => response.json())
    .then(config => {
        const catalog_url = config.catalog_url; // Read the catalog URL from the config file

        // Use the catalog URL to do the HTTP request
        return fetch(`${catalog_url}/add_greenhouse`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(formData)
        });
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Failed to add greenhouse");
        }
        return response.json();
    })
    .then(data => {
        alert(data.message || "Greenhouse added successfully!");
        // Optionally, reload the page or redirect the user
        location.reload();
    })
    .catch(error => {
        console.error("Error:", error.message);
        alert("An error occurred while adding the greenhouse.");
    });
}