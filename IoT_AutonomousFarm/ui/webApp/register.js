function registerUser() {
    // Data from the form
    let username = document.getElementById("username").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;

    $.ajax({
        url: "/register",
        type: "POST",
        contentType: "application/json", 
        data: JSON.stringify({
            username: username,
            email: email,
            password: password
        }),
        dataType: "json",
        success: function(response) {
            console.log("Success:", response);
            if(response && response.message){
                $("#status").text(response.message); 
            } else {
                $("#status").text("Registration successful, but no message returned from server.");
            }
        },
        error: function(xhr, status, error) {
            console.log("Error:", error);
            console.log("XHR:", xhr);
            console.log("Status:", status);
            console.log("Response Text:", xhr.responseText);
            $("#status").text("Failed to register user: " + xhr.responseText);
        }
    });
}