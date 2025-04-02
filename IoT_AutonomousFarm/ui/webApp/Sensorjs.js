$(document).ready(function () {
    var zindex = 10;

    // When clicking on a card, only show the card (don't close it)
    $("div.card").click(function (e) {
        e.preventDefault();

        if (!$(this).hasClass("d-card-show")) {
            if (!$("div.dashboard-cards").hasClass("showing")) {
                $("div.dashboard-cards").addClass("showing");
            }
            $(this).css({ zIndex: zindex }).addClass("d-card-show");
            zindex++;
        }
    });

    // Close the card only when clicking the close button
    $(".close-btn").click(function (e) {
        e.stopPropagation(); // Prevent triggering the card click event

        var card = $(this).closest(".card"); // Find the closest parent card
        card.removeClass("d-card-show");

        // If no more cards are open, remove "showing" class from dashboard
        if ($(".card.d-card-show").length === 0) {
            $("div.dashboard-cards").removeClass("showing");
        }
    });
});


// ***********************************************//
// function fetchDevices() {
//     $.ajax({
//         url: "http://0.0.0.0:8080/get_all_device_info",
//         type: "GET",
//         dataType: "json",
//         success: function(response) {
            
//             console.log("Success:", response);
//             // let responses = JSON.stringify(response)

//             let tableBody = $("#devicesTable tbody");
//             tableBody.empty(); // Clear previous data
            
//             // Loop through JSON response and append rows to the table
//             response.forEach(device => {
              
//                 let row = `
//                     <tr>
//                         <td>${device.device_id}</td>
//                         <td>${device.greenhouse_id}</td>
//                         <td>${device.name}</td>
//                         <td>${device.type}</td>
//                         <td>${device.type}</td>
//                     </tr>
//                 `;
//                 tableBody.append(row);
//             });

//             $("#status").text("Devices loaded successfully!");
//         },
//         error: function(xhr, status, error) {
//             console.error("Error:", error);
//             $("#status").text("Failed to load devices.");
//         }
//     });
// }

    

   

