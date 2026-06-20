import pytds
from fastapi_app.config.settings import DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT


def get_connection():
    return pytds.connect(
        server=DB_SERVER,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        autocommit=False,
    )
