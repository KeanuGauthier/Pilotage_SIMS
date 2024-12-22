from mesure import Mesure
from datetime import datetime
import numpy as np
import uuid


class Capteur:
    def __init__(self, robot, map_image):
        if map_image is None:
            raise ValueError("Erreur : Carte non chargée ou invalide.")
        self.__robot = robot
        self.__map_image = map_image

    def distance_to_obstacle0(self, x, y, angle, max_distance=500):
        height, width = self.__map_image.shape

        # Parcourt chaque unité de distance jusqu'à la limite définie
        for d in range(1, max_distance + 1):
            # Calcule les coordonnées du point à vérifier sur la carte
            check_x = int(x + d * np.cos(np.radians(angle)))
            check_y = int(y + d * np.sin(np.radians(angle)))

            # Vérifie si le point est en dehors des limites de la carte
            if check_x < 0 or check_x >= width or check_y < 0 or check_y >= height:
                return d - 1  # Retourne la distance maximale possible avant la sortie

            # Vérifie si le point rencontré correspond à un obstacle (pixel noir)
            if self.__map_image[check_y, check_x] == 0:
                return d  # Retourne la distance jusqu'à l'obstacle

        # Si aucun obstacle n'est détecté, retourne la distance maximale
        return max_distance

    def distance_to_obstacle1(self, x, y, angle, max_distance=500):
        height, width = self.__map_image.shape
        for d in range(1, max_distance + 1):
            check_x = int(x + d * np.cos(np.radians(angle + 5)))
            check_y = int(y + d * np.sin(np.radians(angle + 5)))
            if check_x < 0 or check_x >= width or check_y < 0 or check_y >= height:
                return d - 1
            if self.__map_image[check_y, check_x] == 0:
                return d
        return max_distance

    def distance_to_obstacle2(self, x, y, angle, max_distance=500):
        height, width = self.__map_image.shape
        for d in range(1, max_distance + 1):
            check_x = int(x + d * np.cos(np.radians(angle + 10)))
            check_y = int(y + d * np.sin(np.radians(angle + 10)))
            if check_x < 0 or check_x >= width or check_y < 0 or check_y >= height:
                return d - 1
            if self.__map_image[check_y, check_x] == 0:
                return d
        return max_distance

    def distance_to_obstacle3(self, x, y, angle, max_distance=500):
        height, width = self.__map_image.shape
        for d in range(1, max_distance + 1):
            check_x = int(x + d * np.cos(np.radians(angle - 5)))
            check_y = int(y + d * np.sin(np.radians(angle - 5)))
            if check_x < 0 or check_x >= width or check_y < 0 or check_y >= height:
                return d - 1
            if self.__map_image[check_y, check_x] == 0:
                return d
        return max_distance

    def distance_to_obstacle4(self, x, y, angle, max_distance=500):
        height, width = self.__map_image.shape
        for d in range(1, max_distance + 1):
            check_x = int(x + d * np.cos(np.radians(angle - 10)))
            check_y = int(y + d * np.sin(np.radians(angle - 10)))
            if check_x < 0 or check_x >= width or check_y < 0 or check_y >= height:
                return d - 1
            if self.__map_image[check_y, check_x] == 0:
                return d
        return max_distance

    def capte(self) -> Mesure:
        distance0 = int(self.distance_to_obstacle0(
            self.__robot.x,
            self.__robot.y,
            self.__robot.angle
        ))
        distance1 = int(self.distance_to_obstacle1(
            self.__robot.x,
            self.__robot.y,
            self.__robot.angle
        ))
        distance2 = int(self.distance_to_obstacle2(
            self.__robot.x,
            self.__robot.y,
            self.__robot.angle
        ))
        distance3 = int(self.distance_to_obstacle3(
            self.__robot.x,
            self.__robot.y,
            self.__robot.angle
        ))
        distance4 = int(self.distance_to_obstacle4(
            self.__robot.x,
            self.__robot.y,
            self.__robot.angle
        ))

        return Mesure(
            id=uuid.uuid4().int,
            x=int(self.__robot.x),
            y=int(self.__robot.y),
            date_heure=datetime.now(),
            angle=self.__robot.angle,
            distance0=distance0,
            distance1=distance1,
            distance2=distance2,
            distance3=distance3,
            distance4=distance4,
            vitesse_moteur_droit=self.__robot.vitesse_moteur_droit,
            vitesse_moteur_gauche=self.__robot.vitesse_moteur_gauche,
        )