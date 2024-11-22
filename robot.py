from capteur import Capteur
from dao_mesure import DAOMesure
import math

class Robot:
    def __init__(self, x: int = 0, y: int = 0, angle: int = 0, map_image=None):
        self.__x = x
        self.__y = y
        self.__angle = angle
        self.__vitesse = 0.0
        self.__acceleration = 0.5
        self.__vitesse_max = 1.0
        self.__vitesse_moteur_droit = 0.0
        self.__vitesse_moteur_gauche = 0.0
        self.capteur = Capteur(self, map_image)
        self.dao_mesure = DAOMesure()
        self.__en_deplacement = False

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def angle(self):
        return self.__angle

    @property
    def vitesse_moteur_droit(self):
        return self.__vitesse_moteur_droit

    @property
    def vitesse_moteur_gauche(self):
        return self.__vitesse_moteur_gauche

    def update_moteurs(self):
        if not self.__en_deplacement:
            self.__vitesse_moteur_droit = 0.0
            self.__vitesse_moteur_gauche = 0.0

    def avancer(self, distance_avance_possible=True):
        if not distance_avance_possible:
            return
        self.__en_deplacement = True
        if self.__vitesse < self.__vitesse_max:
            self.__vitesse = min(self.__vitesse + self.__acceleration, self.__vitesse_max)

        self.__vitesse_moteur_droit = self.__vitesse
        self.__vitesse_moteur_gauche = self.__vitesse

        dx = self.__vitesse * math.cos(math.radians(self.__angle))
        dy = self.__vitesse * math.sin(math.radians(self.__angle))
        self.__x += dx
        self.__y += dy

    def reculer(self):
        self.__en_deplacement = True
        if self.__vitesse > -self.__vitesse_max:
            self.__vitesse = max(self.__vitesse - self.__acceleration, -self.__vitesse_max)

        self.__vitesse_moteur_droit = self.__vitesse
        self.__vitesse_moteur_gauche = self.__vitesse

        dx = self.__vitesse * math.cos(math.radians(self.__angle))
        dy = self.__vitesse * math.sin(math.radians(self.__angle))
        self.__x += dx
        self.__y += dy

    def tourner_gauche(self, facteur_vitesse=1.0):
        self.__en_deplacement = True
        self.__angle = (self.__angle - 5) % 360
        self.__vitesse_moteur_droit = self.__vitesse_max * facteur_vitesse
        self.__vitesse_moteur_gauche = 0.0

    def tourner_droite(self, facteur_vitesse=1.0):
        self.__en_deplacement = True
        self.__angle = (self.__angle + 5) % 360
        self.__vitesse_moteur_droit = 0.0
        self.__vitesse_moteur_gauche = self.__vitesse_max * facteur_vitesse

    def ne_rien_faire(self):
        self.__en_deplacement = False
        self.update_moteurs()

    def arreter(self):
        self.__en_deplacement = False
        self.__vitesse = 0.0
        self.update_moteurs()