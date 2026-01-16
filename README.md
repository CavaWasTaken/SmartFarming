# Smart Farming IoT System

## Project Overview

This project implements a comprehensive **IoT-based Smart Farming system** for autonomous greenhouse management. The system monitors environmental parameters (temperature, humidity, light, soil moisture, pH, NPK nutrients) and automatically controls greenhouse conditions to optimize plant growth. It features real-time monitoring, automated management microservices, data analytics, and multiple user interfaces (Web App and Telegram Bot).

The architecture follows a **microservices design pattern**, where each component operates independently and communicates through MQTT message broker and REST APIs. The system is fully containerized using Docker for easy deployment and scalability.

## Key Features

- **Real-time sensor monitoring**: Continuous collection of environmental data from multiple sensors
- **Automated management**: Intelligent microservices that automatically adjust greenhouse conditions
- **Predictive analytics**: Linear regression models to predict future trends and optimize resource usage
- **Multi-greenhouse support**: Manage multiple greenhouses with different cultivation areas
- **Dual user interface**: Web dashboard and Telegram bot for remote monitoring and control
- **Data persistence**: PostgreSQL database for storing historical data and configurations
- **External integration**: ThingSpeak adaptor for cloud-based data visualization
- **Scheduling system**: Time-based automation for irrigation, lighting, and other operations

## System Architecture

The system consists of the following components:

### Core Services

1. **Catalog Service** (`catalog/`)
   - Central REST API service (CherryPy) exposed on port `8080`
   - Manages all system resources: greenhouses, areas, sensors, plants, users, schedules
   - Authentication and authorization using JWT tokens
   - PostgreSQL database interface for data persistence
   - Coordinates communication between all other services

