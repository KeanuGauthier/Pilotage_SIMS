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
        INSERT INTO mesures (id, x, y, date_heure, angle, distance0, distance1, distance2, distance3, distance4, vitesse_moteur_droit, vitesse_moteur_gauche)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            mesure.id,
            mesure.x,
            mesure.y,
            mesure.date_heure,
            mesure.angle,
            mesure.distance0,
            mesure.distance1,
            mesure.distance2,
            mesure.distance3,
            mesure.distance4,
            mesure.vitesse_moteur_droit,
            mesure.vitesse_moteur_gauche,
        )
        # Vérifiez que le nombre de colonnes correspond au nombre de valeurs
        self.cursor.execute(query, values)
        self.connection.commit()

    def clear_table(self):
        query = "DELETE FROM mesures;"
        self.cursor.execute(query)
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()