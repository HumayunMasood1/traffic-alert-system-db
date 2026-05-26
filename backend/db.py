import oracledb

USERNAME = "System"   # e.g. "system" or "hr"
PASSWORD = "Ezio-7619"   # your SQL Developer password

HOST = "localhost"
PORT = 1521
SID = "xe"

def get_connection():
    dsn = oracledb.makedsn(HOST, PORT, sid=SID)
    return oracledb.connect(user=USERNAME, password=PASSWORD, dsn=dsn)