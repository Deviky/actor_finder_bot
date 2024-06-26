import sqlite3
import config as cnfg
class DataBase():
    def __init__(self):
        self.con = sqlite3.connect(cnfg.DB_NAME);
        self.cursor = self.con.cursor();

    def getById(self, tablename, id):
        res = self.cursor.execute(f"SELECT * FROM '{tablename}' WHERE id = ?", (id,)).fetchone()
        return res

    def getAllIds(self, tablename):
        res = self.cursor.execute(f"SELECT id FROM '{tablename}'").fetchall()
        return [row[0] for row in res]
