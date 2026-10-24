import mysql.connector
from mysql.connector import pooling
from flask import current_app

_pool = None


def get_db_connection():
    global _pool

    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="rido_pool",
            pool_size=5,
            pool_reset_session=False,
            host=current_app.config["DB_HOST"],
            user=current_app.config["DB_USER"],
            password=current_app.config["DB_PASSWORD"],
            database=current_app.config["DB_NAME"],
            port=current_app.config["DB_PORT"],
        )

    conn = _pool.get_connection()
    # Aiven may close idle connections, so revive one if needed
    conn.ping(reconnect=True, attempts=3, delay=0)
    return conn