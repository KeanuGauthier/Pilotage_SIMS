import mysql.connector
from config import DATABASE

class Database:
    def __init__(self):
        self.connection = mysql.connector.connect(
            host=DATABASE['host'],
            user=DATABASE['user'],
            password=DATABASE['password'],
            database=DATABASE['database']
        )
        self.cursor = self.connection.cursor()

    def insert_mesure(self, mesure):
        query = """
        INSERT INTO mesures (id, x, y, date_heure, angle, distance, vitesse_moteur_droit, vitesse_moteur_gauche)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        values = (
            mesure.id, mesure.x, mesure.y, mesure.date_heure,
            mesure.angle, mesure.distance,
            mesure.vitesse_moteur_droit, mesure.vitesse_moteur_gauche
        )
        self.cursor.execute(query, values)
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()