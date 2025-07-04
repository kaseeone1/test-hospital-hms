// Reports module JavaScript functions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize date range pickers
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    const reportTypeSelect = document.getElementById('report_type');
    const periodSelect = document.getElementById('period');
    
    if (dateFromInput && dateToInput) {
        // Set default dates if not already set
        if (!dateFromInput.value) {
            // Default to first day of current month
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            dateFromInput.valueAsDate = firstDay;
        }
        
        if (!dateToInput.value) {
            // Default to today
            dateToInput.valueAsDate = new Date();
        }
        
        // Ensure to date is not before from date
        dateFromInput.addEventListener('change', function() {
            if (dateToInput.value && dateFromInput.value > dateToInput.value) {
                dateToInput.value = dateFromInput.value;
            }
        });
        
        dateToInput.addEventListener('change', function() {
            if (dateFromInput.value && dateToInput.value < dateFromInput.value) {
                dateFromInput.value = dateToInput.value;
            }
        });
    }
    
    // Update date range when period changes
    if (periodSelect) {
        periodSelect.addEventListener('change', function() {
            setDateRangeFromPeriod(this.value);
        });
    }
    
    // Render charts if element exists
    renderReportCharts();
    
    // Print report button
    const printReportBtn = document.getElementById('printReportBtn');
    if (printReportBtn) {
        printReportBtn.addEventListener('click', function() {
            window.print();
        });
    }
});

// Set date range based on selected period
function setDateRangeFromPeriod(period) {
    const dateFromInput = document.getElementById('date_from');
    const dateToInput = document.getElementById('date_to');
    
    if (!dateFromInput || !dateToInput) return;
    
    const today = new Date();
    let fromDate;
    
    switch (period) {
        case 'today':
            fromDate = today;
            break;
        case 'yesterday':
            fromDate = new Date(today);
            fromDate.setDate(today.getDate() - 1);
            break;
        case 'this_week':
            fromDate = new Date(today);
            // Get first day of current week (Sunday = 0)
            const dayOfWeek = today.getDay();
            fromDate.setDate(today.getDate() - dayOfWeek);
            break;
        case 'last_week':
            fromDate = new Date(today);
            // Get first day of last week
            const lastWeekDay = today.getDay() + 7;
            fromDate.setDate(today.getDate() - lastWeekDay);
            const lastWeekToDate = new Date(fromDate);
            lastWeekToDate.setDate(fromDate.getDate() + 6);
            dateToInput.valueAsDate = lastWeekToDate;
            break;
        case 'this_month':
            fromDate = new Date(today.getFullYear(), today.getMonth(), 1);
            break;
        case 'last_month':
            // First day of previous month
            fromDate = new Date(today.getFullYear(), today.getMonth() - 1, 1);
            // Last day of previous month
            const lastMonthToDate = new Date(today.getFullYear(), today.getMonth(), 0);
            dateToInput.valueAsDate = lastMonthToDate;
            break;
        case 'this_year':
            fromDate = new Date(today.getFullYear(), 0, 1);
            break;
        case 'custom':
            // Do nothing, keep the current date selections
            return;
        default:
            // Default to last 30 days
            fromDate = new Date(today);
            fromDate.setDate(today.getDate() - 30);
    }
    
    // Update the date inputs
    dateFromInput.valueAsDate = fromDate;
    
    // Update to date to today for periods that end today
    if (['today', 'this_week', 'this_month', 'this_year'].includes(period)) {
        dateToInput.valueAsDate = today;
    }
}

// Render charts for reports
function renderReportCharts() {
    const chartContainer = document.getElementById('reportChart');
    if (!chartContainer) return;
    
    // Get chart data from hidden div
    const chartDataElement = document.getElementById('chartData');
    if (!chartDataElement) return;
    
    try {
        const chartData = JSON.parse(chartDataElement.textContent);
        const reportType = document.getElementById('reportType')?.value || 'sales';
        
        // Create appropriate chart based on report type
        switch (reportType) {
            case 'sales':
                renderSalesChart(chartData);
                break;
            case 'patients':
                renderPatientsChart(chartData);
                break;
            case 'inventory':
                renderInventoryChart(chartData);
                break;
            case 'staff':
                renderStaffChart(chartData);
                break;
            case 'medicine':
                renderMedicineChart(chartData);
                break;
            case 'financial':
                renderFinancialChart(chartData);
                break;
            case 'trends':
                renderTrendsChart(chartData);
                break;
            case 'comparative':
                renderComparativeChart(chartData);
                break;
            default:
                console.warn('Unknown report type:', reportType);
        }
    } catch (e) {
        console.error('Error parsing chart data', e);
    }
}

