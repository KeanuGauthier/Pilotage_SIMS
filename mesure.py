from datetime import datetime

class Mesure:
    def __init__(self, id: int, x: int, y: int, date_heure: datetime, angle: int, distance: float,
                 vitesse_moteur_droit: float, vitesse_moteur_gauche: float):
        self.__id = id
        self.__x = x
        self.__y = y
        self.__date_heure = date_heure
        self.__angle = angle
        self.__distance = distance
        self.__vitesse_moteur_droit = vitesse_moteur_droit
        self.__vitesse_moteur_gauche = vitesse_moteur_gauche

    def __str__(self):
        return f"Mesure(ID: {self.__id}, X: {self.__x}, Y: {self.__y}, Angle: {self.__angle}, " \
               f"Distance: {self.__distance}, Vitesse Droit: {self.__vitesse_moteur_droit}, " \
               f"Vitesse Gauche: {self.__vitesse_moteur_gauche})"