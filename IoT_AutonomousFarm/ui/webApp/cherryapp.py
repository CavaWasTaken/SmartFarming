import os
import bcrypt
import jinja2
import cherrypy
import psycopg2
from psycopg2 import sql


TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '/Users/thatsnegar/SmartFarming/IoT_AutonomousFarm/ui/webApp')  # Path to templates directory
env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH))


# method to get a connection to the database
def get_db_connection():
    return psycopg2.connect(
        dbname="smartfarm_db",  # db name
        user="iotproject",  # username postgre sql
        password="WeWillDieForIoT", # password postgre sql
        host="localhost",    # host,
        port="5433" # port
    )

def cors():
    cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
    cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

cherrypy.tools.cors = cherrypy.Tool('before_handler', cors)

def getregister():
  cherrypy.response.headers['Content-Type'] = 'text/html'  # Set the Content-Type header
  template = env.get_template('registerform.html')
  return template.render().encode('utf-8')
  
    
def register(conn, username, email, password):
    with conn.cursor() as cur:
        # check if the username already exists
        cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
        user = cur.fetchone()
        if user is not None:
            raise cherrypy.HTTPError(409, "Username already exists")
        # insert the new user in the db
        try:
            # salt hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cur.execute(sql.SQL("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"), [username, email, hashed_password])
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            raise cherrypy.HTTPError(409, "Username already exists")
        except psycopg2.errors.NotNullViolation:
            raise cherrypy.HTTPError(400, "Username, email or password not provided")
        except:
            raise cherrypy.HTTPError(500, "Internal error")
        
        cur.execute(sql.SQL("SELECT * FROM users WHERE username = %s"), [username])
        user = cur.fetchone()

        if user is None:
            raise cherrypy.HTTPError(401, "Incorrect username")
        
        return {
            'message': 'User registered successfully',
            'user_id': user[0],
            'username': user[1],
            'email': user[2]
        }

class CatalogREST(object):
    exposed = True

    def __init__(self, catalog_connection):
        self.catalog_connection = catalog_connection

    @cherrypy.tools.encode(encoding='utf-8')
    def GET(self, *uri, **params):
        if len(uri) == 0:
           return 'notfound'
        elif uri[0] == 'getregister':
            return getregister()
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
    @cherrypy.tools.cors()
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    @cherrypy.tools.allow(methods=['POST'])
    def POST(self, *uri, **params):
        if len(uri) == 0:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')
        elif uri[0] == 'register':
            input_json = cherrypy.request.json
            return register(self.catalog_connection, input_json['username'], input_json['email'], input_json['password'])
        else:
            raise cherrypy.HTTPError(status=400, message='UNABLE TO MANAGE THIS URL')

    @cherrypy.tools.cors()
    def OPTIONS(self, *args, **kwargs):
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return ''

    @cherrypy.tools.json_out()
    def PUT(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')
        
    @cherrypy.tools.json_out()
    def DELETE(self, *uri, **params):
        raise cherrypy.HTTPError(status=405, message='METHOD NOT ALLOWED')

if __name__ == "__main__":
    # configuration of the server
    catalogClient = CatalogREST(get_db_connection())
    conf = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')],
            'tools.cors.on': True
        },
        '/ui':{
            'tools.staticdir.on': True,
             'tools.staticdir.dir': os.path.abspath("webApp")
        }
    }
    cherrypy.config.update({'server.socket_host': '0.0.0.0', 'server.socket_port': 5004})
    cherrypy.tree.mount(catalogClient, '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()