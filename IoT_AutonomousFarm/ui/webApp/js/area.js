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
      window.location.href = "loginform.html";
      return;
    }
  
    if (!greenhouseId || !greenhouseName || !greenhouseLocation) {
      alert("No greenhouse selected. Please select a greenhouse.");
      window.location.href = "greenhouses.html";
      return;
    }
  
    // document.getElementById("username-display").textContent = `Greenhouse owner: ${username}`;
    // document.getElementById("title").textContent = `${greenhouseName} - ${greenhouseLocation}`;
  
    // document.getElementById("logout-button").addEventListener("click", () => {
    //   localStorage.clear();
    //   window.location.href = "loginform.html";
    // });
  
    fetch("../json/WebApp_config.json")
      .then((response) => response.json())
      .then((config) => {
        const catalog_url = config.catalog_url;
  
        return fetch(`${catalog_url}/get_areas_by_greenhouse?greenhouse_id=${greenhouseId}`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });
      })
      .then(async (response) => {
        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.message);
        }
        return response.json();
      })
      .then((data) => {
        const areas = data.areas;
        const dashboardCards = document.querySelector(".dashboard-cards");
  
        areas.forEach((are) => {
          
          const card = document.createElement("div");
          card.className = "card";
          card.innerHTML = `
            <!-- Same card content here -->
            <button class="delete-btn" title="Delete Plant" style="position:absolute; right:10px; top:10px; background:none; border:none; font-size:20px; cursor:pointer;">
              <!-- svg content -->
              <svg fill="#ed0c0c" width="20px" height="20px" viewBox="-3.5 0 19 19" xmlns="http://www.w3.org/2000/svg" class="cf-icon-svg" stroke="#ed0c0c"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M11.383 13.644A1.03 1.03 0 0 1 9.928 15.1L6 11.172 2.072 15.1a1.03 1.03 0 1 1-1.455-1.456l3.928-3.928L.617 5.79a1.03 1.03 0 1 1 1.455-1.456L6 8.261l3.928-3.928a1.03 1.03 0 0 1 1.455 1.456L7.455 9.716z"></path></g></svg>
            </button>
            <div class="card-img"> 
            <!-- svg icon --> 
            <svg height="90px" width="90px" version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 503 503" xml:space="preserve" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <g> <polygon style="fill:#D7E6D8;" points="430.58,461.241 72.42,461.241 72.42,141.527 251.5,10 430.58,141.527 "></polygon> <path style="fill:#4FC497;" d="M349.735,292.209c0,54.254-43.981,98.235-98.235,98.235s-98.235-43.981-98.235-98.235 S251.5,125,251.5,125S349.735,237.955,349.735,292.209z"></path> <g> <path style="fill:#333333;" d="M259.045,118.437c-1.899-2.184-4.651-3.438-7.545-3.438s-5.646,1.254-7.545,3.438 c-1.017,1.169-25.184,29.036-49.76,64.08c-33.795,48.191-50.93,85.097-50.93,109.691c0,56.309,43.225,102.705,98.235,107.769V431 c0,5.523,4.477,10,10,10c5.523,0,10-4.477,10-10v-31.022c55.01-5.064,98.235-51.459,98.235-107.769 c0-24.595-17.135-61.5-50.93-109.691C284.229,147.473,260.062,119.607,259.045,118.437z M261.5,379.874V320 c0-5.523-4.477-10-10-10c-5.523,0-10,4.477-10,10v59.874c-43.962-4.982-78.235-42.393-78.235-87.665 c0-37.932,58.015-115.457,88.236-151.763c30.221,36.296,88.234,113.805,88.234,151.763 C339.735,337.48,305.462,374.891,261.5,379.874z"></path> <path style="fill:#333333;" d="M241.5,277.578V290c0,5.523,4.477,10,10,10s10-4.477,10-10v-12.422c0-5.523-4.477-10-10-10 C245.977,267.578,241.5,272.055,241.5,277.578z"></path> <path style="fill:#333333;" d="M251.5,479c-5.523,0-10,4.477-10,10v4c0,5.523,4.477,10,10,10s10-4.477,10-10v-4 C261.5,483.477,257.023,479,251.5,479z"></path> <path style="fill:#333333;" d="M257.419,1.94c-3.522-2.587-8.316-2.587-11.839,0L30.165,159.71 c-4.486,3.221-5.512,9.469-2.291,13.955c1.953,2.721,5.02,4.169,8.131,4.169c2.02,0,4.058-0.61,5.824-1.878l20.591-14.783v300.068 c0,5.523,4.477,10,10,10h358.16c5.523,0,10-4.477,10-10V161.173l20.591,14.783c1.766,1.268,3.804,1.878,5.824,1.878 c3.111,0,6.178-1.449,8.131-4.169c3.221-4.486,2.195-10.734-2.291-13.955L257.419,1.94z M82.42,451.241V146.664 c0.101-0.098,0.206-0.194,0.302-0.295L251.5,22.407l168.778,123.962c0.096,0.102,0.201,0.197,0.302,0.295v304.577H82.42z"></path> </g> </g> </g></svg>            </div>
            <div class="desc mt-3">
              <h1 class="primary-text">${are.name}</h1>
            </div>
            <div class = "row d-flex">
               <button class="primary-text sensorbtn">
                     Sensors
                </button>
                </div>
               <div class="row d-flex">
                  <button class="primary-text plantsbtn">
                     Plants
                </button>
                </div>
          `;
          card.querySelector(".sensorbtn").addEventListener("click", () => {
            localStorage.setItem("area_id", are.area_id);
            window.location.href = "greenhouseDetails.html";
          });
          
          card.querySelector(".plantsbtn").addEventListener("click", () => {
            localStorage.setItem("area_id", are.area_id);
            window.location.href = "Greenhouseplants.html";
          });
          
          dashboardCards.appendChild(card);
  
        //   card.querySelector(".delete-btn").addEventListener("click", () => {
        //     if (confirm(`Are you sure you want to delete ${plant.name}?`)) {
        //       fetch("../json/WebApp_config.json")
        //         .then((res) => res.json())
        //         .then((config) => {
        //           const catalog_url = config.catalog_url;
        //           return fetch(`${catalog_url}/remove_plant_from_greenhouse`, {
        //             method: "POST",
        //             headers: {
        //               "Content-Type": "application/json",
        //               Authorization: `Bearer ${token}`,
        //             },
        //             body: JSON.stringify({
        //               greenhouse_id: greenhouseId,
        //               plant_id: plant.plant_id,
        //             }),
        //           });
        //         })
        //         .then((res) => res.json())
        //         .then((result) => {
        //           alert(result.message || "Plant deleted successfully.");
        //           card.remove();
        //         })
        //         .catch((err) => {
        //           console.error("Error deleting plant:", err);
        //           alert("Failed to delete plant.");
        //         });
        //     }
        //   });
        });
  
        // Add Area Button
        const token = localStorage.getItem("token");
        const greenhouseId = localStorage.getItem("greenhouse_id");

        // Open the area modal
        document.getElementById("add-area-btn").addEventListener("click", () => {
        document.getElementById("area-modal").classList.remove("d-none");
        });

        // Cancel and close modal
        document.getElementById("cancel-modal").addEventListener("click", () => {
        document.getElementById("area-modal").classList.add("d-none");
        });

        // Confirm and send area to API
        document.getElementById("confirm-add-area").addEventListener("click", () => {
        const areaName = document.getElementById("area-name").value;

        if (!areaName || !greenhouseId) {
            alert("Please enter an area name and ensure a greenhouse is selected.");
            return;
        }

        fetch("../json/WebApp_config.json")
            .then((res) => res.json())
            .then((config) => {
            const catalog_url = config.catalog_url;
            return fetch(`${catalog_url}/add_area`, {
                method: "POST",
                headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                greenhouse_id: parseInt(greenhouseId),
                name: areaName
                })
            });
            })
            .then((res) => res.json())
            .then((result) => {
            alert(result.message || "Area added successfully.");
            location.reload();
            })
    .catch((err) => {
      console.error("Failed to add area:", err);
      alert("Failed to add area.");
      document.getElementById("area-modal").classList.add("d-none");
    });
});
})
      .catch((err) => {
        console.error("Error during initial fetch:", err);
        alert("Failed to load greenhouse data.");
      });
  });
  
  
  