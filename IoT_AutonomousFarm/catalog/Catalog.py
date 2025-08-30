# ============================================
# Catalog Service (CherryPy) — Structured Layout
# ============================================
# Sections:
#   0) Imports
#   1) Logging & Config Bootstrapping
#   2) Server Utilities (DB, CORS, JWT)
#   3) Domain: Greenhouse (info, location, devices)
#   4) Domain: Areas (CRUD, lookups)
#   5) Domain: Sensors (catalog + greenhouse sensors)
#   6) Domain: Plants (catalog + greenhouse plants)
#   7) Domain: Scheduling (events)
#   8) Domain: Users & Auth (register/login/profile)
#   9) Domain: Telegram / OTP Binding
#  10) Domain: ThingSpeak Integration
#  11) REST Router (CatalogREST)
#  12) Main Entrypoint
# ============================================

# -------------------------------
# 0) Imports
# -------------------------------
import cherrypy
import psycopg2
from psycopg2 import sql
import bcrypt
import json
import os
import jwt
import datetime
import time
import requests


# -----------------------------------------------
# 1) Logging & Config Bootstrapping
# -----------------------------------------------
def write_log(message):
    """Append message to Catalog.log"""
    with open("./logs/Catalog.log", "a") as log_file:
        log_file.write(f"{message}\n")

os.makedirs("./logs", exist_ok=True)  # ensure logs dir

# clear log on startup
with open("./logs/Catalog.log", "w") as log_file:
    pass

try:
    with open("./Catalog_config.json", "r") as config_fd:
        config = json.load(config_fd)
        telegram_token = config["telegram_token"]
except FileNotFoundError:
    write_log("Catalog_config.json file not found")
    exit(1)
except json.JSONDecodeError:
    write_log("Error decoding JSON file")
    exit(1)
except KeyError as e:
    write_log(f"Missing key in JSON file: {e}")
    exit(1)


# -----------------------------------------------
# 2) Server Utilities (DB, CORS, JWT)
# -----------------------------------------------
def get_db_connection():
    """Retry up to 5x to connect to Postgres."""
    for _ in range(5):
        try:
            write_log("Database connection estabilished")
            return psycopg2.connect(
                dbname="smartfarm_db",
                user="iotproject",
                password="WeWillDieForIoT",
                host="db",
                port="5432"
            )
        except psycopg2.Error as e:
            write_log(f"Error connecting to database: {e}")
            if _ == 4:
                write_log("Failed to connect to the database after 5 attempts")
                raise Exception("Unable to connect to the database")
            time.sleep(60)

def cors():
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

cherrypy.tools.cors = cherrypy.Tool('before_handler', cors)

# JWT
SECRET_KEY = config["SECRET_KEY"]

def generate_token(user_id, username):
    """Create HS256 JWT (used by: POST /login)"""
    try:
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": int(expiration.timestamp()),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return token
    except Exception as e:
        print(f"Error generating token: {e}")
        raise cherrypy.HTTPError(500, "Internal error")


# ---------------------------------------------------------
# 3) Domain: Greenhouse (info, location, devices)
# ---------------------------------------------------------
# NOTE endpoints:
#   GET /get_greenhouse_info           -> get_greenhouse_info
#   GET /get_greenhouse_location       -> get_greenhouse_location
#   GET /get_devices                   -> get_devices

def get_greenhouse_location(conn, greenhouse_id):
    """Return location for greenhouse_id"""
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT location FROM greenhouses WHERE greenhouse_id = %s"), [greenhouse_id,])
            result = cur.fetchone()
            if result is None:
                cherrypy.response.status = 404
                return {"error": "Greenhouse not found"}
            location = result[0]
            return {'location': location}
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

def get_greenhouse_info(conn, greenhouse_id):
    """Return greenhouse row as dict"""
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM greenhouses WHERE greenhouse_id = %s"), [greenhouse_id,])
            greenhouse = cur.fetchone()
            if greenhouse is None:
                raise cherrypy.HTTPError(404, "Greenhouse not found")
            return {
                'greenhouse_id': greenhouse[0],
                'user_id': greenhouse[1],
                'name': greenhouse[2],
                'location': greenhouse[3],
                'thingSpeak_config': greenhouse[4]
            }
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

def get_devices(conn, greenhouse_id):
    """List devices for greenhouse"""
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM devices WHERE greenhouse_id = %s"), [greenhouse_id])
            devices = cur.fetchall() or []
            if devices is None:
                cherrypy.response.status = 404
                return {"error": "No devices found"}
            devices_list = [{
                'device_id': d[0],
                'greenhouse_id': d[1],
                'name': d[2],
                'type': d[3],
            } for d in devices]
            return {'devices': devices_list}
    except Exception:
        cherrypy.response.status = 500
        return {"error": "Internal error"}


# -----------------------------------------------
# 4) Domain: Areas (CRUD, lookups)
# -----------------------------------------------
# NOTE endpoints:
#   GET  /get_areas_by_greenhouse      -> get_areas_by_greenhouse
#   GET  /get_area_info                -> get_area_info
#   POST /add_area                     -> add_area
#   POST /remove_area_from_greenhouse  -> remove_area_from_greenhouse

