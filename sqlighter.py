import sqlite3
import config as cnfg
class DataBase():
    def __init__(self):
        self.con = sqlite3.connect(cnfg.DB_NAME);
        self.cursor = self.con.cursor();

    def getActorById(self, id):
        res = self.cursor.execute("SELECT * FROM 'actors' WHERE id = ?", (id,)).fetchone()
        return res

    def getActressesById(self, id):
        res = self.cursor.execute("SELECT * FROM 'actresses' WHERE id = ?", (id,)).fetchone()
        return res

    def getAllActorIds(self):
        res = self.cursor.execute("SELECT id FROM 'actors'").fetchall()
        return [row[0] for row in res]

    def getAllActressIds(self):
        res = self.cursor.execute("SELECT id FROM 'actresses'").fetchall()
        return [row[0] for row in res]