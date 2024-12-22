import mysql.connector
from config import DATABASE


class Database:
    def __init__(self):
        # Initialisation de la connexion à la base de données MySQL à l'aide des paramètres définis dans `config.py`
        self.connection = mysql.connector.connect(
            host=DATABASE['host'],
            user=DATABASE['user'],
            password=DATABASE['password'],
            database=DATABASE['database']
        )
        # Création d'un curseur pour exécuter des requêtes SQL
        self.cursor = self.connection.cursor()

    def insert_mesure(self, mesure):
        # Préparation de la requête SQL pour insérer une mesure dans la table `mesures`
        query = """
        INSERT INTO mesures (id, x, y, date_heure, angle, distance0, distance1, distance2, distance3, distance4, vitesse_moteur_droit, vitesse_moteur_gauche)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            mesure.id,              # Identifiant unique de la mesure
            mesure.x,               # Coordonnée X du robot
            mesure.y,               # Coordonnée Y du robot
            mesure.date_heure,      # Date et heure de la mesure
            mesure.angle,           # Angle d'orientation du robot
            mesure.distance0,       # Distance détectée par le capteur principal
            mesure.distance1,       # Distance détectée à un angle +5°
            mesure.distance2,       # Distance détectée à un angle +10°
            mesure.distance3,       # Distance détectée à un angle -5°
            mesure.distance4,       # Distance détectée à un angle -10°
            mesure.vitesse_moteur_droit, # Vitesse du moteur droit
            mesure.vitesse_moteur_gauche # Vitesse du moteur gauche
        )
        # Exécution de la requête et enregistrement des modifications dans la base de données
        self.cursor.execute(query, values)
        self.connection.commit()

    def clear_table(self):
        # Suppression de toutes les entrées de la table `mesures`
        query = "DELETE FROM mesures;"
        self.cursor.execute(query)
        self.connection.commit()

    def close(self):
        # Fermeture du curseur et de la connexion à la base de données
        self.cursor.close()
        self.connection.close()