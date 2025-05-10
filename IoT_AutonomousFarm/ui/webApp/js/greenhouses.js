// $(".button, .close").on("click", function (e) {
//     e.preventDefault();
//     $(".detail, html, body").toggleClass("open");
//   });

document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");
  const userId = localStorage.getItem("user_id");
  const username = localStorage.getItem("username");

  if (!token || !userId || !username) {
    alert("You are not logged in. Please log in to access this page.");
    window.location.href = "loginform.html"; // redirect to login page
  }

  // document.getElementById("username-display").textContent = `Welcome, ${username}`;

  // document.getElementById("logout-button").addEventListener("click", () => {
  //   // clear the token and user information from local storage and redirect to login page
  //   localStorage.removeItem("token");
  //   localStorage.removeItem("user_id");
  //   localStorage.removeItem("username");
  //   window.location.href = "home.html";
  // });

  document.querySelector("tbody").addEventListener("click", (event) => {
    if (event.target.classList.contains("select-button")) {
      const button = event.target;

      // retrieve data attributes from the clicked button
      const selectedGreenhouseId = button.getAttribute("data-greenhouse_id");
      const selectedGreenhouseName = button.getAttribute("data-name");
      const selectedGreenhouseLocation = button.getAttribute("data-location");

      // store the selected greenhouse information in local storage
      localStorage.setItem("greenhouse_id", selectedGreenhouseId);
      localStorage.setItem("greenhouse_name", selectedGreenhouseName);
      localStorage.setItem("greenhouse_location", selectedGreenhouseLocation);
      // redirect to the greenhouse details page
      // window.location.href = "greenhouseDetails.html";
    }
  });

  const formData = {
    user_id: userId,
    username: username
  };

  // read from the config file to get the API URL
  fetch("../json/WebApp_config.json")    // this path is relative to the HTML file
  .then(response => response.json())
  .then(config => {
      const catalog_url = config.catalog_url; // read the catalog URL from the config file

      // use the catalog URL to do the HTTP request
      const queryParams = new URLSearchParams(formData).toString();
      return fetch(`${catalog_url}/get_user_greenhouses?${queryParams}`, {
          method: "GET",
          headers: {"Content-Type": "application/json", "Authorization": `Bearer ${token}`}
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
    if (data.greenhouses) {
      const tableBody = document.querySelector("tbody");
      tableBody.innerHTML = ""; // Clear existing rows

      data.greenhouses.forEach(greenhouse => {
        const row = `
          <tr>
            <td data-title='name'>${greenhouse.name}</td>
            <td data-title='user_id'>${username}</td>
            <td data-title='location'>${greenhouse.location}</td>
            <td class="select">
            <div class="dropdown">
              <button 
                 data-greenhouse_id="${greenhouse.greenhouse_id}" 
                        data-user_id="${greenhouse.user_id}"
                        data-name="${greenhouse.name}" 
                        data-location="${greenhouse.location}"
                type="button" class="btn select-button dropdown-toggle" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false" id="dropdownMenuButton-${greenhouse.greenhouse_id}">
                  Action
                </button>
                <div class="dropdown-menu" aria-labelledby="dropdownMenuButton-${greenhouse.greenhouse_id}">
                  <a class="dropdown-item" href="greenhouseDetails.html">Sensors</a>
                  <a class="dropdown-item" href="greenhouseplants.html">Plants</a>
                  <a class="dropdown-item" href="greenhousedevices.html">Devices</a>
                </div>
             </div>
            </td>
          </tr>
        `;
        tableBody.insertAdjacentHTML("beforeend", row);
      });
    } else {
      console.error("Failed to fetch greenhouses:", data.error);
      alert("An error occurred while fetching the greenhouses");
    }
  })
  .catch(error => {
      console.error("Error:", error.message);
      alert("An error occurred while fetching the greenhouses");
  });
});




