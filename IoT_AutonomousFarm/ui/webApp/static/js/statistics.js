document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");
  const greenhouseId = localStorage.getItem("greenhouse_id");
  
  // Get URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const areaId = urlParams.get('area_id');
  const sensorType = urlParams.get('sensor_type');

  if (!token || !greenhouseId || !areaId || !sensorType) {
    alert("Missing required information. Redirecting to sensors page.");
    window.location.href = "sensors.html";
    return;
  }

  let sensorChart;
  let thingSpeakConfig = null;
  let updateInterval = null;

  // Initialize chart
  function initChart(sensorType, unit = '') {
    const ctx = document.getElementById('sensorChart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (sensorChart) {
      sensorChart.destroy();
    }

    sensorChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: `${sensorType} (${unit})`,
          data: [],
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1,
          fill: false,
        }]
      },
      options: {
        width: 400,
        height: 400,
        responsive: true,
        animation: false,
        scales: {
          x: {
            type: 'time',
            time: {
              tooltipFormat: 'MMM DD, HH:mm:ss',
              displayFormats: {
                minute: 'HH:mm',
                hour: 'MMM DD HH:mm'
              }
            },
            title: {
              display: true,
              text: 'Time'
            }
          },
          y: {
            title: {
              display: true,
              text: `${sensorType} (${unit})`
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: `${sensorType} Data for Area ${areaId}`
          }
        }
      }
    });
  }

  // Fetch ThingSpeak configuration
  function fetchThingSpeakConfig() {
    return fetch("./json/WebApp_config.json")
      .then(res => res.json())
      .then(config => {
        const catalog_url = config.catalog_url;
        return fetch(`${catalog_url}/get_greenhouse_info?greenhouse_id=${greenhouseId}`, {
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          }
        });
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch greenhouse info');
        }
        return response.json();
      })
      .then(data => {
        if (data && data.thingSpeak_config) {
          thingSpeakConfig = data.thingSpeak_config;
          return thingSpeakConfig;
        } else {
          throw new Error('ThingSpeak configuration not found');
        }
      });
  }

  // Fetch data from ThingSpeak
  function fetchThingSpeakData(numResults = 100) {
    if (!thingSpeakConfig) {
      console.error('ThingSpeak configuration not available');
      return Promise.reject('ThingSpeak configuration not available');
    }

    const { channel_id, read_key } = thingSpeakConfig;
    const thingSpeakUrl = `https://api.thingspeak.com/channels/${channel_id}/feeds.json?api_key=${read_key}&results=${numResults}`;

    return fetch(thingSpeakUrl)
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch data from ThingSpeak');
        }
        return response.json();
      })
      .then(data => {
        return data.feeds || [];
      });
  }

  // Process ThingSpeak data based on sensor type
  function processThingSpeakData(feeds, sensorType, areaId) {
    const processedData = [];
    
    feeds.forEach(feed => {
      const timestamp = new Date(feed.created_at);
      let value = null;

      try {
        // Map sensor types to ThingSpeak field names
        let fieldData = null;
        
        switch(sensorType) {
          case 'Temperature':
            fieldData = JSON.parse(feed.field1 || '{}');
            console.log(fieldData);
            value = parseFloat(fieldData[areaId]);
            console.log(`Temperature for area ${areaId}: ${value}`);
            break;
          case 'Humidity':
            fieldData = JSON.parse(feed.field2 || '{}');
            value = parseFloat(fieldData[areaId]);
            break;
          case 'SoilMoisture':
            fieldData = JSON.parse(feed.field3 || '{}');
            value = parseFloat(fieldData[areaId]);
            break;
          case 'pH':
            fieldData = JSON.parse(feed.field4 || '{}');
            value = parseFloat(fieldData[areaId]);
            break;
          case 'LightIntensity':
            fieldData = JSON.parse(feed.field5 || '{}');
            value = parseFloat(fieldData[areaId]);
            break;
          case 'NPK':
            // For NPK, parse each component separately
            const nData = JSON.parse(feed.field6 || '{}');
            const pData = JSON.parse(feed.field7 || '{}');
            const kData = JSON.parse(feed.field8 || '{}');
            
            value = {
              N: parseFloat(nData[areaId]),
              P: parseFloat(pData[areaId]),
              K: parseFloat(kData[areaId])
            };
            break;
          default:
            fieldData = JSON.parse(feed.field1 || '{}');
            value = parseFloat(fieldData[areaId]);
        }

        // Validate the extracted value
        if (sensorType === 'NPK') {
          if (value && !isNaN(value.N) && !isNaN(value.P) && !isNaN(value.K)) {
            processedData.push({ timestamp, value });
          }
        } else {
          if (value !== null && !isNaN(value)) {
            processedData.push({ timestamp, value });
          }
        }
      } catch (error) {
        console.warn(`Failed to parse data for timestamp ${timestamp}:`, error);
      }
    });

    return processedData;
  }

  // Process ThingSpeak data for multiple areas
  function processThingSpeakDataForAllAreas(feeds, sensorType) {
    const areaData = {};
    
    feeds.forEach(feed => {
      const timestamp = new Date(feed.created_at);

      try {
        let fieldData = null;
        
        switch(sensorType) {
          case 'Temperature':
            fieldData = JSON.parse(feed.field1 || '{}');
            break;
          case 'Humidity':
            fieldData = JSON.parse(feed.field2 || '{}');
            break;
          case 'SoilMoisture':
            fieldData = JSON.parse(feed.field3 || '{}');
            break;
          case 'pH':
            fieldData = JSON.parse(feed.field4 || '{}');
            break;
          case 'LightIntensity':
            fieldData = JSON.parse(feed.field5 || '{}');
            break;
          case 'NPK':
            // Handle NPK separately if needed
            const nData = JSON.parse(feed.field6 || '{}');
            const pData = JSON.parse(feed.field7 || '{}');
            const kData = JSON.parse(feed.field8 || '{}');
            
            Object.keys(nData).forEach(area => {
              if (!areaData[area]) areaData[area] = [];
              const value = {
                N: parseFloat(nData[area]),
                P: parseFloat(pData[area]),
                K: parseFloat(kData[area])
              };
              if (!isNaN(value.N) && !isNaN(value.P) && !isNaN(value.K)) {
                areaData[area].push({ timestamp, value });
              }
            });
            return; // Skip the general processing for NPK
          default:
            fieldData = JSON.parse(feed.field1 || '{}');
        }

        // Process data for each area
        if (fieldData) {
          Object.keys(fieldData).forEach(area => {
            if (!areaData[area]) areaData[area] = [];
            const value = parseFloat(fieldData[area]);
            if (!isNaN(value)) {
              areaData[area].push({ timestamp, value });
            }
          });
        }
      } catch (error) {
        console.warn(`Failed to parse data for timestamp ${timestamp}:`, error);
      }
    });

    return areaData;
  }

  // Update chart with new data
  function updateChart(processedData, sensorType) {
    if (!sensorChart) return;

    sensorChart.data.labels = [];
    sensorChart.data.datasets[0].data = [];

    if (sensorType === 'NPK') {
      // For NPK sensor, create separate datasets for N, P, K
      sensorChart.data.datasets = [
        {
          label: 'Nitrogen (N)',
          data: [],
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.1,
          fill: false,
        },
        {
          label: 'Phosphorus (P)',
          data: [],
          borderColor: 'rgb(54, 162, 235)',
          backgroundColor: 'rgba(54, 162, 235, 0.2)',
          tension: 0.1,
          fill: false,
        },
        {
          label: 'Potassium (K)',
          data: [],
          borderColor: 'rgb(255, 205, 86)',
          backgroundColor: 'rgba(255, 205, 86, 0.2)',
          tension: 0.1,
          fill: false,
        }
      ];

      processedData.forEach(dataPoint => {
        sensorChart.data.labels.push(dataPoint.timestamp);
        sensorChart.data.datasets[0].data.push(dataPoint.value.N);
        sensorChart.data.datasets[1].data.push(dataPoint.value.P);
        sensorChart.data.datasets[2].data.push(dataPoint.value.K);
      });
    } else {
      processedData.forEach(dataPoint => {
        sensorChart.data.labels.push(dataPoint.timestamp);
        sensorChart.data.datasets[0].data.push(dataPoint.value);
      });
    }

    sensorChart.update();
  }

  // Update chart with multiple areas
  function updateChartMultipleAreas(areaData, sensorType) {
    if (!sensorChart) return;

    const colors = [
      'rgb(75, 192, 192)',
      'rgb(255, 99, 132)',
      'rgb(54, 162, 235)',
      'rgb(255, 205, 86)',
      'rgb(153, 102, 255)',
      'rgb(255, 159, 64)'
    ];

    sensorChart.data.labels = [];
    sensorChart.data.datasets = [];

    // Get all timestamps for consistent x-axis
    const allTimestamps = new Set();
    Object.values(areaData).forEach(data => {
      data.forEach(point => allTimestamps.add(point.timestamp.getTime()));
    });
    const sortedTimestamps = Array.from(allTimestamps).sort().map(t => new Date(t));
    sensorChart.data.labels = sortedTimestamps;

    // Create datasets for each area
    Object.keys(areaData).forEach((area, index) => {
      const color = colors[index % colors.length];
      const data = areaData[area];

      if (sensorType === 'NPK') {
        // Create separate datasets for N, P, K for each area
        ['N', 'P', 'K'].forEach((component, compIndex) => {
          const componentColor = colors[(index * 3 + compIndex) % colors.length];
          sensorChart.data.datasets.push({
            label: `Area ${area} - ${component}`,
            data: data.map(point => ({
              x: point.timestamp,
              y: point.value[component]
            })),
            borderColor: componentColor,
            backgroundColor: componentColor.replace('rgb', 'rgba').replace(')', ', 0.2)'),
            tension: 0.1,
            fill: false,
          });
        });
      } else {
        sensorChart.data.datasets.push({
          label: `Area ${area}`,
          data: data.map(point => ({
            x: point.timestamp,
            y: point.value
          })),
          borderColor: color,
          backgroundColor: color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
          tension: 0.1,
          fill: false,
        });
      }
    });

    sensorChart.update();
  }

  // Load and display data
  function loadSensorData(numResults = 100) {
    fetchThingSpeakData(numResults)
      .then(feeds => {
        const processedData = processThingSpeakData(feeds, sensorType, areaId);
        updateChart(processedData, sensorType);
      })
      .catch(error => {
        console.error('Error loading sensor data:', error);
        // Fall back to mock data if ThingSpeak fails
        loadMockData();
      });
  }

  // Mock data fallback
  function loadMockData() {
    const mockData = [];
    const now = new Date();
    
    for (let i = 100; i >= 0; i--) {
      const timestamp = new Date(now.getTime() - i * 60000); // 1 minute intervals
      let value;
      
      switch(sensorType) {
        case 'Temperature':
          value = 20 + Math.random() * 10; // 20-30°C
          break;
        case 'Humidity':
          value = 40 + Math.random() * 40; // 40-80%
          break;
        case 'SoilMoisture':
          value = 30 + Math.random() * 40; // 30-70%
          break;
        case 'pH':
          value = 6 + Math.random() * 2; // 6-8 pH
          break;
        case 'LightIntensity':
          value = Math.random() * 1000; // 0-1000 lux
          break;
        case 'NPK':
          value = {
            N: 300 + Math.random() * 400,
            P: 200 + Math.random() * 300,
            K: 250 + Math.random() * 350
          };
          break;
        default:
          value = Math.random() * 100;
      }
      
      mockData.push({ timestamp, value });
    }
    
    updateChart(mockData, sensorType);
  }

  // Initialize the page
  function init() {
    // Get sensor unit from catalog or use defaults
    const sensorUnits = {
      'Temperature': '°C',
      'Humidity': '%RH',
      'SoilMoisture': '%',
      'pH': 'pH',
      'LightIntensity': 'lux',
      'NPK': 'ppm'
    };
    
    const unit = sensorUnits[sensorType] || '';
    initChart(sensorType, unit);

    // Add controls for data range
    addDataControls();

    // Fetch configuration and load data
    fetchThingSpeakConfig()
      .then(() => {
        loadSensorData();
        // Set up auto-refresh every 30 seconds
        updateInterval = setInterval(() => loadSensorData(), 30000);
      })
      .catch(error => {
        console.error('Failed to fetch ThingSpeak config:', error);
        alert('Failed to load ThingSpeak configuration. Using mock data.');
        loadMockData();
      });
  }

  // Add controls for selecting data range
  function addDataControls() {
    const container = document.querySelector('.container');
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'mb-3 d-flex justify-content-center align-items-center';
    controlsDiv.innerHTML = `
      <div class="me-3">
        <label for="dataRange" class="form-label text-white">Number of data points:</label>
        <select id="dataRange" class="form-select" style="width: auto; display: inline-block;">
          <option value="50">Last 50</option>
          <option value="100" selected>Last 100</option>
          <option value="200">Last 200</option>
          <option value="500">Last 500</option>
        </select>
      </div>
      <button id="refreshData" class="btn btn-primary">Refresh Data</button>
    `;
    
    container.insertBefore(controlsDiv, container.firstChild);

    // Add event listeners
    document.getElementById('dataRange').addEventListener('change', (e) => {
      const numResults = parseInt(e.target.value);
      loadSensorData(numResults);
    });

    document.getElementById('refreshData').addEventListener('click', () => {
      const numResults = parseInt(document.getElementById('dataRange').value);
      loadSensorData(numResults);
    });
  }

  // Clean up on page unload
  window.addEventListener('beforeunload', () => {
    if (updateInterval) {
      clearInterval(updateInterval);
    }
  });

  // Start the application
  init();
});