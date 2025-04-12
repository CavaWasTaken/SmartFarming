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

document
  .addEventListener("DOMContentLoaded", () => {
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
        const plants = data.plants;

        const dashboardCards = document.querySelector(".dashboard-cards");

        plants.forEach((plant) => {
          // create a card for each sensor
          const card = document.createElement("div");

          card.className = "card";
          card.innerHTML = `
          <button class="delete-btn" title="Delete Plant" style="position:absolute; right:10px; top:10px; background:none; border:none; font-size:20px; cursor:pointer;"><svg fill="#ed0c0c" width="20px" height="20px" viewBox="-3.5 0 19 19" xmlns="http://www.w3.org/2000/svg" class="cf-icon-svg" stroke="#ed0c0c"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M11.383 13.644A1.03 1.03 0 0 1 9.928 15.1L6 11.172 2.072 15.1a1.03 1.03 0 1 1-1.455-1.456l3.928-3.928L.617 5.79a1.03 1.03 0 1 1 1.455-1.456L6 8.261l3.928-3.928a1.03 1.03 0 0 1 1.455 1.456L7.455 9.716z"></path></g></svg></button>
                <div class="card-img">
                  <svg version="1.1" id="Uploaded to svgrepo.com" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="100px" height="100px" viewBox="0 0 32 32" xml:space="preserve" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <style type="text/css"> .avocado_een{fill:#231F20;} .avocado_negen{fill:#6F9B45;} .avocado_tien{fill:#C3CC6A;} .avocado_drie{fill:#716558;} .avocado_vier{fill:#AF9480;} .st0{fill:#EAD13F;} .st1{fill:#CC4121;} .st2{fill:#FFFAEE;} .st3{fill:#E0A838;} .st4{fill:#D1712A;} .st5{fill:#A3AEB5;} .st6{fill:#788287;} .st7{fill:#248EBC;} .st8{fill:#8D3E93;} .st9{fill:#3D3935;} .st10{fill:#D36781;} .st11{fill:#E598A3;} .st12{fill:#DBD2C1;} .st13{fill:#231F20;} </style> <g> <path class="avocado_tien" d="M26.241,9.442c-0.061-0.167-0.796-0.56-3.433-0.371l-0.712,0.052l0.195-0.687 c0.887-3.12,0.602-4.102,0.433-4.2c-0.19-0.11-1.291,0.188-3.803,2.874l-0.665,0.711l-0.19-0.954C17.263,2.852,16.311,1.5,16,1.5 s-1.263,1.352-2.066,5.368l-0.19,0.954l-0.665-0.711c-2.517-2.691-3.617-2.982-3.803-2.874c-0.169,0.098-0.454,1.08,0.433,4.2 l0.195,0.687L9.191,9.072C6.557,8.883,5.82,9.275,5.759,9.442c-0.285,0.784,3.815,3.739,6.668,5.058h7.146 C22.426,13.182,26.526,10.226,26.241,9.442z"></path> <path class="avocado_negen" d="M26.241,9.442c-0.016-0.043-0.078-0.1-0.202-0.159C23.495,11.257,19.95,12.5,16,12.5 c-3.95,0-7.495-1.243-10.039-3.217C5.837,9.342,5.775,9.4,5.759,9.442c-0.285,0.784,3.815,3.739,6.668,5.058h7.146 C22.426,13.182,26.526,10.226,26.241,9.442z"></path> <polygon class="avocado_vier" points="23.5,27.5 22.434,27.5 23.559,18.5 24.5,18.5 24.5,14.5 7.5,14.5 7.5,18.5 8.441,18.5 9.566,27.5 8.5,27.5 8.5,30.5 23.5,30.5 "></polygon> <polygon class="avocado_drie" points="23.253,21 8.762,21 8.441,18.5 23.559,18.5 "></polygon> <path class="avocado_een" d="M26.711,9.272c-0.201-0.553-1.263-0.75-2.616-0.75c-0.419,0-0.865,0.019-1.323,0.052 c0.615-2.161,0.96-4.331,0.202-4.769c-0.097-0.056-0.209-0.082-0.334-0.082c-0.939,0-2.619,1.479-4.084,3.048 C18.029,4.134,17.083,1,16,1s-2.029,3.134-2.557,5.77c-1.466-1.568-3.145-3.048-4.084-3.048c-0.125,0-0.237,0.026-0.334,0.082 C8.267,4.242,8.613,6.412,9.228,8.573C8.77,8.54,8.323,8.521,7.905,8.521c-1.353,0-2.415,0.197-2.616,0.75 c-0.403,1.107,2.732,3.33,5.139,4.728H7v5h1l1,8H8v4h16v-4h-1l1-8h1v-5h-3.428C23.979,12.602,27.114,10.379,26.711,9.272z M23,30H9 v-2h14V30z M21.992,27H10.008l-1-8h13.984L21.992,27z M24,18H8v-3h16V18z M19.498,14h-6.995c-2.312-1.025-5.465-3.389-6.132-4.33 c0.243-0.068,0.706-0.148,1.534-0.148c0.377,0,0.798,0.017,1.251,0.049l1.424,0.103L10.189,8.3c-0.597-2.1-0.625-3.086-0.585-3.497 c0.462,0.213,1.471,0.898,3.108,2.65l1.329,1.422l0.382-1.909C14.976,4.205,15.617,2.67,16,2.143 c0.383,0.527,1.024,2.062,1.576,4.822l0.382,1.909l1.329-1.422c1.639-1.754,2.648-2.438,3.108-2.651 c0.041,0.41,0.013,1.396-0.585,3.498L21.42,9.673l1.424-0.103c0.454-0.033,0.875-0.049,1.251-0.049c0.828,0,1.29,0.08,1.534,0.148 C24.963,10.611,21.81,12.975,19.498,14z"></path> </g> </g></svg>
                </div>
                <div class="desc mt-3">
                    <h1 class="primary-text">
                        ${plant.name}
                    </h1>
                     <h5 class="text-white">
                         ${plant.species}
                     </h5>
                </div>
               
                <div class="details">
                    <div class="rating">
                        <h6 class="primary-text">
                        ${plant.desired_thresholds.pH.min || 0} - ${
            plant.desired_thresholds.pH.max || 0
          }
                        </h6>
                        <h6 class="secondary-text">PH</h6>  
                    </div>
                     <div class="rating">
                        <h6 class="primary-text">
                        ${plant.desired_thresholds.Humidity.min || 0} - ${
            plant.desired_thresholds.Humidity.max || 0
          }
                        </h6>
                        <h6 class="secondary-text">Humidity</h6>  
                    </div>
                     <div class="rating">
                        <h6 class="primary-text">
                        ${plant.desired_thresholds.LightIntensity.min || 0} - ${
            plant.desired_thresholds.LightIntensity.max || 0
          }
                        </h6>
                        <h6 class="secondary-text">LightIntensity</h6>  
                    </div>
                     <div class="rating">
                        <h6 class="primary-text">
                        ${plant.desired_thresholds.SoilMoisture.min || 0} - ${
            plant.desired_thresholds.SoilMoisture.max || 0
          }
                        </h6>
                        <h6 class="secondary-text">SoilMoisture</h6>  
                    </div>
                      <div class="rating">
                        <h6 class="primary-text">
                        ${plant.desired_thresholds.Temperature.min || 0} - ${
            plant.desired_thresholds.Temperature.max || 0
          }
                        </h6>
                        <h6 class="secondary-text">Temperature</h6>  
                    </div>
                </div>`;

          dashboardCards.appendChild(card);

          const deleteBtn = card.querySelector(".delete-btn");


// <!-- Add event listener to the delete button -->

deleteBtn.addEventListener("click", () => {
  if (confirm(`Are you sure you want to delete ${plant.name}?`)) {
    fetch("../json/WebApp_config.json")
      .then((response) => response.json())
      .then((config) => {
        const catalog_url = config.catalog_url;
        return fetch(`${catalog_url}/remove_plant_from_greenhouse`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            greenhouse_id: greenhouseId,
            plant_id: plant.plant_id,
          }),
        });
      })
      .then((res) => res.json())
      .then((result) => {
        alert(result.message || "Plant deleted successfully.");
        card.remove(); // Remove the card from UI
      })
      .catch((err) => {
        console.error("Error deleting plant:", err);
        alert("Failed to delete plant.");
      });
  }
});

// Add plants functionality
document.getElementById("add-plant-btn").addEventListener("click", () => {
  fetch("../json/WebApp_config.json")
    .then((res) => res.json())
    .then((config) => {
      const catalog_url = config.catalog_url;
      return fetch(`${catalog_url}/get_all_plants`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    })
    .then((res) => res.json())
    .then((availablePlants) => {
      const select = document.getElementById("plant-select");
      select.innerHTML = ""; // Clear old options

      console.log(availablePlants);
      availablePlants.plants.forEach((avplant) => 
      {
        const option = document.createElement("option");
        option.value = avplant.plant_id;
        option.textContent = `${avplant.name} (${avplant.species})`;
        select.appendChild(option);
      });

      document.getElementById("plant-modal").classList.remove("d-none");
    })
    .catch((err) => {
      console.error("Failed to load available plants", err);
      alert("Failed to load available plants.");
    });
});

document.getElementById("cancel-modal").addEventListener("click", () => {
  document.getElementById("plant-modal").classList.add("d-none");
});

document.getElementById("confirm-add-plant").addEventListener("click", () => {
  const plantId = document.getElementById("plant-select").value;

  fetch("../json/WebApp_config.json")
    .then((res) => res.json())
    .then((config) => {
      const catalog_url = config.catalog_url;
      return fetch(`${catalog_url}/add_plant_to_greenhouse`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          greenhouse_id: greenhouseId,
          plant_id: plantId,
        }),
      });
    })
    .then((res) => res.json())
    .then((result) => {
      alert(result.message || "Plant added successfully.");
      location.reload(); // Refresh to show the new plant
    })
    .catch((err) => {
      console.error("Failed to add plant", err);
      alert("Failed to add plant.");
    });
});



          // const setThresholdBtn = card.querySelector(
          //   `#set-threshold-button-${plant.plant_id}`
          // );

          //     setThresholdBtn.addEventListener("click", () => {
          //       const modal = document.createElement("div");
          //       modal.className = "modal d-flex";

          //       modal.innerHTML = `
          //     <div class="modal-content">
          //         <span class="close" style="float: right; font-size: 24px; cursor: pointer;">&times;</span>
          //         <h1>Set Threshold for ${plant.name}</h1>
          //         <form id="thresholdForm-${plant.plant_id}">
          //             <div class="form-group">
          //             <label for="min-threshold">Min Threshold:</label>
          //             <input class="form-control fs-4" type="number" id="min-threshold" value="${
          //               plant.desired_thresholds.pH.min - plant.desired_thresholds.pH.max|| 0
          //             }" required />
          //             </div>

          //             <div class="form-group">
          //             <label for="max-threshold">Max Threshold:</label>
          //             <input class="form-control fs-4" type="number" id="max-threshold" value="${
          //               plant.desired_thresholds.Humidity.min - plant.desired_thresholds.Humidity.max || 0
          //             }" required />
          //             </div>

          //             <button class="btn btn-primary btn-lg btnmodal fs-4" type="submit">Save</button>
          //         </form>
          //     </div>
          // `;

          //       document.body.appendChild(modal);

          //       modal.querySelector(".close").addEventListener("click", () => {
          //         modal.remove();
          //       });

          // modal
          //   .querySelector(`#thresholdForm-${sensor.sensor_id}`)
          //   .addEventListener("submit", (e) => {
          //     e.preventDefault();

          //     const updatedMin = modal.querySelector("#min-threshold").value;
          //     const updatedMax = modal.querySelector("#max-threshold").value;

          //     fetch("../json/WebApp_config.json")
          //       .then((response) => response.json())
          //       .then((config) => {
          //         const catalog_url = config.catalog_url;

          //         return fetch(`${catalog_url}/set_sensor_threshold`, {
          //           method: "POST",
          //           headers: {
          //             "Content-Type": "application/json",
          //             Authorization: `Bearer ${token}`,
          //           },
          //           body: JSON.stringify({
          //             sensor_id: sensor.sensor_id,
          //             threshold: {
          //               min: updatedMin,
          //               max: updatedMax,
          //             },
          //           }),
          //         });
          //       })
          //       .then((res) => res.json())
          //       .then((result) => {
          //         alert(result.message || "Threshold updated!");
          //         modal.remove();
          //         location.reload(); // reload the page to reflect the changes
          //       })
          //       .catch((err) => {
          //         console.error("Error updating threshold:", err);
          //         alert("Failed to update threshold.");
          //       });
          //   });
        });
      });
  })
  .catch((error) => {
    console.error("Error:", error.message);
    alert("An error occurred while fetching data");
  });
