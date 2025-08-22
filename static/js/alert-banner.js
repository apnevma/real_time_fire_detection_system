const banner = document.getElementById("fire-alert-banner");

// Connect to WebSocket server
const socket = new WebSocket(`ws://${window.location.host}/ws/alerts`);

socket.onopen = function() {
    console.log("WebSocket connection opened!");
};

socket.onmessage = function(event) {
    const alert = JSON.parse(event.data);

    Swal.fire({
    icon: 'warning',
    title: '🔥 FIRE ALERT!',
    html: `
      <strong>Building:</strong> ${alert.building}<br>
      <strong>Floor:</strong> ${alert.floor}<br>
      <strong>Detected at:</strong> ${alert.detected_at}
    `,
    confirmButtonText: 'Got it!',
    background: '#fff0f0',
    showClass: {
      popup: 'swal2-show animate__animated animate__shakeX'
    }
  });
};

socket.onerror = function(error) {
    console.error("WebSocket error:", error);
};

socket.onclose = function() {
    console.warn("WebSocket connection closed");
};
