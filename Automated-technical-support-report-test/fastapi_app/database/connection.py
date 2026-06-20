import pymssql
from fastapi_app.config.settings import DB_TDS_VERSION,DB_CHARSET, DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT


def get_connection():
    return pymssql.connect (
        server=DB_SERVER,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        tds_version=DB_TDS_VERSION,
        charset=DB_CHARSET
    )
