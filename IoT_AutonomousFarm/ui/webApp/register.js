function registerUser() {
    //data from the form
    let username = document.getElementById("username").value;
    let email = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    

    let data ={
        username : username,
        email : email,
        password : password
    }

    console.log(JSON.stringify(data))
    $.ajax({
        url: "http://0.0.0.0:8080/register",
        type: "POST",
        contentType: "application/json", 
        dataType: "json",
        data: JSON.stringify(data),
        
        success: function(response) 
        {
            console.log("Success:", response);
            // let responses = JSON.stringify(response)

            if(response && response.message){
                $("#status").text(response.message); 
            } else {
                $("#status").text("Registration successful, but no message returned from server.");
            }
        },
        error: function(xhr, status, error) {
            console.log("Error:", error);
            $("#status").text("Failed to register user");
        }
    });
}