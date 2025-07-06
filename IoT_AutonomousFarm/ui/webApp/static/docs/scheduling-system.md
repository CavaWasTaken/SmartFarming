# Scheduling System Documentation

## Overview
The scheduling system allows users to create, manage, and monitor automated events for their greenhouse devices. Users can schedule activities based on sensor readings and device parameters.

## Features

### 1. Event Management
- **Create Events**: Schedule new automation events with specific parameters
- **Edit Events**: Modify existing scheduled events
- **Delete Events**: Remove unwanted events
- **View Events**: See all scheduled and active events

### 2. Event Types
- **One-time Events**: Execute once at a specific time
- **Recurring Events**: Execute daily, weekly, or monthly
- **Sensor-based Events**: Trigger based on sensor readings

### 3. Event Parameters
- **Sensor Selection**: Choose from available greenhouse sensors
- **Parameter**: Specify the sensor parameter to monitor (e.g., temperature, humidity)
- **Target Value**: Set the desired value for the parameter
- **Execution Time**: Schedule when the event should trigger
- **Frequency**: Set how often the event should repeat

## User Interface

### Navigation
- Access scheduling from the **Devices** page using the "Manage Scheduling" button
- The scheduling link also appears in the navigation menu when a greenhouse is selected

### Event Display
- **Scheduled Events**: Shows future events waiting to be executed
- **Active Events**: Shows currently running events
- **Filter Options**: Filter by sensor type or event status

### Event Creation
1. Click "Add New Event" button
2. Select a sensor from the dropdown
3. Enter the parameter name (e.g., "temperature", "humidity")
4. Set the target value
5. Choose the frequency (once, daily, weekly, monthly)
6. Select execution date and time
7. Optionally add a description
8. Click "Save Event"

### Event Management
- **Edit**: Click the edit button on scheduled events to modify them
- **Delete**: Click the delete button to remove events (with confirmation)
- **Refresh**: Use the refresh button to update the event list

## API Integration

### Endpoints Used
- `GET /get_scheduled_events`: Retrieve all events for a greenhouse
- `POST /schedule_event`: Create a new scheduled event
- `DELETE /delete_event`: Remove an existing event
- `GET /get_sensors`: Get available sensors for the greenhouse
- `GET /get_devices`: Get available devices for the greenhouse

### Data Flow
1. **Load Events**: Fetch from catalog database via API
2. **Create Event**: Send event data to catalog for storage
3. **Delete Event**: Remove event from catalog database
4. **Real-time Updates**: Refresh event list after modifications

## Database Schema

### Events Table (scheduled_events)
- `event_id`: Unique identifier
- `greenhouse_id`: Associated greenhouse
- `frequency`: Event recurrence (once, daily, weekly, monthly)
- `sensor_id`: Target sensor
- `parameter`: Sensor parameter to monitor
- `execution_time`: When to execute the event
- `value`: Target value for the parameter

## Error Handling
- **Network Errors**: Display user-friendly error messages
- **Validation**: Form validation for required fields
- **Authentication**: Redirect to login if token is invalid
- **Permissions**: Check user access to greenhouse data

## Future Enhancements
- **Event History**: Track executed events and their results
- **Conditional Events**: Complex conditions with multiple sensors
- **Event Templates**: Predefined event configurations
- **Notifications**: Alert users when events are executed
- **Event Dependencies**: Chain events together
- **Advanced Scheduling**: More complex time patterns

## Usage Tips
1. Always verify sensor readings before scheduling events
2. Use descriptive parameter names for better organization
3. Test with one-time events before setting up recurring ones
4. Monitor active events to ensure they're working correctly
5. Use the filter options to organize large numbers of events

## Troubleshooting

### Common Issues
- **Events not appearing**: Check network connection and refresh
- **Cannot create event**: Verify all required fields are filled
- **Unauthorized error**: Ensure you're logged in and have greenhouse access
- **Event not executing**: Check device connectivity and sensor availability

### Error Messages
- "Missing required information": URL parameters are missing
- "Failed to fetch events": Network or API error
- "Device not found": Selected device is not available
- "Event not inserted": Database error during creation
