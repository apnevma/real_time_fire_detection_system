// Random color generator
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

const locationColors = {
    'A-1': '#630000ff',
    'A-2': '#d10000ff',
    'A-3': '#ff7066ff',
    'A-4': '#ffaa79ff',
    'B-1': '#000066',
    'B-2': '#1f48c2ff',
    'B-3': '#78b2fdff',
    'B-4': '#72eaffff',
    'C-1': '#0d3f02ff',
    'C-2': '#2e8307ff',
    'C-3': '#77b300',
    'C-4': '#ace600',
};

// Add new location block when "add location" button is clicked
const addBtn = document.getElementById('addLocationBtn');

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('addLocationBtn')?.addEventListener('click', () => {
        console.log('Clicked!')
        const locationFields = document.getElementById('locationFields');
        const newBlock = document.createElement('div');
        newBlock.classList.add('location-block');
        newBlock.innerHTML = `
            <div class="building-floor-row">
                <div class="form-group">
                    <label>Building:</label>
                    <select name="building">
                        <option value="A">A</option>
                        <option value="B">B</option>
                        <option value="C">C</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Floor:</label>
                    <input type="number" name="floor" min="1" max="4">
                </div>
            </div>
        `;
        locationFields.appendChild(newBlock);
    });
});

// Remove location block when "remove location" button is clicked
const removeBtn = document.getElementById('removeLocationBtn')

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('removeLocationBtn')?.addEventListener('click', () => {
        console.log('Remove Location clicked!')
        const locationFields = document.getElementById('locationFields');
        const blocks = locationFields.getElementsByClassName('location-block');
        if (blocks.length > 1) {
            locationFields.removeChild(blocks[blocks.length -1]);
        }
    });
});

// Plot data when form is submitted
const form = document.getElementById('filterForm');
const ctx = document.getElementById('sensorChart').getContext('2d');
let chart;

form.addEventListener('submit', async function (e) {
    e.preventDefault();

    const type = form.type.value;
    const startTime = form.start_time.value;
    const endTime = form.end_time.value;

    // Get all building/floor pairs
    const locationBlocks = document.querySelectorAll('.location-block');

    if (locationBlocks.length === 0) {
        alert("Please add at least one building/floor pair.");
        return;
    }

    // Fetch data for each building-floor pair
    const datasets = [];

    for (const block of locationBlocks) {
        const building = block.querySelector('select[name="building"]').value;
        const floor = block.querySelector('input[name="floor"]').value;

        const params = new URLSearchParams({
            type,
            building,
            floor,
            start_time: startTime,
            end_time: endTime,
            page: 1,
            page_size: 1000
        });

        try {
            const response = await fetch(`/sensor-data/?${params.toString()}`);
            const data = await response.json();
            const results = data.results;

            if (results.length === 0) continue;

            const timestamps = results.map(entry => entry.timestamp);
            const values = results.map(entry => {
                if (type === "Temperature") return entry.temperature;
                if (type === "Humidity") return entry.humidity;
                if (type === "Acoustic") return entry.soundLevel;
                return null;
            });

            const key = `${building}-${floor}`;
            const color = locationColors[key] || 'black';  // fallback color

            datasets.push({
                label: `${type} - ${building} Floor ${floor}`,
                data: values,
                borderWidth: 2,
                fill: false,
                borderColor: color,
                tension: 0.2,
                parsing: {
                    xAxisKey: 'x',
                    yAxisKey: 'y'
                },
                data: timestamps.map((t, i) => ({ x: t, y: values[i] }))
            });
        } catch (error) {
            console.error(`Error fetching data for ${building} floor ${floor}:`, error);
        }
    }

    if (datasets.length === 0) {
        alert("No data found for the given criteria.");
        return;
    }

    if (chart) chart.destroy();

    // Create new chart
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            datasets: datasets
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
