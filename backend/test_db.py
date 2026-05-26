from db import get_connection

try:
    conn = get_connection()
    print("SUCCESS - Database connected!")
    conn.close()
except Exception as e:
    print("FAILED:", e)