def get_areas_by_greenhouse(conn, greenhouse_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute("""
                SELECT area_id, name
                FROM areas
                WHERE greenhouse_id = %s
            """, (greenhouse_id,))
            areas = cur.fetchall() or []
            area_list = [{"area_id": r[0], "name": r[1]} for r in areas]
            return {"areas": area_list}
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

def add_area(conn, greenhouse_id, name):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute("SELECT greenhouse_id FROM greenhouses WHERE greenhouse_id = %s", [greenhouse_id])
            if not cur.fetchone():
                cherrypy.response.status = 404
                return {"error": "Greenhouse not found"}
            cur.execute(
                """
                INSERT INTO areas (name, greenhouse_id)
                VALUES (%s, %s)
                RETURNING area_id
                """,
                (name, greenhouse_id)
            )
            area_id = cur.fetchone()[0]
            conn.commit()
            return {"message": "Area added successfully", "area_id": area_id, "greenhouse_id": greenhouse_id, "name": name}
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

def get_area_info(conn, greenhouse_id, area_id):
    try:
        greenhouse_id = int(greenhouse_id)
        area_id = int(area_id)
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM areas WHERE greenhouse_id = %s AND area_id = %s"), [greenhouse_id, area_id])
            area = cur.fetchone()
            if not area:
                cherrypy.response.status = 404
                return {"error": "Area not found"}
            return {'area_id': area[0], 'name': area[1], 'greenhouse_id': area[2]}
    except ValueError:
        cherrypy.response.status = 400
        return {"error": "Invalid greenhouse_id or area_id. Must be integers."}
    except psycopg2.Error as e:
        cherrypy.response.status = 500
        return {"error": f"Database error: {str(e)}"}
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": f"Internal server error: {str(e)}"}

def remove_area_from_greenhouse(conn, greenhouse_id, area_id):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM areas WHERE greenhouse_id = %s AND area_id = %s"), [greenhouse_id, area_id])
        area = cur.fetchone()
        if area is None:
            raise cherrypy.HTTPError(404, "area is not in the greenhouse")
        try:
            cur.execute(sql.SQL("DELETE FROM areas WHERE greenhouse_id = %s AND area_id = %s"), [greenhouse_id, area_id])
            conn.commit()
            cur.execute(sql.SQL("SELECT area_id FROM areas WHERE area_id = %s"), [area_id])
            areas = cur.fetchall()
            if areas is None:
                raise cherrypy.HTTPError(404, "No areas found")
            area_list = []
            for area in areas:
                cur.execute(sql.SQL("SELECT * FROM areas WHERE area_id = %s"), [area[0]])
                area = cur.fetchone()
                area_dict = {'area_id': area[0], 'name': area[1]}
                area_list.append(area_dict)
            return area_list
        except:
            raise cherrypy.HTTPError(500, "Internal error")


# -------------------------------------------------
# 5) Domain: Sensors (catalog + greenhouse sensors)
# -------------------------------------------------
# NOTE endpoints:
#   GET  /get_sensors                  -> get_sensors
#   GET  /get_all_sensors              -> get_all_sensors
#   POST /add_sensor_from_available    -> add_sensor_from_available
#   POST /set_sensor_threshold         -> set_sensor_threshold
#   GET  /get_sensors_area             -> get_sensors_area
#   POST /remove_sensor_from_greenhouse-> remove_sensor_from_greenhouse

def get_sensors(conn, greenhouse_id, device_name):
    """Device-aware sensor listing"""
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            if device_name is not None and device_name != "WebApp":
                cur.execute(sql.SQL("SELECT * FROM devices WHERE greenhouse_id = %s AND name = %s"), [greenhouse_id, device_name])
                result = cur.fetchone()
                if result is None:
                    cherrypy.response.status = 404
                    return {"error": "Unexisting device"}
                device_id = result[0]
            else:
                device_id = None

            write_log(device_name)
            authorized_devices = ["DeviceConnector", "DataAnalysis", "ThingSpeakAdaptor", "TelegramBot", "TimeShift", "WebApp"]
            if device_name in authorized_devices:
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s"),  [greenhouse_id,])
            elif device_name == "HumidityManagement":
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s AND type = 'Humidity' OR type = 'SoilMoisture'"), [greenhouse_id,])
            elif device_name == "LightManagement":
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s AND type = 'LightIntensity' OR type = 'Temperature'"), [greenhouse_id,])
            elif device_name == "NutrientManagement":
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s AND type = 'NPK' OR type = 'pH' OR type = 'SoilMoisture'"), [greenhouse_id,])
            sensors = cur.fetchall()
            if sensors is None:
                cherrypy.response.status = 404
                return {"error": "No sensors found"}
            sensors_list = []
            for s in sensors:
                sensors_list.append({
                    'sensor_id': s[0],
                    'area_id': s[1],
                    'type': s[2],
                    'name': s[3],
                    'unit': s[4],
                    'threshold': s[5],
                    'domain': s[6],
                    'greenhouse_id': s[7]
                })
            write_log(sensors_list)
            return {'device_id': device_id, 'sensors': sensors_list}
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

def set_sensor_threshold(conn, sensor_id, threshold):
    """Update threshold_range for sensor (POST /set_sensor_threshold)"""
    threshold = json.dumps(threshold)
    with conn.cursor() as cur:
        try:
            cur.execute(sql.SQL("UPDATE sensors SET threshold_range = %s WHERE sensor_id = %s"), [threshold, sensor_id])
            conn.commit()
            return {'message': 'Threshold set'}
        except psycopg2.errors.NotNullViolation:
            raise cherrypy.HTTPError(400, "Threshold not provided")
        except:
            raise cherrypy.HTTPError(500, "Internal error")

def get_all_sensors(conn):
    """List available sensors (templates) from availablesensors"""
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM availablesensors;"))
        sensors = cur.fetchall()
        if sensors is None:
            raise cherrypy.HTTPError(404, "No sensors found")
        sensors_list = [{'sensor_id': s[0], 'name': s[1], 'type': s[2]} for s in sensors]
        return {'sensors': sensors_list}

def add_sensor_from_available(conn, greenhouse_id, sensor_id, area_id):
    """Instantiate sensor from catalog into greenhouse"""
    with conn.cursor() as cur:
        try:
            cur.execute(
                sql.SQL("SELECT type, name, unit, threshold_range, domain FROM availablesensors WHERE sensor_id = %s"),
                [sensor_id]
            )
            sensor = cur.fetchone()
            if sensor is None:
                cherrypy.response.status = 404
                return {"error": "Sensor not found in available sensors"}
            sensor_type, name, unit, threshold_range, domain = sensor
            if isinstance(threshold_range, dict):
                threshold_range = json.dumps(threshold_range)
            if isinstance(domain, dict):
                domain = json.dumps(domain)
            try:
                cur.execute(
                    sql.SQL("""
                        INSERT INTO sensors (greenhouse_id, type, name, unit, threshold_range, domain, area_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING greenhouse_id
                    """),
                    [greenhouse_id, sensor_type, name, unit, threshold_range, domain, area_id]
                )
                new_sensor_id = cur.fetchone()[0]
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                cherrypy.response.status = 409
                return {"error": "Sensor already exists in this greenhouse"}
            return {
                'message': 'Sensor added successfully',
                'sensor_id': new_sensor_id,
                'greenhouse_id': greenhouse_id,
                'type': sensor_type,
                'name': name,
                'unit': unit,
                'threshold_range': threshold_range,
                'domain': domain,
                'area_id': area_id
            }
        except psycopg2.Error as e:
            conn.rollback()
            raise cherrypy.HTTPError(500, f"Database error: {str(e)}")
        except Exception as e:
            conn.rollback()
            raise cherrypy.HTTPError(500, f"Internal error: {str(e)}")

def get_sensors_area(conn, greenhouse_id, area_id):
    """List sensors of an area"""
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM sensors WHERE greenhouse_id = %s and area_id = %s"), [greenhouse_id, area_id])
            sensors = cur.fetchall() or []
            if sensors is None:
                cherrypy.response.status = 404
                return {"error": "No sensors found"}
            sensors_list = [{
                'sensor_id': s[0],
                'greenhouse_id': s[1],
                'type': s[2],
                'name': s[3],
                'unit': s[4],
                'threshold': s[5],
                'domain': s[6],
                'area_id': s[7]
            } for s in sensors]
            return {'sensors': sensors_list}
    except Exception:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

def remove_sensor_from_greenhouse(conn, area_id, sensor_id):
    """Delete sensor by area_id + sensor_id"""
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM sensors WHERE area_id = %s AND sensor_id = %s", [area_id, sensor_id])
        sensor = cur.fetchone()
        if sensor is None:
            raise cherrypy.HTTPError(404, "Sensor is not in the greenhouse")
        try:
            cur.execute("DELETE FROM sensors WHERE area_id = %s AND sensor_id = %s", [area_id, sensor_id])
            conn.commit()
            cur.execute("SELECT sensor_id FROM sensors WHERE area_id = %s", [area_id])
            sensors = cur.fetchall()
            if sensors is None:
                raise cherrypy.HTTPError(404, "No sensors found")
            sensor_list = []
            for s in sensors:
                cur.execute(sql.SQL("SELECT * FROM sensors WHERE sensor_id = %s"), [s[0]])
                row = cur.fetchone()
                sensor_dict = {'sensor_id': row[0], 'name': row[1], 'type': row[2], 'domain': row[3]}
                sensor_list.append(sensor_dict)
            return sensor_list
        except:
            raise cherrypy.HTTPError(500, "Internal error")


# -----------------------------------------------
# 6) Domain: Plants (catalog + greenhouse plants)
# -----------------------------------------------
# NOTE endpoints:
#   GET  /get_all_plants               -> get_all_plants
#   POST /add_plant_to_greenhouse      -> add_plant_to_greenhouse
#   POST /remove_plant_from_greenhouse -> remove_plant_from_greenhouse
#   GET  /get_plants_area              -> get_plants_area

def get_all_plants(conn):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM plants"))
            plants = cur.fetchall()
            if plants is None:
                cherrypy.response.status = 404
                return {"error": "No plants found"}
            plants_list = [{
                'plant_id': p[0],
                'name': p[1],
                'species': p[2],
                'desired_thresholds': p[3]
            } for p in plants]
            return {'plants': plants_list}
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

def add_plant_to_greenhouse(conn, greenhouse_id, plant_id, area_id):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM area_plants WHERE greenhouse_id = %s AND plant_id = %s AND area_id=%s"), [greenhouse_id, plant_id, area_id])
        plant = cur.fetchone()
        if plant is not None:
            raise cherrypy.HTTPError(404, "Plant already in the greenhouse")
        try:
            cur.execute(sql.SQL("INSERT INTO area_plants (greenhouse_id, plant_id, area_id) VALUES (%s, %s,%s)"), [greenhouse_id, plant_id, area_id])
            conn.commit()
            cur.execute(sql.SQL("SELECT plant_id FROM area_plants WHERE greenhouse_id = %s AND area_id=%s"), [greenhouse_id, area_id])
            plants = cur.fetchall()
            if plants is None:
                raise cherrypy.HTTPError(404, "No plants found")
            plants_list = []
            for pl in plants:
                cur.execute(sql.SQL("SELECT * FROM plants WHERE plant_id = %s"), [pl[0]])
                row = cur.fetchone()
                plant_dict = {'plant_id': row[0], 'name': row[1], 'species': row[2], 'desired_thresholds': row[3]}
                plants_list.append(plant_dict)
            return plants_list
        except:
            raise cherrypy.HTTPError(500, "Internal error")

def remove_plant_from_greenhouse(conn, area_id, plant_id):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM area_plants WHERE area_id = %s AND plant_id = %s"), [area_id, plant_id])
        plant = cur.fetchone()
        if plant is None:
            raise cherrypy.HTTPError(404, "Plant not in the greenhouse")
        try:
            cur.execute(sql.SQL("DELETE FROM area_plants WHERE area_id = %s AND plant_id = %s"), [area_id, plant_id])
            conn.commit()
            cur.execute(sql.SQL("SELECT plant_id FROM area_plants WHERE area_id = %s"), [area_id])
            plants = cur.fetchall()
            if plants is None:
                raise cherrypy.HTTPError(404, "No plants found")
            plants_list = []
            for pl in plants:
                cur.execute(sql.SQL("SELECT * FROM plants WHERE plant_id = %s"), [pl[0]])
                row = cur.fetchone()
                plant_dict = {'plant_id': row[0], 'name': row[1], 'species': row[2], 'desired_thresholds': row[3]}
                plants_list.append(plant_dict)
            return plants_list
        except:
            raise cherrypy.HTTPError(500, "Internal error")

def get_plants_area(conn, greenhouse_id, area_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT plant_id FROM area_plants WHERE greenhouse_id = %s and area_id = %s"), [greenhouse_id, area_id])
            plants = cur.fetchall() or []
            plants_list = []
            for pl in plants:
                cur.execute(sql.SQL("SELECT * FROM plants WHERE plant_id = %s"), [pl[0]])
                row = cur.fetchone() or []
                if row:
                    plant_dict = {
                        'plant_id': row[0],
                        'name': row[1],
                        'species': row[2],
                        'desired_thresholds': row[3],
                    }
                    plants_list.append(plant_dict)
            return {'plants': plants_list}
    except Exception:
        cherrypy.response.status = 500
        return {"error": "Internal error"}


# -----------------------------------------------
# 7) Domain: Scheduling (events)
# -----------------------------------------------
# NOTE endpoints:
#   GET    /get_scheduled_events       -> get_scheduled_events
#   POST   /schedule_event             -> schedule_event
#   DELETE /delete_event               -> delete_event

def get_scheduled_events(conn, device_id, device_name, greenhouse_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM scheduled_events WHERE greenhouse_id = %s"), [greenhouse_id])
            events = cur.fetchall()
            events_list = []
            for e in events:
                events_list.append({
                    'event_id': e[0],
                    'frequency': e[1],
                    'execution_time': str(e[2]),
                    'sensor_id': e[3],
                    'greenhouse_id': e[4],
                    'parameter': e[5],
                    'value': str(e[6])
                })
            return {'events': events_list}
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": "Internal error: " + str(e)}

def schedule_event(conn, greenhouse_id, sensor_id, parameter, frequency, value, execution_time):
    write_log(f"Scheduling event for greenhouse {greenhouse_id}, sensor {sensor_id}, parameter {parameter}, frequency {frequency}, value {value}, execution_time {execution_time}")
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("""
                INSERT INTO scheduled_events (greenhouse_id, frequency, sensor_id, parameter, execution_time, value)
                VALUES (%s, %s, %s, %s, %s, %s)
            """), [greenhouse_id, frequency, sensor_id, parameter, execution_time, value])
            conn.commit()
            cur.execute(sql.SQL("""
                SELECT * FROM scheduled_events
                WHERE greenhouse_id = %s AND frequency = %s AND sensor_id = %s AND parameter = %s AND execution_time = %s AND value = %s
            """), [greenhouse_id, frequency, sensor_id, parameter, execution_time, value])
            event = cur.fetchone()
            if event is None:
                cherrypy.response.status = 500
                return {"error": "Event not inserted"}
            cherrypy.response.status = 201
            return {
                'event_id': event[0],
                'frequency': event[1],
                'execution_time': str(event[2]),
                'sensor_id': event[3],
                'greenhouse_id': event[4],
                'parameter': event[5],
                'value': str(event[6])
            }
    except psycopg2.errors.NotNullViolation as e:
        cherrypy.response.status = 400
        return {"error": f"Missing required fields: {str(e)}"}
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

def delete_event(conn, device_id, event_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM devices WHERE device_id = %s"), [device_id])
            device = cur.fetchone()
            if device is None:
                cherrypy.response.status = 404
                return {"error": "Device not found"}
            cur.execute(sql.SQL("DELETE FROM scheduled_events WHERE event_id = %s"), [event_id])
            conn.commit()
            cherrypy.response.status = 200
            return
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}


# -----------------------------------------------
# 8) Domain: Users & Auth (register/login/profile)
# -----------------------------------------------
# NOTE endpoints:
#   POST /register                     -> register
#   POST /login                        -> login
#   GET  /get_user_info                -> get_user_info
#   POST /update_user_info             -> update_user_info
#   GET  /get_user_greenhouses         -> get_user_greenhouses
#   POST /add_greenhouse               -> add_greenhouse

def register(conn, username, email, password):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
            user = cur.fetchone()
            if user is not None:
                cherrypy.response.status = 409
                return {"error": "Username already exists"}
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cur.execute(sql.SQL("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"), [username, email, hashed_password])
            conn.commit()
            cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
            user = cur.fetchone()
            if user is None:
                cherrypy.response.status = 500
                return {"error": "Internal error"}
            return {'message': 'User registered successfully', 'user_id': user[0], 'username': user[1], 'email': user[2]}
    except psycopg2.errors.NotNullViolation:
        cherrypy.response.status = 400
        return {"error": "Missing required fields"}
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

def login(conn, username, password):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
            user = cur.fetchone()
            if user is None:
                cherrypy.response.status = 401
                return {"error": "Incorrect username"}
            stored_hash_raw = user[3]
            if stored_hash_raw is None or stored_hash_raw == "":
                cherrypy.response.status = 401
                return {"error": "Password not set"}
            if isinstance(stored_hash_raw, memoryview):
                stored_hash_bytes = bytes(stored_hash_raw)
            elif isinstance(stored_hash_raw, str) and stored_hash_raw.startswith("\\x"):
                stored_hash_bytes = bytes.fromhex(stored_hash_raw[2:])
            elif isinstance(stored_hash_raw, (bytes, bytearray)):
                stored_hash_bytes = stored_hash_raw
            else:
                stored_hash_bytes = stored_hash_raw.encode('utf-8') if isinstance(stored_hash_raw, str) else bytes(stored_hash_raw)
            try:
                if stored_hash_bytes.startswith(b"$2b$"):
                    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash_bytes):
                        cherrypy.response.status = 401
                        return {"error": "Incorrect password"}
                else:
                    db_pass = stored_hash_bytes.decode('utf-8', errors='ignore').strip()
                    if password.strip() != db_pass:
                        cherrypy.response.status = 401
                        return {"error": "Incorrect password"}
            except ValueError as ve:
                print("LOGIN ERROR: bcrypt invalid salt or corrupted hash:", ve)
                cherrypy.response.status = 401
                return {"error": "Invalid password format"}
            token = generate_token(user[0], user[1])
            cherrypy.response.headers['Authorization'] = f"Bearer {token}"
            return {'message': 'Login successful', 'user_id': user[0], 'username': user[1], 'email': user[2], 'token': token}
    except Exception as e:
        print("LOGIN ERROR TRACE:", e)
        cherrypy.response.status = 500
        return {"error": "Internal error"}

def get_user_greenhouses(conn, user_id, username):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM users WHERE user_id = %s AND username = %s"), [user_id, username])
            user = cur.fetchone()
            if user is None:
                cherrypy.response.status = 404
                return {"error": "User not found"}
            cur.execute(sql.SQL("SELECT * FROM greenhouses WHERE user_id = %s"), [user_id])
            greenhouses = cur.fetchall()
            if greenhouses is None:
                return {'greenhouses': []}
            greenhouses_list = [{
                'greenhouse_id': g[0],
                'user_id': g[1],
                'name': g[2],
                'location': g[3],
                'thingSpeak_config': g[4]
            } for g in greenhouses]
            return {'greenhouses': greenhouses_list}
    except:
        cherrypy.response.status = 500
        return {"error": "Internal error"}

def add_greenhouse(conn, user_id, name, location, thingspeak_config):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT * FROM greenhouses WHERE name = %s AND user_id = %s"),
                [name, user_id]
            )
            if cur.fetchone():
                cherrypy.response.status = 409
                return {"error": "Greenhouse with this name already exists for the user"}
            cur.execute(
                sql.SQL("""
                    INSERT INTO greenhouses (name, location, user_id, thingspeak_config)
                    VALUES (%s, %s, %s, %s)
                    RETURNING greenhouse_id, name, location
                """),
                [name, location, user_id, json.dumps(thingspeak_config) if thingspeak_config else json.dumps({"write_key": "", "read_key": "", "channel_id": ""})]
            )
            greenhouse = cur.fetchone()
            cur.execute(
                sql.SQL("""
                    INSERT INTO areas (greenhouse_id, name)
                    VALUES (%s, %s)
                    RETURNING area_id
                """),
                [greenhouse[0], "Main Area"]
            )
            main_area_id = cur.fetchone()[0]
            default_devices = [
                ("DeviceConnector", "DeviceConnector"),
                ("HumidityManagement", "Microservices"),
                ("LightManagement", "Microservices"),
                ("NutrientManagement", "Microservices"),
                ("DataAnalysis", "Microservices"),
                ("TimeShift", "Microservices"),
                ("ThingSpeakAdaptor", "ThingSpeakAdaptor"),
                ("TelegramBot", "UI")
            ]
            for name_dev, dev_type in default_devices:
                cur.execute(
                    """
                    INSERT INTO devices (greenhouse_id, name, type)
                    VALUES (%s, %s, %s)
                    """,
                    (greenhouse[0], name_dev, dev_type)
                )
            conn.commit()
            return {
                'message': 'Greenhouse added successfully',
                'greenhouse_id': greenhouse[0],
                'name': greenhouse[1],
                'location': greenhouse[2],
                'area_id': main_area_id
            }
    except psycopg2.errors.NotNullViolation as e:
        conn.rollback()
        cherrypy.response.status = 400
        return {"error": f"Missing required fields: {str(e)}"}
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

