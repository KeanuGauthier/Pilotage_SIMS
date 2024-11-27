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

    def distance_to_obstacle(self, x, y, angle, max_distance=500):
        height, width = self.__map_image.shape

        for d in range(1, max_distance + 1):
            check_x = int(x + d * np.cos(np.radians(angle)))
            check_y = int(y + d * np.sin(np.radians(angle)))

            if check_x < 0 or check_x >= width or check_y < 0 or check_y >= height:
                return d - 1

            if self.__map_image[check_y, check_x] == 0:
                return d

        return max_distance

    def capte(self) -> Mesure:
        distance = int(self.distance_to_obstacle(
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
            distance=distance,
            vitesse_moteur_droit=self.__robot.vitesse_moteur_droit,
            vitesse_moteur_gauche=self.__robot.vitesse_moteur_gauche,
        )