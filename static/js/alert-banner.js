const banner = document.getElementById("fire-alert-banner");

// Connect to WebSocket server
const socket = new WebSocket(`ws://${window.location.host}/ws/alerts`);

socket.onmessage = function(event) {
    const alert = JSON.parse(event.data);

    const message = `🔥 FIRE ALERT: Building ${alert.building}, Floor ${alert.floor} at ${alert.detected_at}`;
    banner.innerText = message;
    banner.style.display = "block";

    // Hide banner after 60 seconds
    setTimeout(() => {
        banner.style.display = "none";
    }, 60000);
};

socket.onopen = function() {
    console.log("WebSocket connection opened!");
};

socket.onerror = function(error) {
    console.error("WebSocket error:", error);
};

socket.onclose = function() {
    console.warn("WebSocket connection closed");
};
