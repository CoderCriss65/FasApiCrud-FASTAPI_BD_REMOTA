import mysql.connector
from mysql.connector import pooling, errorcode
import os
import logging
from contextlib import contextmanager

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")

class DBConfig:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "bsuwmw1ycddteycis6m7-mysql.services.clever-cloud.com")
        self.user = os.getenv("DB_USER", "u2laijuwgrququak")
        self.password = os.getenv("DB_PASSWORD", "K7tO7lfFm2i7vXAGHN6U")
        self.database = os.getenv("DB_NAME", "bsuwmw1ycddteycis6m7")
        self.port = int(os.getenv("DB_PORT", 3306))
        self.ssl_disabled = os.getenv("SSL_DISABLED", "True") == "True"
        self.pool_size = int(os.getenv("DB_POOL_SIZE", 3))  # Tamaño reducido por defecto

    def connection_params(self):
        params = {
            "host": self.host,
            "user": self.user,
            "password": self.password,
            "database": self.database,
            "port": self.port,
        }
        if not self.ssl_disabled:
            params["ssl_ca"] = "/etc/ssl/cert.pem"
        return params

# Configuración de la base de datos mysql
db_config = DBConfig()

# Crear pool de conexiones con manejo de errores
connection_pool = None
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="fastapi_pool",
        pool_size=db_config.pool_size,
        **db_config.connection_params()
    )
    logger.info(f"✅ Pool de conexiones creado con {db_config.pool_size} conexiones")
    
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_USER_LIMIT_REACHED:
        # Manejar específicamente el error de límite de conexiones
        logger.error("❌ Error: Has excedido el límite de conexiones simultáneas")
        logger.error(f"Límite actual: 5 conexiones | Intentaste: {db_config.pool_size} conexiones")
        logger.error("Solución: Reduce DB_POOL_SIZE en tu archivo .env a 3 o 4")
        
        # Crear un pool más pequeño como fallback
        reduced_size = min(3, db_config.pool_size - 2)
        logger.warning(f"Intentando crear un pool reducido de {reduced_size} conexiones...")
        
        try:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="fastapi_pool_reduced",
                pool_size=reduced_size,
                **db_config.connection_params()
            )
            logger.info(f"✅ Pool reducido creado con {reduced_size} conexiones")
        except mysql.connector.Error as err2:
            logger.error(f"❌ Error al crear pool reducido: {err2}")
            raise RuntimeError("No se pudo crear el pool de conexiones") from err2
            
    else:
        logger.error(f"❌ Error al crear el pool de conexiones: {err}")
        raise RuntimeError("Error de conexión a la base de datos") from err

@contextmanager
def get_db_connection():
    if connection_pool is None:
        raise RuntimeError("El pool de conexiones no está inicializado")
    
    conn = None
    try:
        conn = connection_pool.get_connection()
        logger.info("✅ Conexión obtenida del pool")
        yield conn
    except mysql.connector.Error as err:
        logger.error(f"Error de conexión a la base de datos: {err}")
        raise
    finally:
        if conn and conn.is_connected():
            conn.close()
            logger.info("🔌 Conexión devuelta al pool")

@contextmanager
def get_db_cursor():
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            yield cursor, conn
        finally:
            cursor.close()

def execute_query(query, params=None, fetch_one=False, fetch_all=False, lastrowid=False):
    with get_db_cursor() as (cursor, conn):
        logger.info(f"DB QUERY: {query}")
        if params:
            logger.info(f"DB PARAMS: {params}")
        
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
            logger.info(f"DB RESULT: {result}")
            return result
        elif fetch_all:
            result = cursor.fetchall()
            logger.info(f"DB RESULT: {len(result)} registros")
            return result
        elif lastrowid:
            conn.commit()
            result = cursor.lastrowid
            logger.info(f"DB RESULT: ID generado - {result}")
            return result
        else:
            conn.commit()
            affected_rows = cursor.rowcount
            logger.info(f"DB RESULT: Filas afectadas - {affected_rows}")
            return affected_rows