import sqlite3
import io
import numpy as np

def convert_array(text):
    out = io.BytesIO(text)
    print("converted from bytes", out)
    out.seek(0)
    return np.load(out)

with sqlite3.connect("database.sqlite3") as cons:
    cursor = cons.cursor()
    #cursor.execute("INSERT INTO embeddings (uid, data) VALUES ('ksdfj', 'slkdfj')")
    cursor.execute("SELECT data FROM embeddings where uid = 232312")
    print(convert_array(cursor.fetchone()[0]).shape)
