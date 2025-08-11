const form = document.getElementById('filterForm');
const ctx = document.getElementById('sensorChart').getContext('2d');
let chart;

form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const params = new URLSearchParams(new FormData(form)).toString();
    const response = await fetch(`/sensor-data/?${params}&page=1&page_size=1000`);
    const data = await response.json();
    const results = data.results;

    if (!results.length) {
        alert("No data found for the given criteria.");
        return;
    }

    const type = form.type.value;
    const timestamps = results.map(entry => entry.timestamp);
    const values = results.map(entry => {
        if (type === "Temperature") return entry.temperature;
        if (type === "Humidity") return entry.humidity;
        if (type === "Acoustic") return entry.soundLevel;
        return null;
    });

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timestamps,
            datasets: [{
                label: `${type} Readings`,
                data: values,
                borderWidth: 2,
                fill: false,
                borderColor: 'blue',
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        tooltipFormat: 'MMM d, HH:mm',
                        displayFormats: {
                            hour: 'HH:mm',
                            day: 'MMM d'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Timestamp'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: `${type} Value`
                    }
                }
            }
        }
    });
});
