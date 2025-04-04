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


document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("thresholdModal");
    const sensorIdInput = document.getElementById("sensor-id");
    const minThresholdInput = document.getElementById("min-threshold");
    const maxThresholdInput = document.getElementById("max-threshold");
    const thresholdForm = document.getElementById("thresholdForm");
  
    // Open modal and populate with sensor details
    document.querySelectorAll(".change-values-btn").forEach(button => {
      button.addEventListener("click", () => {
        const sensorId = button.getAttribute("data-sensor-id");
        const thresholdMin = button.getAttribute("data-threshold-min");
        const thresholdMax = button.getAttribute("data-threshold-max");
  
        // Populate modal fields
        sensorIdInput.value = sensorId;
        minThresholdInput.value = thresholdMin;
        maxThresholdInput.value = thresholdMax;
  
        // Show modal
        modal.style.display = "block";
      });
    });
  
    // Close modal
    window.closeModal = function () {
      modal.style.display = "none";
    };
  
    // Handle form submission
    thresholdForm.addEventListener("submit", event => {
      event.preventDefault();
  
      const sensorId = sensorIdInput.value;
      const minThreshold = minThresholdInput.value;
      const maxThreshold = maxThresholdInput.value;
  
      // Send updated thresholds to the backend
      fetch("/set_sensor_threshold", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          sensor_id: sensorId,
          threshold: {
            min: minThreshold,
            max: maxThreshold
          }
        })
      })
        .then(response => response.json())
        .then(data => {
          alert(data.message || "Threshold updated successfully!");
          closeModal();
        })
        .catch(error => {
          console.error("Error updating thresholds:", error);
          alert("Failed to update thresholds.");
        });
    });
  });
    

   

