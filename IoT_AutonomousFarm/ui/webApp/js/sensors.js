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

  const sensorIcons = {
    Temperature: `<svg width="90px" height="90px" viewBox="0 0 1024 1024" class="icon" version="1.1" xmlns="http://www.w3.org/2000/svg" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M440.277481 390.185208V626.592988l-83.151447 60.801898L323.222878 776.847429l41.997715 137.757747 84.311922 59.814055 101.041317 10.869471 94.270275-53.394674s50.168999-82.211558 51.633181-88.224932c1.464182-6.013375-3.500609-108.544448-5.700078-114.164603s-25.11487-62.950217-25.11487-62.950217l-72.809466-51.150448 0.127876-218.987856" fill="#5FCEFF"></path><path d="M432.876651 310.262633h160.100902V377.234554h-160.100902z" fill="#FFB578"></path><path d="M440.277481 233.536961h143.860635V300.508882h-143.860635z" fill="#FF4893"></path><path d="M512.911117 1007.651038c-116.942712 0-212.082545-95.139833-212.082545-212.082545 0-77.224389 42.592339-148.588855 109.653773-185.669732V117.793088c0-56.49567 45.949087-102.460741 102.428772-102.460741s102.428772 45.961874 102.428772 102.460741v492.102476c67.058237 37.071287 109.653773 108.43895 109.653773 185.672929 0 116.942712-95.139833 212.082545-212.082545 212.082545z m0-947.562049c-31.799594 0-57.67213 25.885324-57.67213 57.704099v505.813993a22.384715 22.384715 0 0 1-12.921882 20.284349c-58.762274 27.391065-96.731891 86.926989-96.731891 151.677063 0 92.262621 75.063282 167.325903 167.325903 167.325903s167.325903-75.060086 167.325903-167.325903c0-64.762861-37.96642-124.301982-96.725497-151.677063a22.36873 22.36873 0 0 1-12.928276-20.284349V117.793088c0-31.818776-25.872536-57.704099-57.67213-57.704099z" fill="#4F46A3"></path><path d="M512.911117 933.77061c-74.193725 0-134.557647-60.37671-134.557647-134.589617 0-52.055172 30.517636-99.935188 77.748681-121.97144a22.378321 22.378321 0 1 1 18.925666 40.562306c-31.540645 14.715345-51.917705 46.671587-51.917705 81.412331 0 49.532815 40.284175 89.832974 89.801005 89.832975s89.801005-40.296962 89.801006-89.832975a22.378321 22.378321 0 1 1 44.756642 0c0 74.209709-60.363922 134.586419-134.557648 134.58642zM512.911117 179.173626H432.860666a22.378321 22.378321 0 1 1 0-44.756642h80.050451a22.378321 22.378321 0 1 1 0 44.756642zM592.833692 255.899298H432.860666a22.378321 22.378321 0 1 1 0-44.756642h159.973026a22.378321 22.378321 0 1 1 0 44.756642zM592.833692 332.62497H432.860666a22.378321 22.378321 0 1 1 0-44.756642h159.973026a22.378321 22.378321 0 1 1 0 44.756642zM592.833692 409.350642H432.860666a22.378321 22.378321 0 1 1 0-44.756642h159.973026a22.378321 22.378321 0 1 1 0 44.756642z" fill="#4F46A3"></path></g></svg>`,
    Humidity: `<svg fill="#fd4893" width="90px" height="90px" viewBox="0 0 64 64" version="1.1" xml:space="preserve" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" stroke="#fd4893"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <g id="cloudy_sunny"></g> <g id="bright"></g> <g id="cloudy"></g> <g id="high_rainfall"></g> <g id="windy"></g> <g id="rain_with_thunder"></g> <g id="clear_night"></g> <g id="cloudy_night"></g> <g id="moon"></g> <g id="sun"></g> <g id="rainy_night"></g> <g id="windy_night"></g> <g id="night_rain_thunder"></g> <g id="windy_rain"></g> <g id="temperature"></g> <g id="humidity"> <g> <path d="M49.7,35.9C47.3,21.2,29.5,4,28.7,3.3c-0.4-0.4-1-0.4-1.4,0C26.4,4.1,6,23.7,6,39c0,12.1,9.9,22,22,22 c3.4,0,6.7-0.8,9.7-2.3c2.1,1.4,4.6,2.3,7.3,2.3c7.2,0,13-5.8,13-13C58,42.5,54.6,37.8,49.7,35.9z M28,59C17,59,8,50,8,39 C8,26.1,24.4,9,28,5.4C31.3,8.7,45,23,47.6,35.3C46.7,35.1,45.9,35,45,35c-7.2,0-13,5.8-13,13c0,3.7,1.5,7,4,9.3 C33.5,58.4,30.8,59,28,59z M45,59c-6.1,0-11-4.9-11-11s4.9-11,11-11s11,4.9,11,11S51.1,59,45,59z"></path> <path d="M28,54c-8.3,0-15-6.7-15-15c0-0.6-0.4-1-1-1s-1,0.4-1,1c0,9.4,7.6,17,17,17c0.6,0,1-0.4,1-1S28.6,54,28,54z"></path> <path d="M48.4,40.1c-0.5-0.2-1.1,0-1.3,0.5l-6,14c-0.2,0.5,0,1.1,0.5,1.3C41.7,56,41.9,56,42,56c0.4,0,0.8-0.2,0.9-0.6l6-14 C49.1,40.9,48.9,40.3,48.4,40.1z"></path> <path d="M44,44c0-1.7-1.3-3-3-3s-3,1.3-3,3s1.3,3,3,3S44,45.7,44,44z M40,44c0-0.6,0.4-1,1-1s1,0.4,1,1s-0.4,1-1,1S40,44.6,40,44z "></path> <path d="M49,49c-1.7,0-3,1.3-3,3s1.3,3,3,3s3-1.3,3-3S50.7,49,49,49z M49,53c-0.6,0-1-0.4-1-1s0.4-1,1-1s1,0.4,1,1S49.6,53,49,53z "></path> </g> </g> <g id="air_pressure"></g> <g id="low_rainfall"></g> <g id="moderate_rainfall"></g> <g id="Sunset"></g> </g></svg>`,
    LightIntensity: `<svg width="90px" height="90px" viewBox="0 0 1024 1024" class="icon" version="1.1" xmlns="http://www.w3.org/2000/svg" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M835.84 387.84c0-156.16-125.44-281.6-281.6-281.6s-281.6 125.44-281.6 281.6c0 108.8 62.72 204.8 153.6 250.88v209.92c0 14.08 11.52 25.6 25.6 25.6h204.8c14.08 0 25.6-11.52 25.6-25.6V638.72c92.16-46.08 153.6-140.8 153.6-250.88z" fill="#FAC546"></path><path d="M656.64 887.04h-204.8c-21.76 0-38.4-16.64-38.4-38.4V646.4c-94.72-51.2-153.6-149.76-153.6-258.56 0-162.56 131.84-294.4 294.4-294.4s294.4 131.84 294.4 294.4c0 108.8-58.88 207.36-153.6 258.56v202.24c0 21.76-16.64 38.4-38.4 38.4z m-102.4-768c-148.48 0-268.8 120.32-268.8 268.8 0 101.12 56.32 193.28 147.2 239.36 3.84 2.56 6.4 6.4 6.4 11.52v209.92c0 7.68 5.12 12.8 12.8 12.8h204.8c7.68 0 12.8-5.12 12.8-12.8V638.72c0-5.12 2.56-8.96 6.4-11.52 90.88-46.08 147.2-138.24 147.2-239.36 0-148.48-120.32-268.8-268.8-268.8z" fill="#231C1C"></path><path d="M682.24 848.64c0 14.08-11.52 25.6-25.6 25.6h-204.8c-14.08 0-25.6-11.52-25.6-25.6v-102.4c0-14.08 11.52-25.6 25.6-25.6h204.8c14.08 0 25.6 11.52 25.6 25.6v102.4z" fill="#C89005"></path><path d="M656.64 887.04h-204.8c-21.76 0-38.4-16.64-38.4-38.4v-102.4c0-21.76 16.64-38.4 38.4-38.4h204.8c21.76 0 38.4 16.64 38.4 38.4v102.4c0 21.76-16.64 38.4-38.4 38.4z m-204.8-153.6c-7.68 0-12.8 5.12-12.8 12.8v102.4c0 7.68 5.12 12.8 12.8 12.8h204.8c7.68 0 12.8-5.12 12.8-12.8v-102.4c0-7.68-5.12-12.8-12.8-12.8h-204.8z" fill="#231C1C"></path><path d="M423.36 772.2752l205.2352-64.1664 7.6288 24.4352-205.2224 64.1664zM423.04 849.1264l256.256-76.8 7.3472 24.512-256.256 76.8z" fill="#231C1C"></path><path d="M477.44 874.24h25.6v25.6h-25.6z" fill="#231C1C"></path><path d="M592.64 874.24h25.6v25.6h-25.6z" fill="#231C1C"></path><path d="M554.24 771.84c-35.84 0-64-28.16-64-64v-204.8c0-3.84 0-15.36 10.24-19.2 11.52-3.84 17.92 5.12 25.6 16.64 6.4 8.96 19.2 28.16 28.16 28.16s21.76-19.2 28.16-28.16c7.68-11.52 14.08-20.48 25.6-16.64 10.24 3.84 10.24 15.36 10.24 19.2v204.8c0 35.84-28.16 64-64 64z m-38.4-241.92v177.92c0 21.76 16.64 38.4 38.4 38.4s38.4-16.64 38.4-38.4V529.92c-10.24 12.8-23.04 24.32-38.4 24.32s-28.16-11.52-38.4-24.32z" fill="#231C1C"></path></g></svg>`,
    SoilMoisture: `<svg width="90px" height="90px" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" fill="#5fceff" class="bi bi-moisture"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M13.5 0a.5.5 0 0 0 0 1H15v2.75h-.5a.5.5 0 0 0 0 1h.5V7.5h-1.5a.5.5 0 0 0 0 1H15v2.75h-.5a.5.5 0 0 0 0 1h.5V15h-1.5a.5.5 0 0 0 0 1h2a.5.5 0 0 0 .5-.5V.5a.5.5 0 0 0-.5-.5h-2zM7 1.5l.364-.343a.5.5 0 0 0-.728 0l-.002.002-.006.007-.022.023-.08.088a28.458 28.458 0 0 0-1.274 1.517c-.769.983-1.714 2.325-2.385 3.727C2.368 7.564 2 8.682 2 9.733 2 12.614 4.212 15 7 15s5-2.386 5-5.267c0-1.05-.368-2.169-.867-3.212-.671-1.402-1.616-2.744-2.385-3.727a28.458 28.458 0 0 0-1.354-1.605l-.022-.023-.006-.007-.002-.001L7 1.5zm0 0-.364-.343L7 1.5zm-.016.766L7 2.247l.016.019c.24.274.572.667.944 1.144.611.781 1.32 1.776 1.901 2.827H4.14c.58-1.051 1.29-2.046 1.9-2.827.373-.477.706-.87.945-1.144zM3 9.733c0-.755.244-1.612.638-2.496h6.724c.395.884.638 1.741.638 2.496C11 12.117 9.182 14 7 14s-4-1.883-4-4.267z"></path> </g></svg>`,
    pH: `<svg height="90px" width="90px" version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 512 512" xml:space="preserve" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path style="fill:#439EE8;" d="M285.929,414.731h-59.858c-4.428,0-8.017,3.589-8.017,8.017v81.236c0,4.427,3.588,8.017,8.017,8.017 h59.858c4.428,0,8.017-3.589,8.017-8.017v-81.236C293.946,418.32,290.357,414.731,285.929,414.731z"></path> <path style="fill:#5293C4;" d="M293.946,444.125v-21.378c0-4.427-3.589-8.017-8.017-8.017h-40.618h-19.24 c-4.427,0-8.017,3.589-8.017,8.017v21.378v59.858c0,4.427,3.589,8.017,8.017,8.017h19.24c-4.428,0-8.017-3.589-8.017-8.017v-56.117 c0-2.066,1.675-3.741,3.741-3.741H293.946z"></path> <path style="fill:#5CC4E0;" d="M379.992,0H132.008c-4.427,0-8.017,3.589-8.017,8.017v226.607c0,2.379,1.057,4.635,2.884,6.158 l72.154,60.127c1.219,1.015,1.923,2.519,1.923,4.106v117.733c0,4.427,3.589,8.017,8.017,8.017h94.063 c4.427,0,8.017-3.589,8.017-8.017V305.014c0-1.586,0.704-3.09,1.923-4.106l72.154-60.127c1.828-1.523,2.884-3.779,2.884-6.158V8.017 C388.008,3.589,384.419,0,379.992,0z"></path> <path style="fill:#439EE8;" d="M221.261,422.747V305.014c0-1.586-0.704-3.09-1.923-4.106l-72.154-60.127 c-1.828-1.523-2.884-3.78-2.884-6.159V8.017c0-4.427,3.588-8.017,8.017-8.017h-20.309c-4.427,0-8.017,3.589-8.017,8.017v226.605 c0,2.379,1.056,4.636,2.884,6.159l72.154,60.127c1.219,1.015,1.923,2.519,1.923,4.106v117.733c0,4.427,3.589,8.017,8.017,8.017 h20.309C224.849,430.764,221.261,427.175,221.261,422.747z"></path> <g> <path style="fill:#BEE7F3;" d="M259.207,33.136h-7.482c-4.428,0-8.017-3.589-8.017-8.017s3.588-8.017,8.017-8.017h7.482 c4.428,0,8.017,3.589,8.017,8.017S263.635,33.136,259.207,33.136z"></path> <path style="fill:#BEE7F3;" d="M296.618,33.136h-7.482c-4.428,0-8.017-3.589-8.017-8.017s3.588-8.017,8.017-8.017h7.482 c4.428,0,8.017,3.589,8.017,8.017S301.046,33.136,296.618,33.136z"></path> <path style="fill:#BEE7F3;" d="M334.029,33.136h-7.482c-4.428,0-8.017-3.589-8.017-8.017s3.588-8.017,8.017-8.017h7.482 c4.428,0,8.017,3.589,8.017,8.017S338.458,33.136,334.029,33.136z"></path> <path style="fill:#BEE7F3;" d="M222.864,33.136h-7.482c-4.428,0-8.017-3.589-8.017-8.017s3.588-8.017,8.017-8.017h7.482 c4.428,0,8.017,3.589,8.017,8.017S227.293,33.136,222.864,33.136z"></path> <path style="fill:#BEE7F3;" d="M185.453,33.136h-7.482c-4.428,0-8.017-3.589-8.017-8.017s3.588-8.017,8.017-8.017h7.482 c4.428,0,8.017,3.589,8.017,8.017S189.881,33.136,185.453,33.136z"></path> </g> <path style="fill:#5293C4;" d="M345.787,42.756H166.213c-4.428,0-8.017,3.589-8.017,8.017v149.645c0,4.427,3.588,8.017,8.017,8.017 h179.574c4.428,0,8.017-3.589,8.017-8.017V50.772C353.804,46.345,350.215,42.756,345.787,42.756L345.787,42.756z"></path> <path style="fill:#E0DDDF;" d="M174.23,188.66V62.53c0-2.066,1.675-3.741,3.741-3.741h156.058c2.066,0,3.741,1.675,3.741,3.741 V188.66c0,2.066-1.675,3.741-3.741,3.741H177.971C175.905,192.401,174.23,190.726,174.23,188.66z"></path> <path style="fill:#F9F8F9;" d="M184.384,185.453h142.163c2.066,0,3.741-1.675,3.741-3.741V69.478c0-2.066-1.675-3.741-3.741-3.741 H184.384c-2.066,0-3.741,1.675-3.741,3.741v112.234C180.643,183.778,182.318,185.453,184.384,185.453z"></path> <g> <path style="fill:#FF675C;" d="M238.898,76.96h-42.756c-4.428,0-8.017,3.589-8.017,8.017v81.236c0,4.427,3.588,8.017,8.017,8.017 s8.017-3.589,8.017-8.017v-34.739h34.739c4.428,0,8.017-3.589,8.017-8.017v-38.48C246.914,80.55,243.326,76.96,238.898,76.96z M230.881,115.441h-26.722V92.994h26.722V115.441z"></path> <path style="fill:#FF675C;" d="M315.858,76.96c-4.428,0-8.017,3.589-8.017,8.017v30.463h-35.273V84.977 c0-4.427-3.588-8.017-8.017-8.017s-8.017,3.589-8.017,8.017v81.236c0,4.427,3.588,8.017,8.017,8.017s8.017-3.589,8.017-8.017 v-34.739h35.273v34.739c0,4.427,3.588,8.017,8.017,8.017c4.428,0,8.017-3.589,8.017-8.017V84.977 C323.875,80.55,320.286,76.96,315.858,76.96z"></path> </g> <path style="fill:#F78B4F;" d="M215.382,221.795c-15.03,0-27.257,12.228-27.257,27.257c0,15.03,12.227,27.257,27.257,27.257 c15.03,0,27.257-12.227,27.257-27.257C242.639,234.024,230.412,221.795,215.382,221.795z"></path> <path style="fill:#FBEFA5;" d="M215.382,230.347c10.315,0,18.706,8.391,18.706,18.706c0,10.315-8.391,18.706-18.706,18.706 s-18.706-8.391-18.706-18.706C196.676,238.737,205.067,230.347,215.382,230.347 M215.382,221.795 c-15.03,0-27.257,12.228-27.257,27.257c0,15.03,12.227,27.257,27.257,27.257c15.03,0,27.257-12.227,27.257-27.257 C242.639,234.024,230.412,221.795,215.382,221.795L215.382,221.795z"></path> <path style="fill:#F78B4F;" d="M296.618,221.795c-15.029,0-27.257,12.228-27.257,27.257c0,15.03,12.228,27.257,27.257,27.257 c15.029,0,27.257-12.227,27.257-27.257C323.875,234.024,311.647,221.795,296.618,221.795z"></path> <path style="fill:#FBEFA5;" d="M296.618,230.347c10.315,0,18.706,8.391,18.706,18.706c0,10.315-8.391,18.706-18.706,18.706 s-18.706-8.391-18.706-18.706C277.912,238.737,286.303,230.347,296.618,230.347 M296.618,221.795 c-15.03,0-27.257,12.228-27.257,27.257c0,15.03,12.227,27.257,27.257,27.257c15.03,0,27.257-12.227,27.257-27.257 C323.875,234.024,311.648,221.795,296.618,221.795L296.618,221.795z"></path> </g></svg>`,
    NPK: `<svg width="90px" height="90px" viewBox="0 0 1024 1024" class="icon" version="1.1" xmlns="http://www.w3.org/2000/svg" fill="#000000"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M682.666667 512m-192 0a192 192 0 1 0 384 0 192 192 0 1 0-384 0Z" fill="#B2EBF2"></path><path d="M682.666667 256c-140.8 0-256 115.2-256 256s115.2 256 256 256 256-115.2 256-256-115.2-256-256-256z m0 426.666667c-93.866667 0-170.666667-76.8-170.666667-170.666667s76.8-170.666667 170.666667-170.666667 170.666667 76.8 170.666666 170.666667-76.8 170.666667-170.666666 170.666667z" fill="#4DD0E1"></path><path d="M541.866667 469.333333L422.4 108.8l-132.266667 482.133333-46.933333-121.6H85.333333v85.333334h98.133334l123.733333 305.066666 123.733333-456.533333 51.2 151.466667H640v-85.333334z" fill="#3F51B5"></path><path d="M682.666667 512m-85.333334 0a85.333333 85.333333 0 1 0 170.666667 0 85.333333 85.333333 0 1 0-170.666667 0Z" fill="#3F51B5"></path></g></svg>`,
    Default: `<svg fill="#808080" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16 2a2 2 0 0 0-2 2v10.586l-.293-.293a1 1 0 0 0-1.414 1.414l2 2a1 1 0 0 0 1.414 0l2-2a1 1 0 0 0-1.414-1.414L18 14.586V4a2 2 0 0 0-2-2z"></path></svg>`,
  };

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

  // document.getElementById(
  //   "username-display"
  // ).textContent = `Greenhouse owner: ${username}`;

  // document.getElementById(
  //   "title"
  // ).textContent = `${greenhouseName} - ${greenhouseLocation}`;

  // document.getElementById("logout-button").addEventListener("click", () => {
  //   // clear the token and user information from local storage and redirect to login page
  //   localStorage.removeItem("token");
  //   localStorage.removeItem("user_id");
  //   localStorage.removeItem("username");
  //   localStorage.removeItem("greenhouse_id");
  //   localStorage.removeItem("greenhouse_name");
  //   localStorage.removeItem("greenhouse_location");
  //   window.location.href = "loginform.html";
  // });

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

       mindomain = sensor.domain.min
       maxdomain = sensor.domain.max

        // handle the threshold in the special case of NPK sensor
        if (sensor.type === "NPK") {
          console.log(sensor.domain);
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
        const sensorIcon = sensorIcons[sensor.type] || sensorIcons.Default;

        card.innerHTML = `
          <button class="delete-btn" title="Delete Sensor" style="position:absolute; right:10px; top:10px; background:none; border:none; font-size:20px; cursor:pointer;">
            <!-- svg content -->
            <svg fill="#ed0c0c" width="20px" height="20px" viewBox="-3.5 0 19 19" xmlns="http://www.w3.org/2000/svg" class="cf-icon-svg" stroke="#ed0c0c"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"><path d="M11.383 13.644A1.03 1.03 0 0 1 9.928 15.1L6 11.172 2.072 15.1a1.03 1.03 0 1 1-1.455-1.456l3.928-3.928L.617 5.79a1.03 1.03 0 1 1 1.455-1.456L6 8.261l3.928-3.928a1.03 1.03 0 0 1 1.455 1.456L7.455 9.716z"></path></g></svg>
          </button>
                <div class="card-img">
                   ${sensorIcon}
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
                    <div class="rating">
                        <h6 class="primary-text">${mindomain}</h6>
                        <h6 class="secondary-text">Min Domain</h6>
                    </div>
                    <div class="rating">
                        <h6 class="primary-text">${maxdomain}</h6>
                        <h6 class="secondary-text">Max Domain</h6>
                    </div>
                </div>`;

        dashboardCards.appendChild(card);

        //delete sensor 
        card.querySelector(".delete-btn").addEventListener("click", () => {
          if (confirm(`Are you sure you want to delete ${sensor.name}?`)) {
            fetch("../json/WebApp_config.json")
              .then((res) => res.json())
              .then((config) => {
                const catalog_url = config.catalog_url;
                return fetch(`${catalog_url}/remove_sensor_from_greenhouse`, {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                  },
                  body: JSON.stringify({
                    greenhouse_id: greenhouseId,
                    sensor_id: sensor.sensor_id,
                  }),
                });
              })
              .then((res) => res.json())
              .then((result) => {
                alert(result.message || "Sensor deleted successfully.");
                card.remove();
              })
              .catch((err) => {
                console.error("Error deleting sensor:", err);
                alert("Failed to delete sensor.");
              });
          }
        });


        // Modal for setting threshold
        const setThresholdBtn = card.querySelector(
          `#set-threshold-button-${sensor.sensor_id}`
        );

        setThresholdBtn.addEventListener("click", () => {
          const modal = document.createElement("div");
          modal.className = "modal d-flex";
          if (sensor.type === "NPK") {
            modal.innerHTML = `
        <div class="modal-content">
            <span class="close" style="float: right; font-size: 24px; cursor: pointer;">&times;</span>
            <h1>Set Threshold for ${sensor.name}</h1>
            <form id="thresholdForm-${sensor.sensor_id}">
                <div class="form-group">
                <label for="min-threshold"> N Min Threshold:</label>
                <input class="form-control fs-4" type="number" id="n-min-threshold-${sensor.sensor_id}" value="${
                  sensor.threshold.N.min || 0
                }" required />
                </div>
                
                <div class="form-group">
                <label for="max-threshold"> N Max Threshold:</label>
                <input class="form-control fs-4" type="number" id="n-max-threshold-${sensor.sensor_id}" value="${
                  sensor.threshold.N.max || 0
                }" required />
                </div>

                 <div class="form-group">
                <label for="max-threshold">P Min Threshold:</label>
                <input class="form-control fs-4" type="number" id="p-min-threshold-${sensor.sensor_id}" value="${
                  sensor.threshold.P.min || 0
                }" required />
                </div>
                 <div class="form-group">
                <label for="max-threshold"> P Max Threshold:</label>
                <input class="form-control fs-4" type="number" id="p-max-threshold-${sensor.sensor_id}" value="${
                  sensor.threshold.P.max || 0
                }" required />
                </div>

                 <div class="form-group">
                <label for="max-threshold"> K Min Threshold:</label>
                <input class="form-control fs-4" type="number" id="k-min-threshold-${sensor.sensor_id}" value="${
                  sensor.threshold.K.min || 0
                }" required />
                </div>
                 <div class="form-group">
                <label for="max-threshold"> K Max Threshold:</label>
                <input class="form-control fs-4" type="number" id="k-max-threshold-${sensor.sensor_id}" value="${
                  sensor.threshold.K.max || 0
                }" required />
                </div>

                <button class="btn btn-primary btn-lg btnmodal fs-4" type="submit">Save</button>
            </form>
        </div>
    `;
          } else {
            modal.innerHTML = `
            <div class="modal-content">
                <span class="close" style="float: right; font-size: 24px; cursor: pointer;">&times;</span>
                <h1>Set Threshold for ${sensor.name}</h1>
                <form id="thresholdForm-${sensor.sensor_id}">
                    <div class="form-group">
                    <label for="min-threshold">Min Threshold:</label>
                    <input class="form-control fs-4" type="number" id="min-threshold-${sensor.sensor_id}" value="${
                      sensor.threshold?.min || 0
                    }" required />
                    </div>
                    
                    <div class="form-group">
                    <label for="max-threshold">Max Threshold:</label>
                    <input class="form-control fs-4" type="number" id="max-threshold-${sensor.sensor_id}" value="${
                      sensor.threshold?.max || 0
                    }" required />
                    </div>
    
                    <button class="btn btn-primary btn-lg btnmodal fs-4" type="submit">Save</button>
                </form>
            </div>
        `;
          }

          document.body.appendChild(modal);

          modal.querySelector(".close").addEventListener("click", () => {
            modal.remove();
          });

          modal
            .querySelector(`#thresholdForm-${sensor.sensor_id}`)
            .addEventListener("submit", (e) => {
              e.preventDefault();
              let payload;

              if (sensor.type === "NPK") {
                const updatedNMin = parseFloat(document.getElementById(`n-min-threshold-${sensor.sensor_id}`).value);
                const updatedNMax = parseFloat(document.getElementById(`n-max-threshold-${sensor.sensor_id}`).value); 
                const updatedPMin = parseFloat(document.getElementById(`p-min-threshold-${sensor.sensor_id}`).value);
                const updatedPMax = parseFloat(document.getElementById(`p-max-threshold-${sensor.sensor_id}`).value);
                const updatedKMin = parseFloat(document.getElementById(`k-min-threshold-${sensor.sensor_id}`).value);
                const updatedKMax = parseFloat(document.getElementById(`k-max-threshold-${sensor.sensor_id}`).value);
                //validate the threshold against domain
                if (
                  updatedNMin < mindomain || updatedNMax > maxdomain ||
                  updatedPMin < mindomain || updatedPMax > maxdomain ||
                  updatedKMin < mindomain || updatedKMax > maxdomain
                ) {
                  alert("Threshold values must be within the allowed domain range.");
                  return; // Stop submission if validation fails
                }
               //validate that min shpuld be less than max
               if(updatedNMin > updatedNMax || updatedPMin > updatedPMax || updatedKMin > updatedKMax)
               {
                alert("Min threshold should be less than max threshold");
                return; // Stop submission if validation fails
               }
                payload ={
                  sensor_id: sensor.sensor_id,
                  threshold: {
                    N: { min: updatedNMin, max: updatedNMax },
                    P: { min: updatedPMin, max: updatedPMax },
                    K: { min: updatedKMin, max: updatedKMax }
                  },
                };
              }else
              {
                const updatedMin = parseFloat(document.getElementById(`min-threshold-${sensor.sensor_id}`).value);
                const updatedMax = parseFloat(document.getElementById(`max-threshold-${sensor.sensor_id}`).value); 

                 // Validate the thresholds against the domain
                  if (updatedMin < mindomain || updatedMax > maxdomain) {
                    alert("Threshold values must be within the allowed domain range.");
                    return; // Stop submission if validation fails
                  }
                  //validate min must be less than max
                  if(updatedMin > updatedMax)
                  {
                    alert("Min threshold should be less than max threshold");
                    return; // Stop submission if validation fails
                  }
                payload = {
                  sensor_id: sensor.sensor_id,
                  threshold: {
                    min: updatedMin,
                    max: updatedMax,
                  },
                };
              }

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
                    body: JSON.stringify(
                      payload
                    ),
                  });
                })
                .then((res) => res.json())
                .then((result) => {
                  alert(result.message || "Threshold updated!");
                  modal.remove();
                  location.reload(); // reload the page to reflect the changes
                })
                .catch((err) => {
                  console.error("Error updating threshold:", err);
                  alert("Failed to update threshold.");
                });
            });
        });
  

      });

        // Add Sensors Button
    // fetch sensors and show available ones 
    document.getElementById("add-sensor-btn").addEventListener("click", () => {
      fetch("../json/WebApp_config.json")
        .then((res) => res.json())
        .then((config) => {
          const catalog_url = config.catalog_url;
          return fetch(`${catalog_url}/get_all_sensors`, {
            headers: { Authorization: `Bearer ${token}` },
          });
        })
        
        .then((res) => res.json())
       
        .then((availableSensors) => {
          const select = document.getElementById("sensor-select");
          select.innerHTML = "";
          availableSensors.sensors.forEach((sensor) => {
            const option = document.createElement("option");
            option.value = sensor.sensor_id;
            option.textContent = `${sensor.name} (${sensor.type})`;
            select.appendChild(option);
          });
          document.getElementById("sensor-modal").classList.remove("d-none");
        })
        .catch((err) => {
          console.error("Failed to load available sensors:", err);
          alert("Failed to load available sensors.");
        });
    });

    document.getElementById("cancel-modal").addEventListener("click", () => {
      document.getElementById("sensor-modal").classList.add("d-none");
    });

    document.getElementById("confirm-add-sensor").addEventListener("click", () => {
      const sensorId = document.getElementById("sensor-select").value;
      fetch("../json/WebApp_config.json")
        .then((res) => res.json())
        .then((config) => {
          console.log(greenhouseId, sensorId)
          const catalog_url = config.catalog_url;
          return fetch(`${catalog_url}/add_sensor_from_available`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            
            body: JSON.stringify({
              greenhouse_id: greenhouseId,
              sensor_id: sensorId,
            }),
          });
        })
        .then((res) => res.json())
        .then((result) => {
          alert(result.message || "sensor added successfully.");
          location.reload();
        })
        .catch((err) => {
          console.error("Failed to add sensor:", err);
          alert("Failed to add sensor.");
          location.reload(); // still reload to reset modal state
        });
    });


    })
    .catch((error) => {
      console.error("Error:", error.message);
      alert("An error occurred while fetching sensor data");
    });




});
