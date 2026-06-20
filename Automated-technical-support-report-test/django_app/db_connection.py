import pytds
from django.conf import settings


def get_connection():
    cfg = settings.MSSQL_CONFIG
    return pytds.connect(
        server=cfg['server'],
        user=cfg['user'],
        password=cfg['password'],
        database=cfg['database'],
        port=cfg['port'],
        autocommit=False,
    )



def get_role(user):
    try:
        return user.profile.role
    except:
        return None

def is_high_level(user):
    return get_role(user) in ['developer', 'owner']

def is_manager_level(user):
    return get_role(user) in ['developer', 'owner', 'admin', 'agent']

def is_agent_level(user):
    return get_role(user) in ['developer', 'owner', 'admin', 'agent']

def is_visitor(user):
    return get_role(user) == 'visitor'