def get_user_info(conn, user_id):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT username, email FROM users WHERE user_id = %s;"), [user_id])
        user = cur.fetchone()
        if user is None:
            raise cherrypy.HTTPError(404, "No user found")
        return {'username': user[0], 'email': user[1]}

def update_user_info(conn, user_id, username, email, new_password=None):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM users WHERE user_id = %s"), [user_id])
            user = cur.fetchone()
            if not user:
                cherrypy.response.status = 404
                return {"error": "User not found"}
            cur.execute(sql.SQL("UPDATE users SET username = %s, email = %s WHERE user_id = %s"), [username, email, user_id])
            if new_password:
                hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute(sql.SQL("UPDATE users SET password_hash = %s WHERE user_id = %s"), [hashed_pw, user_id])
            conn.commit()
            return {"message": "User information updated successfully"}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cherrypy.response.status = 409
        return {"error": "Username or email already in use"}
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}


# -----------------------------------------------
# 9) Domain: Telegram / OTP Binding
# -----------------------------------------------
# NOTE endpoints:
#   GET  /get_telegram_chat_id         -> get_telegram_chat_id
#   POST /otp                          -> otp
#   POST /verify_telegram_otp          -> verify_telegram_otp
#   POST /logout_telegram              -> logout_telegram

def get_telegram_chat_id(conn, greenhouse_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT user_id FROM greenhouses WHERE greenhouse_id = %s;"), [greenhouse_id])
            chat_id = cur.fetchone()
            if chat_id is None:
                cherrypy.response.status = 404
                return {"error": "No greenhouse found with this ID"}
            cur.execute(sql.SQL("SELECT telegram_user_id FROM users WHERE user_id = %s;"), [chat_id[0]])
            chat_id = cur.fetchone()
            if chat_id is None:
                cherrypy.response.status = 404
                return {"error": "No Telegram chat ID found for this user"}
            return {'telegram_chat_id': chat_id[0]}
    except Exception as e:
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

def otp(conn, telegram_chat_id, otp_code):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM otps WHERE telegram_user_id = %s"), [telegram_chat_id])
            user = cur.fetchone()
            if not user:
                cur.execute(sql.SQL("INSERT INTO otps (telegram_user_id, otp) VALUES (%s, %s)"), [telegram_chat_id, otp_code])
            else:
                cur.execute(sql.SQL("UPDATE otps SET otp = %s WHERE telegram_user_id = %s"), [otp_code, telegram_chat_id])
            conn.commit()
            return {"message": "OTP code updated successfully"}
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

def verify_telegram_otp(conn, user_id, otp_code):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT telegram_user_id FROM otps WHERE otp = %s"), [otp_code])
            telegramUser = cur.fetchone()
            if not telegramUser:
                cherrypy.response.status = 404
                return {"error": "OTP code not found"}
            cur.execute(sql.SQL("DELETE FROM otps WHERE otp = %s"), [otp_code])
            cur.execute(sql.SQL("SELECT username, email FROM users WHERE user_id = %s"), [user_id])
            user_info = cur.fetchone()
            if not user_info:
                cherrypy.response.status = 404
                return {"error": "User not found"}
            try:
                cur.execute(sql.SQL("UPDATE users SET telegram_user_id = %s WHERE user_id = %s"), [telegramUser[0], user_id])
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                cherrypy.status = 409
                return {"error": f"Unique violation {str(e)}"}
            message = f"Welcome {user_info[0]}!"
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {"chat_id": telegramUser[0], "text": message}
            try:
                response = requests.post(url, json=payload, timeout=5)
                if response.ok:
                    write_log(f"Telegram message sent successfully to user {telegramUser[0]}")
                else:
                    write_log(f"Failed to send Telegram message: {response.text}")
            except Exception as e:
                write_log(f"Failed to send Telegram message: {e}")
            return {"telegram_user_id": telegramUser[0]}
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}

