const ctx = document.getElementById('sensorChart').getContext('2d');

const sensorChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [], // timestamps
    datasets: [{
      label: 'Temperature (°C)',  // You can make this dynamic per sensor type
      data: [],
      borderColor: 'rgb(75, 192, 192)',
      tension: 0.1,
      fill: false,
    }]
  },
  options: {
    responsive: true,
    animation: false,
    scales: {
      x: {
        type: 'time',
        time: {
          tooltipFormat: 'HH:mm:ss',
          unit: 'second'
        },
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Temperature (°C)'
        },
        suggetdedMin: 15,
        suggestedMax: 30,
      }
    }
  }
});

// Simulate mock data every 2 seconds
setInterval(() => {
    const now = new Date();
    const mockValue = 20 + Math.random() * 5; // Temperature between 20-25°C

    sensorChart.data.labels.push(now);
    sensorChart.data.datasets[0].data.push(mockValue);

    if (sensorChart.data.labels.length > 20) {
      sensorChart.data.labels.shift();
      sensorChart.data.datasets[0].data.shift();
    }

    sensorChart.update();
  }, 2000);
  
