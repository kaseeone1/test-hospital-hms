// Dashboard JavaScript functions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize counters with animation
    const counters = document.querySelectorAll('.counter-value');
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));
        const duration = 1000; // milliseconds
        const step = target / (duration / 10); // update every 10ms
        let current = 0;
        
        const updateCounter = () => {
            current += step;
            if (current < target) {
                counter.textContent = Math.ceil(current);
                setTimeout(updateCounter, 10);
            } else {
                counter.textContent = target;
            }
        };
        
        updateCounter();
    });

    // Render charts if they exist on the page
    renderRevenueChart();
    renderVisitorsChart();
});

// Function to render revenue charts if the element exists
function renderRevenueChart() {
    const revenueChartElem = document.getElementById('revenueChart');
    if (!revenueChartElem) return;

    // Get current date
    const today = new Date();
    const labels = [];
    
    // Generate labels for last 7 days
    for (let i = 6; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        labels.push(d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    
    // Sample data (will be replaced by actual data from backend)
    const data = {
        labels: labels,
        datasets: [{
            label: 'Daily Revenue',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgb(75, 192, 192)',
            data: [0, 0, 0, 0, 0, 0, 0], // Empty data until populated by actual data
            fill: true,
            tension: 0.4
        }]
    };
    
    // Get context and create chart
    const ctx = revenueChartElem.getContext('2d');
    const revenueChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Revenue Trend (Last 7 Days)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        // Format y-axis labels as currency
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });
    
    // If there's actual chart data in the page, update the chart
    const chartDataElement = document.getElementById('revenueChartData');
    if (chartDataElement) {
        try {
            const chartData = JSON.parse(chartDataElement.textContent);
            revenueChart.data.labels = chartData.labels;
            revenueChart.data.datasets[0].data = chartData.data;
            revenueChart.update();
        } catch (e) {
            console.error('Error parsing chart data', e);
        }
    }
}

// Function to render visitors chart if the element exists
function renderVisitorsChart() {
    const visitorsChartElem = document.getElementById('visitorsChart');
    if (!visitorsChartElem) return;
    
    // Get current date
    const today = new Date();
    const labels = [];
    
    // Generate labels for last 7 days
    for (let i = 6; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        labels.push(d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    
    // Sample data (will be replaced by actual data from backend)
    const data = {
        labels: labels,
        datasets: [{
            label: 'Patient Visits',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgb(54, 162, 235)',
            data: [0, 0, 0, 0, 0, 0, 0], // Empty data until populated by actual data
            borderWidth: 1
        }]
    };
    
    // Get context and create chart
    const ctx = visitorsChartElem.getContext('2d');
    const visitorsChart = new Chart(ctx, {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Patient Visits (Last 7 Days)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
    
    // If there's actual chart data in the page, update the chart
    const chartDataElement = document.getElementById('visitorsChartData');
    if (chartDataElement) {
        try {
            const chartData = JSON.parse(chartDataElement.textContent);
            visitorsChart.data.labels = chartData.labels;
            visitorsChart.data.datasets[0].data = chartData.data;
            visitorsChart.update();
        } catch (e) {
            console.error('Error parsing chart data', e);
        }
    }
}

// Clock for dashboard
function updateClock() {
    const clockElement = document.getElementById('dashboardClock');
    if (clockElement) {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        const dateString = now.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        
        clockElement.textContent = `${dateString} ${timeString}`;
    }
}

// Update clock every second
setInterval(updateClock, 1000);
updateClock(); // Initial call
