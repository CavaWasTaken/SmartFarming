document.addEventListener("DOMContentLoaded", function() {
    const token = localStorage.getItem("token");
    const userId = localStorage.getItem("user_id");
    const username = localStorage.getItem("username");

    if (!token || !userId || !username) {
        alert("You are not logged in. Please log in to access this page.");
        window.location.href = "loginform.html"; // redirect to login page
    }
});

function addGreenhouse() {        
    // Read the values from the input fields and remove any leading/trailing whitespace
    const greenhouseName = document.getElementById("greenhouse-name").value.trim();
    const greenhouseLocation = document.getElementById("greenhouse-location").value.trim();
    const userId = localStorage.getItem("user_id");

    // Check if any of the fields are empty
    if (!greenhouseName || !greenhouseLocation) {
        alert("Both name and location are required!");
        return;
    }
    
    // Example JSON data for thingspeak_config
    const thingspeak_config = {
        read_key: "",
        write_key: "",
        channel_id: ""
    };

    const formData = {
        name: greenhouseName,
        location: greenhouseLocation,
        user_id: userId,
        thingspeak_config: thingspeak_config,
    };

    // Read from the config file to get the API URL
    fetch("./json/WebApp_config.json")    // This path is relative to the HTML file
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
    .then(async response => {
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error);
        }
        return response.json();
    })
    .then(data => {
        alert(data.message || "Greenhouse added successfully!");
        // redirect to the greenhouses page
        window.location.href = "greenhouses.html"; // Redirect to the greenhouses page
    })
    .catch(error => {
        console.error("Error:", error.message);
        alert("An error occurred while adding the greenhouse.");
        document.getElementById("addGreenhouseForm").reset(); // Reset the form
    });
}

document.getElementById("AddGreenhouseButton")?.addEventListener("click", function () {
    addGreenhouse();
});