def logout_telegram(conn, user_id):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("UPDATE users SET telegram_user_id = NULL WHERE telegram_user_id = %s"), [user_id])
            conn.commit()
            return {"message": "User logged out successfully"}
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}


# -----------------------------------------------
# 10) Domain: ThingSpeak Integration
# -----------------------------------------------
# NOTE endpoints:
#   POST /update_thingspeak_config     -> update_thingspeak_config

def update_thingspeak_config(conn, greenhouse_id, channel_id, write_key, read_key):
    try:
        if conn.closed:
            cherrypy.response.status = 500
            return {"error": "Database connection is closed"}
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT * FROM greenhouses WHERE greenhouse_id = %s"), [greenhouse_id])
            greenhouse = cur.fetchone()
            if not greenhouse:
                cherrypy.response.status = 404
                return {"error": "Greenhouse not found"}
            cur.execute(
                sql.SQL("UPDATE greenhouses SET thingspeak_config = %s WHERE greenhouse_id = %s"),
                [json.dumps({"channel_id": channel_id, "write_key": write_key, "read_key": read_key}), greenhouse_id]
            )
            conn.commit()
            cherrypy.response.status = 200
            return {"message": "ThingSpeak configuration updated successfully"}
    except Exception as e:
        conn.rollback()
        cherrypy.response.status = 500
        return {"error": f"Internal error: {str(e)}"}