2. **PostgreSQL Database** (`db/`)
   - Stores all system data: user accounts, greenhouse configurations, sensor readings, plant information, schedules
   - Initialized with schema from `backup.sql`
   - Exposed on port `5433` (mapped from container's `5432`)

3. **MQTT Broker - Eclipse Mosquitto** (`mosquitto/`)
   - Message broker for IoT communication
   - Handles pub/sub messaging between sensors and management services
   - Exposed on ports `1883` (MQTT) and `9001` (WebSocket)

### IoT Components

4. **Device Connector** (`deviceConnector/`)
   - Simulates and manages IoT sensors (Temperature, Humidity, Light, Soil Moisture, pH, NPK)
   - Publishes sensor readings to MQTT topics
   - Receives and executes control actions from management services
   - Topic pattern: `greenhouse_{id}/area_{id}/sensor_{id}/{parameter}`

### Management Microservices

5. **Data Analysis Service** (`microservices/DataAnalysis/`)
   - Analyzes sensor data trends using statistical methods
   - Implements linear regression for predictive analytics
   - Detects anomalies and critical thresholds
   - Triggers alerts and automatic interventions

6. **Humidity Management** (`microservices/HumidityManagement/`)
   - Monitors humidity levels
   - Automatically activates/deactivates humidifiers and ventilation
   - Maintains optimal humidity ranges for plant growth

7. **Light Management** (`microservices/LightManagement/`)
   - Controls artificial lighting systems
   - Adjusts light intensity based on plant requirements and time of day
   - Integrates with scheduling system for automated day/night cycles

8. **Nutrient Management** (`microservices/NutrientManagement/`)
   - Monitors NPK (Nitrogen, Phosphorus, Potassium) levels
   - Controls fertilizer dispensing systems
   - Maintains optimal nutrient balance for different plant types

9. **Time Shift Service** (`microservices/TimeShift/`)
   - Manages scheduled operations and time-based automation
   - Coordinates irrigation cycles, lighting schedules, and maintenance tasks
   - Implements event-driven architecture for scheduled actions

### External Integrations

10. **ThingSpeak Adaptor** (`thingSpeakAdaptor/`)
    - Bridges local system with ThingSpeak cloud platform
    - Forwards sensor data to ThingSpeak channels for external visualization
    - Enables remote monitoring and data sharing

### User Interfaces

11. **Telegram Bot** (`ui/telegramBot/`)
    - Conversational interface for mobile monitoring
    - Receive alerts and notifications
    - Query sensor status and greenhouse conditions
    - Execute basic control commands remotely

12. **Web Application** (`ui/webApp/`)
    - Full-featured dashboard (NGINX + static web app)
    - Visualize real-time sensor data with charts and graphs
    - Manage greenhouses, areas, sensors, and plants
    - Configure schedules and automation rules
    - User authentication and profile management
    - Exposed on port `8000`

## Project Structure

```
SmartFarming/
├── IoT_AutonomousFarm/           # Main application directory
│   ├── catalog/                   # Central REST API service
│   │   ├── Catalog.py            # Main catalog service code
│   │   ├── Catalog_config.json   # Configuration (SECRET_KEY, Telegram token)
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── db/                        # Database initialization
│   │   ├── backup.sql            # Initial database schema and data
│   │   └── installDB.txt         # Database setup instructions
│   │
│   ├── mosquitto/                 # MQTT broker configuration
│   │   ├── config/               # Mosquitto configuration files
│   │   ├── data/                 # Persistent MQTT data
│   │   └── log/                  # Broker logs
│   │
│   ├── deviceConnector/           # IoT sensor simulator
│   │   ├── DeviceConnector.py    # Main device connector logic
│   │   ├── MqttClient.py         # MQTT client wrapper
│   │   ├── DeviceConnector_config.json
│   │   ├── sensors/              # Sensor class implementations
│   │   │   ├── Temperature.py
│   │   │   ├── Humidity.py
│   │   │   ├── Light.py
│   │   │   ├── SoilMoisture.py
│   │   │   ├── pH.py
│   │   │   └── NPK.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── microservices/             # Management microservices
│   │   ├── DataAnalysis/         # Analytics and prediction
│   │   │   ├── DataAnalysis.py
│   │   │   ├── DataAnalysis_config.json
│   │   │   ├── MqttClient.py
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── HumidityManagement/   # Humidity control
│   │   │   ├── HumidityManagement.py
│   │   │   ├── Management.py     # Base management class
│   │   │   ├── MqttClient.py
│   │   │   ├── HumidityManagement_config.json
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   ├── LightManagement/      # Light control
│   │   ├── NutrientManagement/   # Nutrient control
│   │   └── TimeShift/            # Scheduling service
│   │
│   ├── thingSpeakAdaptor/        # ThingSpeak integration
│   │   ├── ThingSpeakAdaptor.py
│   │   ├── ThingSpeakAdaptor_config.json
│   │   ├── MqttClient.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── ui/                        # User interfaces
│   │   ├── telegramBot/          # Telegram bot interface
│   │   │   ├── TelegramBot.py
│   │   │   ├── TelegramBot_config.json
│   │   │   ├── Dockerfile
│   │   │   └── requirements.txt
│   │   │
│   │   └── webApp/               # Web dashboard
│   │       ├── static/           # HTML, CSS, JS files
│   │       │   ├── home.html
│   │       │   ├── greenhouses.html
│   │       │   ├── sensors.html
│   │       │   ├── css/
│   │       │   ├── js/
│   │       │   └── json/WebApp_config.json
│   │       ├── nginx/
│   │       │   └── default.conf
│   │       └── Dockerfile
│   │
│   ├── docker-compose.yml         # Main Docker orchestration
│   ├── docker-compose-company-server.yml  # Company server deployment
│   └── docker-compose-customer.yml        # Customer deployment
│
├── Lab4/                          # Laboratory exercises
├── Testing/                       # Hardware testing scripts
├── .gitignore
└── README.md                      # This file
```

## System Logic and Communication Flow

### 1. Initialization Flow
1. PostgreSQL database starts and initializes schema from `backup.sql`
2. MQTT broker (Mosquitto) starts and waits for connections
3. Catalog service starts and connects to the database
4. All other services register with the Catalog and subscribe to MQTT topics

### 2. Sensor Data Flow
1. **Device Connector** simulates sensor readings (or interfaces with real hardware)
2. Sensor data is published to MQTT topics: `greenhouse_{id}/area_{id}/sensor_{id}/{parameter}`
3. **Management Microservices** subscribe to relevant sensor topics
4. **Data Analysis** processes the data and stores it in PostgreSQL via Catalog REST API
5. **ThingSpeak Adaptor** forwards data to cloud for external visualization
6. **Web App** and **Telegram Bot** fetch data from Catalog API for user display

### 3. Automated Control Flow
1. **Management Services** continuously monitor sensor data
2. When thresholds are exceeded:
   - Service calculates required action (increase/decrease)
   - Publishes action message to MQTT: `greenhouse_{id}/area_{id}/action/sensor_{id}`
3. **Device Connector** receives action and simulates actuator response
4. Sensor adjusts its reading simulation accordingly
5. New readings are published, closing the control loop

### 4. User Interaction Flow
- **Web App**: Users log in → JWT authentication → View dashboards → Send commands → Catalog → MQTT → Device Connector
- **Telegram Bot**: Users authenticate → Query status → Bot queries Catalog API → Returns formatted data

### 5. Scheduling Flow
1. Users create schedules via Web App (stored in database)
2. **Time Shift Service** periodically checks for scheduled events
3. When event time arrives, publishes action messages to MQTT
4. Corresponding actuators execute the scheduled action

## How to Run

### Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 1.29+)
- At least **4GB RAM** and **10GB disk space**
- Ports `1883`, `5433`, `8000`, `8080`, `9001` must be available

### Quick Start

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd /path/to/SmartFarming/IoT_AutonomousFarm
   ```

2. **Configure secrets** (optional):
   - Edit `catalog/Catalog_config.json` to set your own `SECRET_KEY` and Telegram `telegram_token`
   - Update database credentials in `docker-compose.yml` if needed (default: user=`iotproject`, password=`WeWillDieForIoT`)

3. **Start the entire system**:
   ```bash
   docker-compose up --build
   ```
   
   This command will:
   - Build all Docker images (first run takes 5-10 minutes)
   - Start all services in dependency order
   - Display logs from all containers

4. **Wait for services to initialize**:
   - Watch the logs until you see messages like "Catalog service started" and "MQTT client connected"
   - The database initialization may take 30-60 seconds

5. **Access the interfaces**:
   - **Web Application**: Open browser to `http://localhost:8000`
   - **Catalog REST API**: `http://localhost:8080`
   - **MQTT Broker**: Connect clients to `localhost:1883`
   - **PostgreSQL**: Connect to `localhost:5433` (credentials in docker-compose.yml)

### Running in Detached Mode

To run in background without blocking terminal:
```bash
docker-compose up -d --build
```

View logs:
```bash
docker-compose logs -f [service_name]
```

### Stopping the System

```bash
docker-compose down
```

To also remove volumes (database data):
```bash
docker-compose down -v
```

### Alternative Deployment Configurations

**Company Server Deployment** (excludes customer-facing services):
```bash
docker-compose -f docker-compose-company-server.yml up --build
```

**Customer Deployment** (lightweight setup for end users):
```bash
docker-compose -f docker-compose-customer.yml up --build
```

### Testing Individual Components

Run a specific service:
```bash
docker-compose up catalog db mosquitto
```

### Troubleshooting

**Port conflicts**: If ports are already in use, modify the port mappings in `docker-compose.yml`:
```yaml
ports:
  - "8001:8080"  # Changed from 8080:8080
```

**Database connection issues**: Ensure PostgreSQL is healthy:
```bash
docker-compose ps
docker-compose logs db
```

**MQTT connection problems**: Check Mosquitto broker status:
```bash
docker-compose logs mosquitto
```

**Service crashes**: View specific service logs:
```bash
docker-compose logs [service_name]
```

**Rebuild after code changes**:
```bash
docker-compose up --build --force-recreate
```

### Development Mode

For development with hot-reload (Python files mounted as volumes):
1. Ensure volumes are correctly mapped in `docker-compose.yml`
2. Make code changes on host machine
3. Services will automatically restart (depending on configuration)

### API Documentation

**Catalog REST API Endpoints** (available at `http://localhost:8080`):

- **Authentication**:
  - `POST /register` - Register new user
  - `POST /login` - Login and get JWT token
  - `GET /profile` - Get user profile (requires auth)

- **Greenhouses**:
  - `GET /greenhouses` - List all greenhouses
  - `POST /greenhouses` - Create new greenhouse
  - `GET /greenhouses/{id}` - Get greenhouse details
  - `PUT /greenhouses/{id}` - Update greenhouse
  - `DELETE /greenhouses/{id}` - Delete greenhouse

- **Sensors**:
  - `GET /greenhouses/{gh_id}/sensors` - List sensors
  - `POST /greenhouses/{gh_id}/sensors` - Add sensor
  - `GET /sensor-data/{sensor_id}` - Get sensor readings

- **Scheduling**:
  - `GET /schedules` - List schedules
  - `POST /schedules` - Create schedule
  - `PUT /schedules/{id}` - Update schedule
  - `DELETE /schedules/{id}` - Delete schedule

(Refer to `catalog/Catalog.py` for complete API documentation)

## Technologies Used

- **Backend**: Python 3.11, CherryPy (REST API)
- **Database**: PostgreSQL 15
- **Message Broker**: Eclipse Mosquitto (MQTT)
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Web Server**: NGINX
- **Containerization**: Docker, Docker Compose
- **Data Analysis**: SciPy (linear regression)
- **Authentication**: JWT (JSON Web Tokens), bcrypt
- **External APIs**: Telegram Bot API, ThingSpeak API

## Contributors

This project was developed as part of the **Programming for IoT** course.

## License

This project is part of academic coursework and is intended for educational purposes.