$(document).ready(function () {
  $(".select-button").on("click", function () {
    // Get greenhouse details from data attributes
    let provider = $(this).data("provider");
    let email = $(this).data("email");
    let city = $(this).data("city");
    let location = $(this).data("location");
    let greenhouseid = $(this).data("greenhouse_id"); // Get greenhouse ID

    // Update details section dynamically
    $(".detail-container").html(`
      <dl>
        <input type="hidden" class="greenhouse-id" value="${greenhouseid}">
        <dt>Plants</dt>
        <a href= "/login">
        <svg width="24" height="8" viewBox="0 0 16 8" fill="none" xmlns="http://www.w3.org/2000/svg" class="arrow-icon">
        <path d="M15 4H4V1" stroke="white"/>
        <path d="M14.5 4H3.5H0" stroke="white"/>
        <path d="M15.8536 4.35355C16.0488 4.15829 16.0488 3.84171 15.8536 3.64645L12.6716 0.464466C12.4763 0.269204 12.1597 0.269204 11.9645 0.464466C11.7692 0.659728 11.7692 0.976311 11.9645 1.17157L14.7929 4L11.9645 6.82843C11.7692 7.02369 11.7692 7.34027 11.9645 7.53553C12.1597 7.7308 12.4763 7.7308 12.6716 7.53553L15.8536 4.35355ZM15 4.5L15.5 4.5L15.5 3.5L15 3.5L15 4.5Z" fill="white"/>
        </svg>
        </a>

        <dt>Devices</dt>
        <a href= "/login">
        <svg width="24" height="8" viewBox="0 0 16 8" fill="none" xmlns="http://www.w3.org/2000/svg" class="arrow-icon">
        <path d="M15 4H4V1" stroke="white"/>
        <path d="M14.5 4H3.5H0" stroke="white"/>
        <path d="M15.8536 4.35355C16.0488 4.15829 16.0488 3.84171 15.8536 3.64645L12.6716 0.464466C12.4763 0.269204 12.1597 0.269204 11.9645 0.464466C11.7692 0.659728 11.7692 0.976311 11.9645 1.17157L14.7929 4L11.9645 6.82843C11.7692 7.02369 11.7692 7.34027 11.9645 7.53553C12.1597 7.7308 12.4763 7.7308 12.6716 7.53553L15.8536 4.35355ZM15 4.5L15.5 4.5L15.5 3.5L15 3.5L15 4.5Z" fill="white"/>
        </svg>
        </a>

        <dt>Sensors</dt>
       <a href= "/get_all_sensors?greenhouse_id=${greenhouseid}">
        <svg width="24" height="8" viewBox="0 0 16 8" fill="none" xmlns="http://www.w3.org/2000/svg" class="arrow-icon">
        <path d="M15 4H4V1" stroke="white"/>
        <path d="M14.5 4H3.5H0" stroke="white"/>
        <path d="M15.8536 4.35355C16.0488 4.15829 16.0488 3.84171 15.8536 3.64645L12.6716 0.464466C12.4763 0.269204 12.1597 0.269204 11.9645 0.464466C11.7692 0.659728 11.7692 0.976311 11.9645 1.17157L14.7929 4L11.9645 6.82843C11.7692 7.02369 11.7692 7.34027 11.9645 7.53553C12.1597 7.7308 12.4763 7.7308 12.6716 7.53553L15.8536 4.35355ZM15 4.5L15.5 4.5L15.5 3.5L15 3.5L15 4.5Z" fill="white"/>
        </svg>
        </a>

        <dt>Ask For Plot</dt>
       <a href= "/login">
        <svg width="24" height="8" viewBox="0 0 16 8" fill="none" xmlns="http://www.w3.org/2000/svg" class="arrow-icon">
        <path d="M15 4H4V1" stroke="white"/>
        <path d="M14.5 4H3.5H0" stroke="white"/>
        <path d="M15.8536 4.35355C16.0488 4.15829 16.0488 3.84171 15.8536 3.64645L12.6716 0.464466C12.4763 0.269204 12.1597 0.269204 11.9645 0.464466C11.7692 0.659728 11.7692 0.976311 11.9645 1.17157L14.7929 4L11.9645 6.82843C11.7692 7.02369 11.7692 7.34027 11.9645 7.53553C12.1597 7.7308 12.4763 7.7308 12.6716 7.53553L15.8536 4.35355ZM15 4.5L15.5 4.5L15.5 3.5L15 3.5L15 4.5Z" fill="white"/>
        </svg>
        </a>

        <dt>Event Management</dt>
        <a href= "/login">
        <svg width="24" height="8" viewBox="0 0 16 8" fill="none" xmlns="http://www.w3.org/2000/svg" class="arrow-icon">
        <path d="M15 4H4V1" stroke="white"/>
        <path d="M14.5 4H3.5H0" stroke="white"/>
        <path d="M15.8536 4.35355C16.0488 4.15829 16.0488 3.84171 15.8536 3.64645L12.6716 0.464466C12.4763 0.269204 12.1597 0.269204 11.9645 0.464466C11.7692 0.659728 11.7692 0.976311 11.9645 1.17157L14.7929 4L11.9645 6.82843C11.7692 7.02369 11.7692 7.34027 11.9645 7.53553C12.1597 7.7308 12.4763 7.7308 12.6716 7.53553L15.8536 4.35355ZM15 4.5L15.5 4.5L15.5 3.5L15 3.5L15 4.5Z" fill="white"/>
        </svg>
        </a>
      </dl>
    `);

    // Open details section
    $(".detail, html, body").addClass("open");
  });

  $(".close").on("click", function () {
    // Close details section
    $(".detail, html, body").removeClass("open");
  });
});
