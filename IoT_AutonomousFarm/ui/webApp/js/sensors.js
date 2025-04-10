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
  const token = localStorage.getItem("token");
  const userId = localStorage.getItem("user_id");
  const username = localStorage.getItem("username");

  const greenhouseId = localStorage.getItem("greenhouse_id");
  const greenhouseName = localStorage.getItem("greenhouse_name");
  const greenhouseLocation = localStorage.getItem("greenhouse_location");

  if (!token || !userId || !username) {
    alert("You are not logged in. Please log in to access this page.");
    window.location.href = "loginform.html"; // redirect to login page
  }

  if (!greenhouseId || !greenhouseName || !greenhouseLocation) {
    alert(
      "No greenhouse selected. Please select a greenhouse to access this page."
    );
    window.location.href = "greenhouses.html"; // redirect to available greenhouses page
  }

  document.getElementById(
    "username-display"
  ).textContent = `Greenhouse owner: ${username}`;

  document.getElementById(
    "title"
  ).textContent = `${greenhouseName} - ${greenhouseLocation}`;

  document.getElementById("logout-button").addEventListener("click", () => {
    // clear the token and user information from local storage and redirect to login page
    localStorage.removeItem("token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    localStorage.removeItem("greenhouse_id");
    localStorage.removeItem("greenhouse_name");
    localStorage.removeItem("greenhouse_location");
    window.location.href = "loginform.html";
  });

  // read from the config file to get the API URL
  fetch("../json/WebApp_config.json") // this path is relative to the HTML file
    .then((response) => response.json())
    .then((config) => {
      const catalog_url = config.catalog_url; // read the catalog URL from the config file

      // use the catalog URL to do the HTTP request
      const formData = {
        greenhouse_id: greenhouseId,
      };
      const queryParams = new URLSearchParams(formData).toString();
      return fetch(
        `${catalog_url}/get_greenhouse_configurations?${queryParams}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );
    })
    .then(async (response) => {
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.message);
      }
      return response.json();
    })
    .then((data) => {
      const sensors = data.sensors;
      
     
      const dashboardCards = document.querySelector(".dashboard-cards");

      sensors.forEach((sensor) => {
        
        console.log(sensor.threshold);

        // handle the threshold in the special case of NPK sensor
        if (sensor.type === "NPK")
        {
          minThreshold =
            sensor.threshold.N.min +
            ", " +
            sensor.threshold.P.min +
            ", " +
            sensor.threshold.K.min;
          maxThreshold =
            sensor.threshold.N.max +
            ", " +
            sensor.threshold.P.max +
            ", " +
            sensor.threshold.K.max;
        } else {
          minThreshold = sensor.threshold.min;
          maxThreshold = sensor.threshold.max;
        }

        // create a card for each sensor
        const card = document.createElement("div");

        card.className = "card";

        card.innerHTML = `
                <div class="card-img">
                    <svg fill="#e1c61b" viewBox="-5.5 0 32 32" version="1.1" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <title>light</title> <path d="M11.875 6v2.469c0 0.844-0.375 1.25-1.156 1.25s-1.156-0.406-1.156-1.25v-2.469c0-0.813 0.375-1.219 1.156-1.219s1.156 0.406 1.156 1.219zM14.219 9.25l1.438-2.031c0.469-0.625 1.063-0.75 1.656-0.313s0.656 1 0.188 1.688l-1.438 2c-0.469 0.688-1.031 0.75-1.656 0.313-0.594-0.438-0.656-0.969-0.188-1.656zM5.781 7.25l1.469 2c0.469 0.688 0.406 1.219-0.219 1.656-0.594 0.469-1.156 0.375-1.625-0.313l-1.469-2c-0.469-0.688-0.406-1.219 0.219-1.656 0.594-0.469 1.156-0.375 1.625 0.313zM10.719 11.125c2.688 0 4.875 2.188 4.875 4.875 0 2.656-2.188 4.813-4.875 4.813s-4.875-2.156-4.875-4.813c0-2.688 2.188-4.875 4.875-4.875zM1.594 11.813l2.375 0.75c0.781 0.25 1.063 0.719 0.813 1.469-0.219 0.75-0.75 0.969-1.563 0.719l-2.313-0.75c-0.781-0.25-1.063-0.75-0.844-1.5 0.25-0.719 0.75-0.938 1.531-0.688zM17.5 12.563l2.344-0.75c0.813-0.25 1.313-0.031 1.531 0.688 0.25 0.75-0.031 1.25-0.844 1.469l-2.313 0.781c-0.781 0.25-1.281 0.031-1.531-0.719-0.219-0.75 0.031-1.219 0.813-1.469zM10.719 18.688c1.5 0 2.719-1.219 2.719-2.688 0-1.5-1.219-2.719-2.719-2.719s-2.688 1.219-2.688 2.719c0 1.469 1.188 2.688 2.688 2.688zM0.906 17.969l2.344-0.75c0.781-0.25 1.313-0.063 1.531 0.688 0.25 0.75-0.031 1.219-0.813 1.469l-2.375 0.781c-0.781 0.25-1.281 0.031-1.531-0.719-0.219-0.75 0.063-1.219 0.844-1.469zM18.219 17.219l2.344 0.75c0.781 0.25 1.063 0.719 0.813 1.469-0.219 0.75-0.719 0.969-1.531 0.719l-2.344-0.781c-0.813-0.25-1.031-0.719-0.813-1.469 0.25-0.75 0.75-0.938 1.531-0.688zM3.938 23.344l1.469-1.969c0.469-0.688 1.031-0.781 1.625-0.313 0.625 0.438 0.688 0.969 0.219 1.656l-1.469 1.969c-0.469 0.688-1.031 0.813-1.656 0.375-0.594-0.438-0.656-1.031-0.188-1.719zM16.063 21.375l1.438 1.969c0.469 0.688 0.406 1.281-0.188 1.719s-1.188 0.281-1.656-0.344l-1.438-2c-0.469-0.688-0.406-1.219 0.188-1.656 0.625-0.438 1.188-0.375 1.656 0.313zM11.875 23.469v2.469c0 0.844-0.375 1.25-1.156 1.25s-1.156-0.406-1.156-1.25v-2.469c0-0.844 0.375-1.25 1.156-1.25s1.156 0.406 1.156 1.25z"></path> </g></svg>
                </div>
                <div class="desc">
                    <h6 class="primary-text">
                        ${sensor.name}
                    </h6>
                </div>
                <button class="primary-text treshbtn" id="set-threshold-button-${sensor.sensor_id}">
                    Set Threshold
                </button>
                <div class="details">
                    <div class="rating">
                        <h6 class="primary-text">${sensor.type}</h6>
                        <h6 class="secondary-text">Type</h6>  
                    </div>
                    <div class="rating">
                        <h6 class="primary-text">${sensor.unit}</h6>
                        <h6 class="secondary-text">Unit</h6>
                    </div>
                    <div class="rating">
                        <h6 class="primary-text">${minThreshold}</h6>
                        <h6 class="secondary-text">Min Threshold</h6>
                    </div>
                    <div class="rating">
                        <h6 class="primary-text">${maxThreshold}</h6>
                        <h6 class="secondary-text">Max Threshold</h6>
                    </div>
                </div>`;

        dashboardCards.appendChild(card);

        const setThresholdBtn = card.querySelector(`#set-threshold-button-${sensor.sensor_id}`);

        setThresholdBtn.addEventListener("click", () => {
          const modal = document.createElement("div");
          modal.className = "modal d-flex";

          modal.innerHTML = `
        <div class="modal-content">
            <span class="close" style="float: right; font-size: 24px; cursor: pointer;">&times;</span>
            <h2>Set Threshold for ${sensor.name}</h2>
            <form id="thresholdForm-${sensor.sensor_id}">
                <label for="min-threshold">Min Threshold:</label>
                <input type="number" id="min-threshold" value="${
                  sensor.threshold?.min || 0
                }" required />
                </br>
                <label for="max-threshold">Max Threshold:</label>
                <input type="number" id="max-threshold" value="${
                  sensor.threshold?.max || 0
                }" required />

                <button type="submit">Save</button>
            </form>
        </div>
    `;

          document.body.appendChild(modal);

          modal.querySelector(".close").addEventListener("click", () => {
            modal.remove();
          });

          modal
            .querySelector(`#thresholdForm-${sensor.sensor_id}`)
            .addEventListener("submit", (e) => {
              e.preventDefault();

              const updatedMin = modal.querySelector("#min-threshold").value;
              const updatedMax = modal.querySelector("#max-threshold").value;

              fetch("../json/WebApp_config.json")
                .then((response) => response.json())
                .then((config) => {
                  const catalog_url = config.catalog_url;

                  return fetch(`${catalog_url}/set_sensor_threshold`, {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                      Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                      sensor_id: sensor.sensor_id,
                      threshold: {
                        min: updatedMin,
                        max: updatedMax,
                      },
                    }),
                  });
                })
                .then((res) => res.json())
                .then((result) => {
                  alert(result.message || "Threshold updated!");
                  modal.remove();
                })
                .catch((err) => {
                  console.error("Error updating threshold:", err);
                  alert("Failed to update threshold.");
                });
            });
        });
      });
    })
    .catch((error) => {
      console.error("Error:", error.message);
      alert("An error occurred while fetching sensor data");
    });

  // const modal = document.getElementById("thresholdModal");
  // const sensorIdInput = document.getElementById("sensor-id");
  // const minThresholdInput = document.getElementById("min-threshold");
  // const maxThresholdInput = document.getElementById("max-threshold");
  // const thresholdForm = document.getElementById("thresholdForm");

  // // Open modal and populate with sensor details
  // document.querySelectorAll(".change-values-btn").forEach(button => {
  //   button.addEventListener("click", () => {
  //     const sensorId = button.getAttribute("data-sensor-id");
  //     const thresholdMin = button.getAttribute("data-threshold-min");
  //     const thresholdMax = button.getAttribute("data-threshold-max");

  //     // Populate modal fields
  //     sensorIdInput.value = sensorId;
  //     minThresholdInput.value = thresholdMin;
  //     maxThresholdInput.value = thresholdMax;

  //     // Show modal
  //     modal.style.display = "block";
  //   });
  // });

  // // Close modal
  // window.closeModal = function () {
  //   modal.style.display = "none";
  // };

  // // Handle form submission
  // thresholdForm.addEventListener("submit", event => {
  //   event.preventDefault();

  //   const sensorId = sensorIdInput.value;
  //   const minThreshold = minThresholdInput.value;
  //   const maxThreshold = maxThresholdInput.value;

  //   // Send updated thresholds to the backend
  //   fetch("/set_sensor_threshold", {
  //     method: "POST",
  //     headers: {
  //       "Content-Type": "application/json"
  //     },
  //     body: JSON.stringify({
  //       sensor_id: sensorId,
  //       threshold: {
  //         min: minThreshold,
  //         max: maxThreshold
  //       }
  //     })
  //   })
  //     .then(response => response.json())
  //     .then(data => {
  //       alert(data.message || "Threshold updated successfully!");
  //       closeModal();
  //     })
  //     .catch(error => {
  //       console.error("Error updating thresholds:", error);
  //       alert("Failed to update thresholds.");
  //     });
  // });
});