// Render sales report chart
function renderSalesChart(data) {
    const ctx = document.getElementById('reportChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Pharmacy Sales',
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1,
                    data: data.pharmacy
                },
                {
                    label: 'Service Revenue',
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 1,
                    data: data.services
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Revenue Breakdown'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });
}

// Render patients report chart
function renderPatientsChart(data) {
    const ctx = document.getElementById('reportChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'New Patients',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1,
                    data: data.new_patients
                },
                {
                    label: 'Patient Visits',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgb(54, 162, 235)',
                    tension: 0.1,
                    data: data.visits
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Patient Statistics'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Count'
                    },
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

// Render inventory report chart
function renderInventoryChart(data) {
    const ctx = document.getElementById('reportChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Quantity Sold',
                    backgroundColor: 'rgba(255, 206, 86, 0.5)',
                    borderColor: 'rgb(255, 206, 86)',
                    borderWidth: 1,
                    data: data.quantities,
                    yAxisID: 'y'
                },
                {
                    label: 'Revenue',
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1,
                    data: data.revenues,
                    type: 'line',
                    yAxisID: 'y1'
                },
                {
                    label: 'Profit',
                    backgroundColor: 'rgba(153, 102, 255, 0.5)',
                    borderColor: 'rgb(153, 102, 255)',
                    borderWidth: 1,
                    data: data.profits,
                    type: 'line',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Top Selling Medicines'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Medicine'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Quantity Sold'
                    },
                    beginAtZero: true
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    },
                    beginAtZero: true,
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + value;
                        }
                    }
                }
            }
        }
    });
}

// Render staff performance chart
function renderStaffChart(data) {
    const ctx = document.getElementById('reportChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Activities',
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1,
                    data: data.activities
                },
                {
                    label: 'Check-ins',
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 1,
                    data: data.check_ins
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Staff Performance Metrics' }
            },
            scales: {
                x: { title: { display: true, text: 'Staff Member' } },
                y: { beginAtZero: true, title: { display: true, text: 'Count' } }
            }
        }
    });
}

// Render medicine analysis chart
function renderMedicineChart(data) {
    const ctx = document.getElementById('reportChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.quantities,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)',
                    'rgba(255, 159, 64, 0.8)',
                    'rgba(199, 199, 199, 0.8)',
                    'rgba(83, 102, 255, 0.8)',
                    'rgba(255, 205, 86, 0.8)',
                    'rgba(54, 162, 235, 0.8)'
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'right' },
                title: { display: true, text: 'Top Selling Medicines' }
            }
        }
    });
}

// Render financial summary chart
function renderFinancialChart(data) {
    const ctx = document.getElementById('reportChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Daily Revenue',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgb(75, 192, 192)',
                borderWidth: 2,
                tension: 0.1,
                data: data.revenue
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Daily Revenue Trend' }
            },
            scales: {
                x: { title: { display: true, text: 'Date' } },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Revenue ($)' },
                    ticks: { callback: function(value) { return '$' + value; } }
                }
            }
        }
    });
}

// Render trends analysis chart
function renderTrendsChart(data) {
    const ctx = document.getElementById('reportChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Revenue',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 2,
                    tension: 0.1,
                    data: data.revenue
                },
                {
                    label: 'Patients',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    borderColor: 'rgb(255, 99, 132)',
                    borderWidth: 2,
                    tension: 0.1,
                    data: data.patients,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Monthly Trends' }
            },
            scales: {
                x: { title: { display: true, text: 'Month' } },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Revenue ($)' },
                    beginAtZero: true,
                    ticks: { callback: function(value) { return '$' + value; } }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Patient Count' },
                    beginAtZero: true,
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// Render comparative analysis chart
function renderComparativeChart(data) {
    const ctx = document.getElementById('reportChart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'Revenue',
                    backgroundColor: ['rgba(75, 192, 192, 0.5)', 'rgba(54, 162, 235, 0.5)'],
                    borderColor: ['rgb(75, 192, 192)', 'rgb(54, 162, 235)'],
                    borderWidth: 1,
                    data: data.revenue
                },
                {
                    label: 'Patients',
                    backgroundColor: ['rgba(255, 99, 132, 0.5)', 'rgba(255, 159, 64, 0.5)'],
                    borderColor: ['rgb(255, 99, 132)', 'rgb(255, 159, 64)'],
                    borderWidth: 1,
                    data: data.patients,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' },
                title: { display: true, text: 'Period Comparison' }
            },
            scales: {
                x: { title: { display: true, text: 'Period' } },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: { display: true, text: 'Revenue ($)' },
                    beginAtZero: true,
                    ticks: { callback: function(value) { return '$' + value; } }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: { display: true, text: 'Patient Count' },
                    beginAtZero: true,
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}