# -----------------------------------------------
# 11) REST Router (CatalogREST)
# -----------------------------------------------
class CatalogREST(object):
    exposed = True

    def __init__(self, catalog_connection):
        self.catalog_connection = catalog_connection

    @cherrypy.tools.cors()
    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        if len(uri) == 0:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}

        elif uri[0] == 'get_sensors':
            if 'greenhouse_id' in params and 'device_name' in params:
                return get_sensors(self.catalog_connection, params['greenhouse_id'], params['device_name'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_greenhouse_info':
            if 'greenhouse_id' in params:
                return get_greenhouse_info(self.catalog_connection, params['greenhouse_id'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_greenhouse_location':
            if 'greenhouse_id' in params:
                return get_greenhouse_location(self.catalog_connection, params['greenhouse_id'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_user_greenhouses':
            if 'user_id' in params and 'username' in params:
                return get_user_greenhouses(self.catalog_connection, params['user_id'], params['username'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_devices':
            if 'greenhouse_id' in params:
                return get_devices(self.catalog_connection, params['greenhouse_id'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_all_plants':
            if len(params) > 0:
                cherrypy.response.status = 400
                return {"error": "No parameters allowed"}
            return get_all_plants(self.catalog_connection)

        elif uri[0] == 'get_scheduled_events':
            if 'device_id' in params and 'device_name' in params and 'greenhouse_id' in params:
                return get_scheduled_events(self.catalog_connection, params["device_id"], params["device_name"], params["greenhouse_id"])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_all_sensors':
            if len(params) > 0:
                cherrypy.response.status = 400
                return {"error": "No parameters allowed"}
            return get_all_sensors(self.catalog_connection)

        elif uri[0] == 'get_areas_by_greenhouse':
            if 'greenhouse_id' in params:
                return get_areas_by_greenhouse(self.catalog_connection, params['greenhouse_id'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_sensors_area':
            if 'greenhouse_id' in params and 'area_id' in params:
                return get_sensors_area(self.catalog_connection, params['greenhouse_id'], params['area_id'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_plants_area':
            if 'greenhouse_id' in params and 'area_id' in params:
                return get_plants_area(self.catalog_connection, params['greenhouse_id'], params['area_id'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_user_info':
            if 'user_id' in params:
                return get_user_info(self.catalog_connection, params['user_id'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_telegram_chat_id':
            if 'greenhouse_id' in params:
                return get_telegram_chat_id(self.catalog_connection, params['greenhouse_id'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        elif uri[0] == 'get_area_info':
            if 'greenhouse_id' in params and 'area_id' in params:
                return get_area_info(self.catalog_connection, params['greenhouse_id'], params['area_id'])
            cherrypy.response.status = 400
            return {"error": "Missing parameters"}

        else:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}

    @cherrypy.tools.cors()
    @cherrypy.tools.encode(encoding='utf-8')
    @cherrypy.tools.json_out()
    def POST(self, *uri, **params):
        if len(uri) == 0:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}

        elif uri[0] == 'register':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'username' not in input_json or 'email' not in input_json or 'password' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return register(self.catalog_connection, input_json['username'], input_json['email'], input_json['password'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'login':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'username' not in input_json or 'password' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return login(self.catalog_connection, input_json['username'], input_json['password'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'add_plant_to_greenhouse':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'greenhouse_id' not in input_json or 'plant_id' not in input_json or 'area_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return add_plant_to_greenhouse(self.catalog_connection, input_json['greenhouse_id'], input_json['plant_id'], input_json['area_id'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'schedule_event':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                required = ["greenhouse_id", "sensor_id", "parameter", "frequency", "desired_value", "execution_time"]
                if any(k not in input_json for k in required):
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return schedule_event(self.catalog_connection, input_json['greenhouse_id'], input_json['sensor_id'], input_json['parameter'], input_json['frequency'], input_json['desired_value'], input_json['execution_time'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'add_greenhouse':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json or 'name' not in input_json or 'location' not in input_json or 'thingspeak_config' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return add_greenhouse(self.catalog_connection, input_json['user_id'], input_json['name'], input_json['location'], input_json['thingspeak_config'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'add_sensor_from_available':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'greenhouse_id' not in input_json or 'sensor_id' not in input_json or 'area_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return add_sensor_from_available(self.catalog_connection, input_json['greenhouse_id'], input_json['sensor_id'], input_json['area_id'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'add_area':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'greenhouse_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return add_area(self.catalog_connection, input_json['greenhouse_id'], input_json['name'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'otp':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json or 'otp_code' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return otp(self.catalog_connection, input_json['user_id'], input_json['otp_code'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        elif uri[0] == 'verify_telegram_otp':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json or 'otp' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return verify_telegram_otp(self.catalog_connection, input_json['user_id'], input_json['otp'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}

        else:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}
        
    @cherrypy.tools.cors()
    @cherrypy.tools.encode(encoding='utf-8')
    @cherrypy.tools.json_out()
    def PUT(self, *uri, **params):
        if len(uri) == 0:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}
            
        elif uri[0] == 'set_sensor_threshold':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'sensor_id' not in input_json or 'threshold' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                if not isinstance(input_json['threshold'], dict):
                    cherrypy.response.status = 400
                    return {"error": "Threshold must be a dictionary"}
                return set_sensor_threshold(self.catalog_connection, input_json['sensor_id'], input_json['threshold'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
                
        elif uri[0] == 'update_user_info':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json or 'username' not in input_json or 'email' not in input_json or 'new_password' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return update_user_info(self.catalog_connection, input_json['user_id'], input_json['username'], input_json['email'], input_json['new_password'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
                
        elif uri[0] == 'update_thingspeak_config':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                required = ['greenhouse_id', 'channel_id', 'writeKey', 'readKey']
                if any(k not in input_json for k in required):
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return update_thingspeak_config(self.catalog_connection, input_json['greenhouse_id'], input_json['channel_id'], input_json['writeKey'], input_json['readKey'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
            
        elif uri[0] == 'logout_telegram':
            try:
                input_json = json.loads(cherrypy.request.body.read())
                if 'user_id' not in input_json:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return logout_telegram(self.catalog_connection, input_json['user_id'])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
            
        else:
            cherrypy.response.status = 405
            return {"error": "METHOD NOT ALLOWED"}

    @cherrypy.tools.cors()
    @cherrypy.tools.encode(encoding='utf-8')
    @cherrypy.tools.json_out()
    def DELETE(self, *uri, **params):
        if len(uri) == 0:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}
        
        if uri[0] == 'delete_event':
            try:
                if "device_id" not in params and "event_id" not in params:
                    cherrypy.response.status = 400
                    return {"error": "Missing required fields"}
                return delete_event(self.catalog_connection, params["device_id"], params["event_id"])
            except json.JSONDecodeError:
                cherrypy.response.status = 400
                return {"error": "Invalid JSON format"}
            
        elif uri[0] == 'remove_area_from_greenhouse':
            if 'area_id' not in params or 'greenhouse_id' not in params:
                cherrypy.response.status = 400
                return {"error": "Missing required fields"}
            return remove_area_from_greenhouse(self.catalog_connection, params['greenhouse_id'], params['area_id'])
            
        elif uri[0] == 'remove_plant_from_greenhouse':
            if 'area_id' not in params or 'plant_id' not in params:
                cherrypy.response.status = 400
                return {"error": "Missing required fields"}
            return remove_plant_from_greenhouse(self.catalog_connection, params['area_id'], params['plant_id'])
            
        elif uri[0] == 'remove_sensor_from_greenhouse':
            if 'sensor_id' not in params or 'area_id' not in params:
                cherrypy.response.status = 400
                return {"error": "Missing required fields"}
            return remove_sensor_from_greenhouse(self.catalog_connection, params['area_id'], params['sensor_id'])
            
        else:
            cherrypy.response.status = 400
            return {"error": "UNABLE TO MANAGE THIS URL"}

    @cherrypy.tools.cors()
    def OPTIONS(self, *args, **kwargs):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return ''


# -----------------------------------------------
# 12) Main Entrypoint
# -----------------------------------------------
if __name__ == "__main__":
    try:
        write_log("Catalog service starting...")
        catalogClient = CatalogREST(get_db_connection())
        conf = {
            '/': {
                'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
                'tools.sessions.on': True,
                'tools.response_headers.on': True,
                'tools.response_headers.headers': [('Content-Type', 'application/json')],
                'tools.cors.on': True,
            },
        }
        cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 8080})
        cherrypy.tree.mount(catalogClient, '/', conf)
        cherrypy.engine.start()
    except Exception as e:
        write_log(f"Error starting the REST API: {e}")
        exit(1)