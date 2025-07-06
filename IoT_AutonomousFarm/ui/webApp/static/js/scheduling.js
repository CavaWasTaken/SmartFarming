document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");
  const userId = localStorage.getItem("user_id");
  const urlParams = new URLSearchParams(window.location.search);
  const greenhouseId = urlParams.get('greenhouse_id');

  if (!token || !userId || !greenhouseId) {
    alert("You are not logged in or no greenhouse selected. Redirecting...");
    window.location.href = "loginform.html";
    return;
  }

  let catalogUrl = '';
  let allEvents = [];
  let sensors = [];
  let devices = [];
  let eventToDelete = null;

  // Initialize the page
  async function init() {
    try {
      await loadConfig();
      await loadSensors();
      await loadDevices();
      await loadEvents();
      setupEventListeners();
      populateSensorFilter();
      
      // Set up periodic refresh to check for events deleted by the system
      setInterval(async () => {
        try {
          await loadEvents();
        } catch (error) {
          console.error('Error in periodic refresh:', error);
        }
      }, 30000); // Refresh every 30 seconds
      
    } catch (error) {
      console.error('Error initializing page:', error);
      showError('Failed to load page data');
    }
  }

  // Load configuration
  async function loadConfig() {
    const response = await fetch('./json/WebApp_config.json');
    const config = await response.json();
    catalogUrl = config.catalog_url;
  }

  // Load sensors from catalog
  async function loadSensors() {
    try {
      const response = await fetch(`${catalogUrl}/get_sensors?greenhouse_id=${greenhouseId}&device_name=WebApp`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch sensors');
      }

      const data = await response.json();
      sensors = data.sensors || [];
      console.log('Sensors loaded:', sensors);
      
      // Populate sensor dropdowns
      populateSensorDropdowns();
    } catch (error) {
      console.error('Error loading sensors:', error);
      showError('Failed to load sensors');
    }
  }

  // Load devices from catalog
  async function loadDevices() {
    try {
      const response = await fetch(`${catalogUrl}/get_devices?greenhouse_id=${greenhouseId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch devices');
      }

      const data = await response.json();
      devices = data.devices || [];
    } catch (error) {
      console.error('Error loading devices:', error);
      showError('Failed to load devices');
    }
  }

  // Load scheduled events from catalog
  async function loadEvents() {
    try {
      showLoadingSpinner();
      
      // We need to get events for all devices in the greenhouse
      // For now, we'll use the first device as a placeholder
      // In a real implementation, you might want to modify the API to get all events for a greenhouse
      if (devices.length === 0) {
        hideLoadingSpinner();
        return;
      }

      const device = devices[0]; // Use first device as placeholder
      const response = await fetch(`${catalogUrl}/get_scheduled_events?device_id=${device.device_id}&device_name=${device.name}&greenhouse_id=${greenhouseId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch events');
      }

      const data = await response.json();
      allEvents = data.events || [];
      
      displayEvents();
      hideLoadingSpinner();
    } catch (error) {
      console.error('Error loading events:', error);
      showError('Failed to load events');
      hideLoadingSpinner();
    }
  }

  // Populate sensor dropdowns
  async function populateSensorDropdowns() {
    const sensorSelect = document.getElementById('sensorSelect');
    const sensorFilter = document.getElementById('sensorFilter');
    
    // Clear existing options
    sensorSelect.innerHTML = '<option value="">Select a sensor</option>';

    for (const sensor of sensors) {
      let areaName = '';
      if (sensor.area_id) {
        try {
          // Synchronously fetch area info (not recommended for large lists, but fine for dropdowns)
          // If you want to optimize, consider prefetching all areas in loadSensors
            const areaResponse = await fetch(`${catalogUrl}/get_area_info?area_id=${sensor.area_id}&greenhouse_id=${greenhouseId}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
            });
          if (areaResponse.ok) {
            const areaData = await areaResponse.json();
            areaName = areaData.name;
          } else {
            areaName = sensor.area_id;
          }
        } catch (err) {
          areaName = sensor.area_id;
        }
      }
      const option = document.createElement('option');
      option.value = sensor.sensor_id;
      // Add area info if available
      const areaText = areaName ? `${areaName}` : (sensor.area_id ? `${sensor.area_id}` : '');
      option.textContent = `${sensor.name} (${sensor.type} - ${areaText})`;
      option.dataset.type = sensor.type;
      option.dataset.unit = sensor.unit;
      option.dataset.area = sensor.area_id || '';
      sensorSelect.appendChild(option);
    }

    // Update sensor filter
    sensorFilter.innerHTML = '<option value="all">All Sensors</option>';
    const sensorTypes = [...new Set(sensors.map(s => s.type))];
    sensorTypes.forEach(type => {
      const option = document.createElement('option');
      option.value = type;
      option.textContent = type;
      sensorFilter.appendChild(option);
    });
  }

  // Display events in their respective sections
  function displayEvents() {
    const scheduledContainer = document.getElementById('scheduledEvents');
    
    // Clear existing events
    scheduledContainer.innerHTML = '';

    if (allEvents.length === 0) {
      showEmptyState(scheduledContainer, 'No scheduled events', 'Create your first automation event using the "Add New Event" button.');
      return;
    }

    // Filter events
    const filteredEvents = filterEvents();
    
    // Display scheduled events
    if (filteredEvents.length === 0) {
      showEmptyState(scheduledContainer, 'No events match your filters', 'Try adjusting your filter criteria.');
    } else {
      filteredEvents.forEach(event => {
        scheduledContainer.appendChild(createEventCard(event, 'scheduled'));
      });
    }
  }

  // Create event card HTML
  function createEventCard(event, status) {
    const card = document.createElement('div');
    card.className = 'event-card';
    card.dataset.eventId = event.event_id;

    const sensor = sensors.find(s => s.sensor_id == event.sensor_id);
    const sensorName = sensor ? sensor.name : 'Unknown Sensor';
    const sensorType = sensor ? sensor.type : 'Unknown';
    const unit = sensor ? sensor.unit : '';

    const executionTime = new Date(event.execution_time);
    
    // Ensure we're displaying the correct local time
    const formattedDate = executionTime.toLocaleDateString('en-CA'); // YYYY-MM-DD format
    const formattedTime = executionTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });

    card.innerHTML = `
      <div class="event-header">
        <h6 class="event-title">${sensorName} - ${event.parameter}</h6>
        <span class="event-status status-${status}">${status}</span>
      </div>
      
      <div class="event-details">
        <div class="event-detail">
          <strong>Sensor:</strong> ${sensorType}
        </div>
        <div class="event-detail">
          <strong>Target Value:</strong> ${event.value} ${unit}
        </div>
        <div class="event-detail">
          <strong>Frequency:</strong> 
          <span class="frequency-badge">${event.frequency}</span>
        </div>
        <div class="time-info">
          <div class="event-detail">
            <strong>Date:</strong> ${formattedDate}
          </div>
          <div class="event-detail">
            <strong>Time:</strong> ${formattedTime}
          </div>
        </div>
      </div>

      <div class="event-actions">
        ${status === 'scheduled' ? `
          <button class="btn btn-warning btn-sm-custom edit-event-btn" data-event-id="${event.event_id}">
            <i class="fas fa-edit"></i> Edit
          </button>
        ` : ''}
        <button class="btn btn-danger btn-sm-custom delete-event-btn" data-event-id="${event.event_id}">
          <i class="fas fa-trash"></i> Delete
        </button>
      </div>
    `;

    return card;
  }

  // Show empty state
  function showEmptyState(container, title, message) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-calendar-times"></i>
        <h5>${title}</h5>
        <p>${message}</p>
      </div>
    `;
  }

  // Check if event is currently active
  // Filter events based on current filters
  function filterEvents() {
    const statusFilter = document.getElementById('statusFilter').value;
    const sensorFilter = document.getElementById('sensorFilter').value;
    
    return allEvents.filter(event => {
      // Filter by sensor type
      if (sensorFilter !== 'all') {
        const sensor = sensors.find(s => s.sensor_id == event.sensor_id);
        if (!sensor || sensor.type !== sensorFilter) {
          return false;
        }
      }
      
      // Filter by status (simplified - just checking if event time has passed)
      if (statusFilter === 'scheduled') {
        const now = new Date();
        const executionTime = new Date(event.execution_time);
        return executionTime > now;
      }
      
      return true;
    });
  }

  // Setup event listeners
  function setupEventListeners() {

    // Add event button
    document.getElementById('addEventBtn').addEventListener('click', () => {
      resetEventForm();
      setupParameterDropdown();
      setupFrequencyDropdown();
      document.getElementById('eventModalLabel').textContent = 'Add New Event';
      const modal = new bootstrap.Modal(document.getElementById('eventModal'));
      modal.show();
    });

    // Sensor selection change handler
    document.getElementById('sensorSelect').addEventListener('change', function() {
      const selectedOption = this.options[this.selectedIndex];
      if (selectedOption.dataset.type) {
        updateParameterField(selectedOption.dataset.type);
      } else {
        // Clear parameter field if no sensor selected
        const parameterInput = document.getElementById('parameterInput');
        if (parameterInput.tagName.toLowerCase() === 'select') {
          parameterInput.innerHTML = '<option value="">Select a sensor first</option>';
          parameterInput.className = 'form-control parameter-input parameter-select';
        } else {
          parameterInput.value = '';
          parameterInput.className = 'form-control parameter-input';
        }
        parameterInput.disabled = true;
      }
    });

    // Refresh button
    document.getElementById('refreshBtn').addEventListener('click', loadEvents);

    // Filter change handlers
    document.getElementById('statusFilter').addEventListener('change', displayEvents);
    document.getElementById('sensorFilter').addEventListener('change', displayEvents);

    // Save event button
    document.getElementById('saveEventBtn').addEventListener('click', handleSaveEvent);

    // Confirm delete button
    document.getElementById('confirmDeleteBtn').addEventListener('click', handleDeleteEvent);

    // Event delegation for edit and delete buttons
    document.addEventListener('click', (e) => {
      if (e.target.closest('.edit-event-btn')) {
        const eventId = e.target.closest('.edit-event-btn').dataset.eventId;
        handleEditEvent(eventId);
      } else if (e.target.closest('.delete-event-btn')) {
        const eventId = e.target.closest('.delete-event-btn').dataset.eventId;
        showDeleteConfirmation(eventId);
      }
    });

    // Set minimum date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('executionDate').min = today;

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }

  // Handle saving an event
  async function handleSaveEvent() {
    const form = document.getElementById('eventForm');
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    // Validate parameter values against database constraints
    const validParameters = ['Temperature', 'Humidity', 'SoilMoisture', 'pH', 'Nitrogen', 'Phosphorus', 'Potassium', 'LightIntensity'];
    const validFrequencies = ['Once', 'Daily', 'Weekly', 'Monthly'];
    
    const parameter = document.getElementById('parameterInput').value;
    const frequency = document.getElementById('frequencySelect').value;
    
    if (!validParameters.includes(parameter)) {
      showError(`Invalid parameter: ${parameter}. Must be one of: ${validParameters.join(', ')}`);
      return;
    }
    
    if (!validFrequencies.includes(frequency)) {
      showError(`Invalid frequency: ${frequency}. Must be one of: ${validFrequencies.join(', ')}`);
      return;
    }

    const formData = {
      greenhouse_id: parseInt(greenhouseId),
      device_id: devices[0]?.device_id, // Use first device as placeholder
      sensor_id: parseInt(document.getElementById('sensorSelect').value),
      parameter: parameter,
      desired_value: parseFloat(document.getElementById('valueInput').value),
      frequency: frequency,
      execution_time: formatDateTimeForDB(document.getElementById('executionDate').value, document.getElementById('executionTime').value)
    };

    try {
      const response = await fetch(`${catalogUrl}/schedule_event`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to save event');
      }

      const newEvent = await response.json();
      
      // Close modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('eventModal'));
      modal.hide();
      
      // Reload events
      await loadEvents();
      
      showSuccess('Event scheduled successfully!');
    } catch (error) {
      console.error('Error saving event:', error);
      showError(error.message || 'Failed to save event');
    }
  }

  // Handle editing an event
  function handleEditEvent(eventId) {
    const event = allEvents.find(e => e.event_id == eventId);
    if (!event) return;

    // Setup dropdowns first
    setupParameterDropdown();
    setupFrequencyDropdown();

    // Populate form with event data
    document.getElementById('sensorSelect').value = event.sensor_id;
    
    // Find the sensor to get its type
    const sensor = sensors.find(s => s.sensor_id == event.sensor_id);
    if (sensor) {
      updateParameterField(sensor.type);
      // Set the parameter value after updating the field
      setTimeout(() => {
        document.getElementById('parameterInput').value = event.parameter;
      }, 0);
    }
    
    document.getElementById('valueInput').value = event.value;
    document.getElementById('frequencySelect').value = event.frequency;
    
    // Use helper function to parse date/time consistently
    const { date, time } = parseDateTimeFromDB(event.execution_time);
    document.getElementById('executionDate').value = date;
    document.getElementById('executionTime').value = time;

    document.getElementById('eventModalLabel').textContent = 'Edit Event';
    const modal = new bootstrap.Modal(document.getElementById('eventModal'));
    modal.show();
  }

  // Show delete confirmation
  function showDeleteConfirmation(eventId) {
    eventToDelete = eventId;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
  }

  // Handle deleting an event
  async function handleDeleteEvent() {
    if (!eventToDelete) return;

    try {
      const deviceId = devices[0]?.device_id; // Use first device as placeholder
      const response = await fetch(`${catalogUrl}/delete_event?device_id=${deviceId}&event_id=${eventToDelete}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to delete event');
      }

      // Close modal
      const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
      modal.hide();
      
      // Reload events
      await loadEvents();
      
      showSuccess('Event deleted successfully!');
      eventToDelete = null;
    } catch (error) {
      console.error('Error deleting event:', error);
      showError(error.message || 'Failed to delete event');
    }
  }

  // Update parameter field based on sensor type
  function updateParameterField(sensorType) {
    const parameterContainer = document.getElementById('parameterInput').parentNode;
    const oldField = document.getElementById('parameterInput');
    
    // Remove old field
    oldField.remove();
    
    if (sensorType === 'NPK') {
      // Create select dropdown for NPK nutrients
      const select = document.createElement('select');
      select.id = 'parameterInput';
      select.className = 'form-control parameter-input npk-select newly-created';
      select.required = true;
      
      // Add options for NPK nutrients  
      const nutrients = [
        { value: '', text: 'Select nutrient' },
        { value: 'Nitrogen', text: 'Nitrogen (N)' },
        { value: 'Phosphorus', text: 'Phosphorus (P)' },
        { value: 'Potassium', text: 'Potassium (K)' }
      ];
      
      nutrients.forEach(nutrient => {
        const option = document.createElement('option');
        option.value = nutrient.value;
        option.textContent = nutrient.text;
        select.appendChild(option);
      });
      
      parameterContainer.appendChild(select);
      
      // Remove the newly-created class after animation
      setTimeout(() => {
        select.classList.remove('newly-created');
      }, 2000);
    } else {
      // Create readonly input for other sensor types
      const input = document.createElement('input');
      input.type = 'text';
      input.id = 'parameterInput';
      input.className = 'form-control parameter-input readonly-parameter newly-created';
      input.value = sensorType;
      input.readOnly = true;
      input.required = true;
      
      parameterContainer.appendChild(input);
      
      // Remove the newly-created class after animation
      setTimeout(() => {
        input.classList.remove('newly-created');
      }, 2000);
    }
  }

  // Setup parameter dropdown with valid database values
  function setupParameterDropdown() {
    const parameterInput = document.getElementById('parameterInput');
    
    // Reset to default disabled state
    if (parameterInput.tagName.toLowerCase() === 'select') {
      parameterInput.innerHTML = '<option value="">Select a sensor first</option>';
      parameterInput.className = 'form-control parameter-input parameter-select';
    } else {
      parameterInput.value = '';
      parameterInput.className = 'form-control parameter-input';
    }
    parameterInput.disabled = true;
  }

  // Setup frequency dropdown with valid database values
  function setupFrequencyDropdown() {
    const frequencySelect = document.getElementById('frequencySelect');
    frequencySelect.innerHTML = '<option value="">Select frequency</option>';
    const validFrequencies = ['Once', 'Daily', 'Weekly', 'Monthly'];
    
    validFrequencies.forEach(freq => {
      const option = document.createElement('option');
      option.value = freq;
      option.textContent = freq;
      frequencySelect.appendChild(option);
    });
  }

  // Reset event form
  function resetEventForm() {
    document.getElementById('eventForm').reset();
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('executionDate').value = today;
    
    // Reset parameter field to disabled state
    const parameterInput = document.getElementById('parameterInput');
    if (parameterInput.tagName.toLowerCase() === 'select') {
      parameterInput.innerHTML = '<option value="">Select a sensor first</option>';
      parameterInput.className = 'form-control parameter-input parameter-select';
    } else {
      parameterInput.value = '';
      parameterInput.className = 'form-control parameter-input';
    }
    parameterInput.disabled = true;
  }

  // Show loading spinner
  function showLoadingSpinner() {
    const container = document.getElementById('scheduledEvents');
    
    container.innerHTML = `
      <div class="loading-spinner">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    `;
  }

  // Hide loading spinner
  function hideLoadingSpinner() {
    // This will be handled by displayEvents()
  }

  // Show success message
  function showSuccess(message) {
    showToast(message, 'success');
  }

  // Show error message
  function showError(message) {
    showToast(message, 'error');
  }

  // Show toast notification
  function showToast(message, type = 'info') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast-notification');
    existingToasts.forEach(toast => toast.remove());

    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
      <div class="toast-content">
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
      </div>
    `;

    document.body.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 100);

    // Auto remove after 5 seconds
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  }

  // Populate sensor filter dropdown
  function populateSensorFilter() {
    const sensorFilter = document.getElementById('sensorFilter');
    sensorFilter.innerHTML = '<option value="all">All Sensors</option>';
    
    const sensorTypes = [...new Set(sensors.map(s => s.type))];
    sensorTypes.forEach(type => {
      const option = document.createElement('option');
      option.value = type;
      option.textContent = type;
      sensorFilter.appendChild(option);
    });
  }

  // Helper function to format date and time for database storage
  function formatDateTimeForDB(dateStr, timeStr) {
    // Simply concatenate date and time without timezone conversion
    const formattedDateTime = `${dateStr} ${timeStr}:00`;
    
    console.log('Date formatting debug:', {
      inputDate: dateStr,
      inputTime: timeStr,
      formattedForDB: formattedDateTime
    });
    
    return formattedDateTime;
  }

  // Helper function to parse database timestamp for form display
  function parseDateTimeFromDB(timestampStr) {
    // Parse the timestamp string from database (should be in ISO format)
    const dateTime = new Date(timestampStr);
    
    // Get local date components (this automatically handles timezone conversion)
    const year = dateTime.getFullYear();
    const month = String(dateTime.getMonth() + 1).padStart(2, '0');
    const day = String(dateTime.getDate()).padStart(2, '0');
    const hours = String(dateTime.getHours()).padStart(2, '0');
    const minutes = String(dateTime.getMinutes()).padStart(2, '0');
    
    const dateStr = `${year}-${month}-${day}`;
    const timeStr = `${hours}:${minutes}`;
    
    console.log('Date parsing debug:', {
      inputTimestamp: timestampStr,
      dateTimeObject: dateTime.toString(),
      parsedDate: dateStr,
      parsedTime: timeStr,
      timezoneOffset: dateTime.getTimezoneOffset()
    });
    
    return { date: dateStr, time: timeStr };
  }

  // Load configuration
  init();
});
