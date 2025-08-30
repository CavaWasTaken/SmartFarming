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
});
  
// ***********************************************//

document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");
  const userId = localStorage.getItem("user_id");
  const username = localStorage.getItem("username");

  const greenhouseId = localStorage.getItem("greenhouse_id");
  const greenhouseName = localStorage.getItem("greenhouse_name");
  const greenhouseLocation = localStorage.getItem("greenhouse_location");

  const deviceIcons = {
    Microservices: `<svg width="100px" height="100px" viewBox="0 0 48 48" version="1" xmlns="http://www.w3.org/2000/svg" enable-background="new 0 0 48 48" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill="#E65100" d="M25.6,34.4c0.1-0.4,0.1-0.9,0.1-1.4s0-0.9-0.1-1.4l2.8-2c0.3-0.2,0.4-0.6,0.2-0.9l-2.7-4.6 c-0.2-0.3-0.5-0.4-0.8-0.3L22,25.3c-0.7-0.6-1.5-1-2.4-1.4l-0.3-3.4c0-0.3-0.3-0.6-0.6-0.6h-5.3c-0.3,0-0.6,0.3-0.6,0.6L12.4,24 c-0.9,0.3-1.6,0.8-2.4,1.4l-3.1-1.4c-0.3-0.1-0.7,0-0.8,0.3l-2.7,4.6c-0.2,0.3-0.1,0.7,0.2,0.9l2.8,2c-0.1,0.4-0.1,0.9-0.1,1.4 s0,0.9,0.1,1.4l-2.8,2c-0.3,0.2-0.4,0.6-0.2,0.9l2.7,4.6c0.2,0.3,0.5,0.4,0.8,0.3l3.1-1.4c0.7,0.6,1.5,1,2.4,1.4l0.3,3.4 c0,0.3,0.3,0.6,0.6,0.6h5.3c0.3,0,0.6-0.3,0.6-0.6l0.3-3.4c0.9-0.3,1.6-0.8,2.4-1.4l3.1,1.4c0.3,0.1,0.7,0,0.8-0.3l2.7-4.6 c0.2-0.3,0.1-0.7-0.2-0.9L25.6,34.4z M16,38c-2.8,0-5-2.2-5-5c0-2.8,2.2-5,5-5c2.8,0,5,2.2,5,5C21,35.8,18.8,38,16,38z"></path> <path fill="#FFA000" d="M41.9,15.3C42,14.8,42,14.4,42,14s0-0.8-0.1-1.3l2.5-1.8c0.3-0.2,0.3-0.5,0.2-0.8l-2.5-4.3 c-0.2-0.3-0.5-0.4-0.8-0.2l-2.9,1.3c-0.7-0.5-1.4-0.9-2.2-1.3l-0.3-3.1C36,2.2,35.8,2,35.5,2h-4.9c-0.3,0-0.6,0.2-0.6,0.5l-0.3,3.1 c-0.8,0.3-1.5,0.7-2.2,1.3l-2.9-1.3c-0.3-0.1-0.6,0-0.8,0.2l-2.5,4.3c-0.2,0.3-0.1,0.6,0.2,0.8l2.5,1.8C24,13.2,24,13.6,24,14 s0,0.8,0.1,1.3l-2.5,1.8c-0.3,0.2-0.3,0.5-0.2,0.8l2.5,4.3c0.2,0.3,0.5,0.4,0.8,0.2l2.9-1.3c0.7,0.5,1.4,0.9,2.2,1.3l0.3,3.1 c0,0.3,0.3,0.5,0.6,0.5h4.9c0.3,0,0.6-0.2,0.6-0.5l0.3-3.1c0.8-0.3,1.5-0.7,2.2-1.3l2.9,1.3c0.3,0.1,0.6,0,0.8-0.2l2.5-4.3 c0.2-0.3,0.1-0.6-0.2-0.8L41.9,15.3z M33,19c-2.8,0-5-2.2-5-5c0-2.8,2.2-5,5-5c2.8,0,5,2.2,5,5C38,16.8,35.8,19,33,19z"></path> </g></svg>`,
    DeviceConnector: `<svg width="100px" height="100px" viewBox="0 0 32 32" enable-background="new 0 0 32 32" version="1.1" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <g id="Layer_2"></g> <g id="Layer_3"></g> <g id="Layer_4"></g> <g id="Layer_5"></g> <g id="Layer_6"></g> <g id="Layer_7"></g> <g id="Layer_8"></g> <g id="Layer_9"></g> <g id="Layer_10"></g> <g id="Layer_11"></g> <g id="Layer_12"></g> <g id="Layer_13"></g> <g id="Layer_14"></g> <g id="Layer_15"></g> <g id="Layer_16"></g> <g id="Layer_17"></g> <g id="Layer_18"></g> <g id="Layer_19"></g> <g id="Layer_20"></g> <g id="Layer_21"></g> <g id="Layer_22"></g> <g id="Layer_23"></g> <g id="Layer_24"></g> <g id="Layer_25"></g> <g id="Layer_26"></g> <g id="Layer_27"> <g> <path d="M26,31c-0.5527,0-1-0.4478-1-1V10c0-1.6543-1.3457-3-3-3s-3,1.3457-3,3v16c0,2.7568-2.2432,5-5,5h-1 c-2.7568,0-5-2.2432-5-5v-6c0-0.5522,0.4473-1,1-1s1,0.4478,1,1v6c0,1.6543,1.3457,3,3,3h1c1.6543,0,3-1.3457,3-3V10 c0-2.7568,2.2432-5,5-5s5,2.2432,5,5v20C27,30.5522,26.5527,31,26,31z" fill="#4391B2"></path> </g> <g> <path d="M9,7C8.4473,7,8,6.5522,8,6V2c0-0.5522,0.4473-1,1-1s1,0.4478,1,1v4C10,6.5522,9.5527,7,9,7z" fill="#4391B2"></path> </g> <g> <path d="M13,6v11c0,2.21-1.79,4-4,4s-4-1.79-4-4V6c0-0.55,0.45-1,1-1h6C12.55,5,13,5.45,13,6z" fill="#48B1DD"></path> </g> <g> <path d="M9,10c0,0.55-0.45,1-1,1H5V9h3C8.55,9,9,9.45,9,10z" fill="#96CEE5"></path> </g> <g> <path d="M13,13v2h-3c-0.55,0-1-0.45-1-1s0.45-1,1-1H13z" fill="#96CEE5"></path> </g> </g> <g id="Layer_28"></g> <g id="Layer_29"></g> <g id="Layer_30"></g> <g id="Layer_31"></g> </g></svg>`,
    ThingSpeakAdaptor: `<svg fill="#000000" width="100px" height="100px" viewBox="0 0 24 24" id="adapter-4" data-name="Flat Line" xmlns="http://www.w3.org/2000/svg" class="icon flat-line"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path id="secondary" d="M11,3h6a1,1,0,0,1,1,1V14a1,1,0,0,1-1,1H10a1,1,0,0,1-1-1V5a2,2,0,0,1,2-2Z" transform="translate(27 18) rotate(-180)" style="fill: #2ca9bc; stroke-width: 2;"></path><path id="primary" d="M6,5H9M6,9H9m6,12V15M9,4V14a1,1,0,0,0,1,1h6a2,2,0,0,0,2-2V4a1,1,0,0,0-1-1H10A1,1,0,0,0,9,4Z" style="fill: none; stroke: #000000; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2;"></path></g></svg>`,
    UI: `<svg width="100px" height="100px" viewBox="0 0 1024 1024" class="icon" version="1.1" xmlns="http://www.w3.org/2000/svg" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M889.202585 296.368893v432.636883l-374.709001 216.334426-374.677031-216.334426V296.368893l374.677031-216.334426z" fill="#5FCEFF"></path><path d="M514.493584 967.718523a22.378321 22.378321 0 0 1-11.18916-2.998695l-374.677032-216.334426a22.381518 22.381518 0 0 1-11.18916-19.382823V296.368893a22.375124 22.375124 0 0 1 11.18916-19.379626l374.677032-216.334426a22.36873 22.36873 0 0 1 22.378321 0l374.709 216.334426a22.375124 22.375124 0 0 1 11.189161 19.379626v432.636883a22.381518 22.381518 0 0 1-11.189161 19.382823l-374.709 216.334426a22.407093 22.407093 0 0 1-11.189161 2.995498z m-352.29871-251.631432l352.29871 203.412544 352.33068-203.412544V309.287578l-352.33068-203.412544-352.29871 203.412544v406.799513z" fill="#4F46A3"></path><path d="M407.780962 735.943055c-48.343567 0-93.79074-18.826562-127.972027-53.007848-34.200468-34.197271-53.036621-79.657232-53.036621-128.0008v-221.289625a22.378321 22.378321 0 1 1 44.756642 0v221.289625c0 36.390347 14.181462 70.6068 39.929319 96.354657 25.725478 25.731872 59.935537 39.897349 96.322687 39.897349 75.127221 0 136.252006-61.121588 136.252006-136.252006v-221.289625a22.378321 22.378321 0 1 1 44.756642 0v221.289625c0 99.807312-81.201336 181.008648-181.008648 181.008648zM706.307764 735.943055a22.378321 22.378321 0 0 1-22.378321-22.378321v-379.919952a22.378321 22.378321 0 1 1 44.756642 0v379.919952a22.378321 22.378321 0 0 1-22.378321 22.378321z" fill="#4F46A3"></path><path d="M407.780962 657.203334c-30.818145 0-59.762905-11.99478-81.501845-33.772083-21.751728-21.710168-33.746508-50.667716-33.746508-81.505042v-206.267378a22.378321 22.378321 0 1 1 44.756642 0v206.267378c0 18.868122 7.327302 36.57257 20.636009 49.858899 13.311904 13.337479 31.006762 20.664781 49.855702 20.664781 38.871144 0 70.491711-31.636552 70.491711-70.52368v-206.267378a22.378321 22.378321 0 1 1 44.756642 0v206.267378c0 63.564022-51.700315 115.277125-115.248353 115.277125zM776.63963 735.943055a22.378321 22.378321 0 0 1-22.378321-22.378321v-379.919952a22.378321 22.378321 0 1 1 44.756642 0v379.919952a22.378321 22.378321 0 0 1-22.378321 22.378321z" fill="#4F46A3"></path></g></svg>`,
    Default: `<svg fill="#000000" width="100px" height="100px" viewBox="0 0 24 24" id="device-projector" data-name="Flat Line" xmlns="http://www.w3.org/2000/svg" class="icon flat-line"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path id="secondary" d="M4,8H7.18a3,3,0,1,0,5.64,0H20a1,1,0,0,1,1,1v6a1,1,0,0,1-1,1H4a1,1,0,0,1-1-1V9A1,1,0,0,1,4,8Z" style="fill: #2ca9bc; stroke-width: 2;"></path><path id="primary" d="M13,8h7a1,1,0,0,1,1,1v6a1,1,0,0,1-1,1H4a1,1,0,0,1-1-1V9A1,1,0,0,1,4,8H7" style="fill: none; stroke: #000000; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2;"></path><path id="primary-2" data-name="primary" d="M19,16H17v2h2ZM5,18H7V16H5ZM10,6A3,3,0,1,1,7,9,3,3,0,0,1,10,6Z" style="fill: none; stroke: #000000; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2;"></path></g></svg>`,
  };

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

  // read from the config file to get the API URL
  fetch("./json/WebApp_config.json") // this path is relative to the HTML file
    .then((response) => response.json())
    .then((config) => {
      const catalog_url = config.catalog_url; // read the catalog URL from the config file

      // use the catalog URL to do the HTTP request
      const formData = {
        greenhouse_id: greenhouseId,
      };
      const queryParams = new URLSearchParams(formData).toString();
      return fetch(
        `${catalog_url}/get_devices?${queryParams}`,
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
      const devices = data.devices;

      const dashboardCards = document.querySelector(".dashboard-cards");

      devices.forEach((device) => {
        const card = document.createElement("div");
        card.className = "card";
        const deviceIcon = deviceIcons[device.type] || deviceIcons.Default;

        let extraContent = "";
        if (device.name === "TelegramBot") {
          extraContent = `
            <div class="telegram-bot-section">
              <input type="text" placeholder="OTP" id="otp" required class="telegram-input"/>
              <button type="submit" class="telegram-send-btn">Save</button>
            </div>
          `;
        }
        if(device.name === "ThingSpeakAdaptor") {
          extraContent = `
            <div class="thingspeak-adaptor-section">
              <input type="text" class="thingspeak-channelID" placeholder="Channel ID" />
              <input type="text" class="thingspeak-write-key" placeholder="WRITE API Key..." />
              <input type="text" class="thingspeak-read-key" placeholder="READ API Key..." />
              <button type="submit" class="thingspeak-send-btn">Save</button>
            </div>
          `;
        }
        if(device.name === "TimeShift") {
          extraContent = `
            <div class="time-shift-section">
              <button id="manageSchedulingBtn" class="manage-scheduling-btn">Manage Scheduling</button>
            </div>
          `;
        }

        card.innerHTML = `
          <div class="card-img">
            ${deviceIcon}
          </div>
          <div class="desc">
            <h6 class="primary-text">
              ${device.name}
            </h6>
          </div>
          ${extraContent}
          <div class="details">
            <div class="rating">
              <h6 class="primary-text">${device.type}</h6>
              <h6 class="secondary-text">Type</h6>  
            </div>
          </div>
        `;

        dashboardCards.appendChild(card);
      });

      // Add event listener for scheduling button
      document.getElementById('manageSchedulingBtn').addEventListener('click', () => {
        window.location.href = `scheduling.html?greenhouse_id=${encodeURIComponent(greenhouseId)}`;
      });

      fetch("./json/WebApp_config.json")
        .then(res => res.json())
        .then(config => {
          const catalog_url = config.catalog_url;
          return fetch(
            `${catalog_url}/get_greenhouse_info?greenhouse_id=${encodeURIComponent(greenhouseId)}`,
            {
              method: "GET",
              headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
              },
            }
          );
        })
        .then(async response => {
          if (!response.ok) {
            const err = await response.json();
            throw new Error(err.message);
          }
          return response.json();
        })
        .then(data => {
          if (data && data.thingSpeak_config) {
            console.log("ThingSpeak Config:", data.thingSpeak_config);
            const { channel_id, write_key, read_key} = data.thingSpeak_config;
            document.querySelectorAll('.thingspeak-adaptor-section').forEach(section => {
              const channelID = section.querySelector('.thingspeak-channelID');
              const writeKey = section.querySelector('.thingspeak-write-key');
              const readKey = section.querySelector('.thingspeak-read-key');
              if (channelID && channel_id) channelID.value = channel_id;
              if (writeKey && write_key) writeKey.value = write_key;
              if (readKey && read_key) readKey.value = read_key;
              if (channelID && writeKey && readKey) {
                const sendBtn = section.querySelector('.thingspeak-send-btn');
                sendBtn.textContent = "Configured";
              }
            });
          }
        })
        .catch(err => {
          console.error("Error fetching ThingSpeak config:", err);
        });

      document.querySelectorAll('.telegram-bot-section .telegram-send-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
          const otpInput = this.closest('.telegram-bot-section').querySelector('.telegram-input');
          const otp = otpInput.value.trim();
          if (!otp) {
            alert('Please enter the OTP.');
            return;
          }
          fetch('./json/WebApp_config.json')
            .then(res => res.json())
            .then(config => {
              const catalog_url = config.catalog_url;
              return fetch(`${catalog_url}/verify_telegram_otp`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                  user_id: userId,
                  otp: otp,
                }),
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
              if (data) {
                alert("OTP verified successfully!");
                document.getElementById("otp").value = ""; // clear the OTP input
              } else {
                alert("Failed to verify OTP.");
              }
            })
            .catch(err => {
              console.error("Error verifying OTP:", err);
              alert(err.message || "Failed to verify OTP.");
              document.getElementById("otp").value = ""; // clear the OTP input
            });
        });
      });

      document.querySelectorAll('.thingspeak-adaptor-section .thingspeak-send-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
          const thingspeakSection = this.closest('.thingspeak-adaptor-section');
          const channelID = thingspeakSection.querySelector('.thingspeak-channelID');
          const writeKey = thingspeakSection.querySelector('.thingspeak-write-key');
          const readKey = thingspeakSection.querySelector('.thingspeak-read-key');
          
          const channelId = channelID.value.trim();
          const write_key = writeKey.value.trim();
          const read_key = readKey.value.trim();
          
          if (!channelId || !write_key || !read_key) {
            alert('Please enter all required fields: Channel ID, WRITE API Key, and READ API Key.');
            window.location.reload(); // reload the page to reset the form
            return;
          }
          
          fetch('./json/WebApp_config.json')
            .then(res => res.json())
            .then(config => {
              const catalog_url = config.catalog_url;
              return fetch(`${catalog_url}/update_thingspeak_config`, {
                method: 'PUT',
                headers: {
                  'Content-Type': 'application/json',
                  Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                  greenhouse_id: greenhouseId,
                  channel_id: channelId,
                  writeKey: write_key,
                  readKey: read_key,
                }),
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
              if (data) {
                alert("ThingSpeak configuration saved successfully!");
                this.textContent = "Configured";
              } else {
                alert("Failed to save ThingSpeak configuration.");
              }
            })
            .catch(err => {
              console.error("Error saving ThingSpeak config:", err);
              alert(err.message || "Failed to save ThingSpeak configuration.");
              window.location.reload();
            });
        });
      });
  })
  .catch((error) => {
      console.error("Error:", error.message);
      alert("An error occurred while fetching sensor data");
      window.location.reload(); // reload the page to reset the form
    });
})