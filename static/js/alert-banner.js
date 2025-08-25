const { DateTime } = luxon;

const banner = document.getElementById("fire-alert-banner");

// Connect to WebSocket server
const socket = new WebSocket(`ws://${window.location.host}/ws/alerts`);

// empty array to hold incoming incoming fire alerts
const alertQueue = [];

socket.onopen = function() {
    console.log("WebSocket connection opened!");
};

socket.onmessage = function(event) {
    const alert = JSON.parse(event.data);
    console.log("Received Alert!");
    alertQueue.push(alert);

    if (alertQueue.length === 1) {
        showNextAlert();
    }
};

function showNextAlert() {
    if (alertQueue.length === 0) return;

    console.log("Showing Alert!");
    const alert = alertQueue[0];

    const readableTime = DateTime.fromISO(alert.detected_at).toLocaleString(DateTime.DATETIME_MED);

    Swal.fire({
    icon: 'warning',
    title: '🔥 FIRE ALERT!',
    html: `
      <strong>Building:</strong> ${alert.building}<br>
      <strong>Floor:</strong> ${alert.floor}<br>
      <strong>Detected at:</strong> ${readableTime}
    `,
    confirmButtonText: 'Got it!',
    timer: 60000,
    timerProgressBar: true,
    background: '#fddedeff',
    showClass: {
      popup: 'swal2-show animate__animated animate__shakeX'
    }
  }).then(() => {
    alertQueue.shift();
    showNextAlert();
  });
}

socket.onerror = function(error) {
    console.error("WebSocket error:", error);
};

socket.onclose = function() {
    console.warn("WebSocket connection closed");
};
