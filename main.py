import keyboard
import time
import cv2
from robot import Robot


def main():
    map_image_path = "map_image.png"
    map_image = cv2.imread(map_image_path, cv2.IMREAD_GRAYSCALE)

    if map_image is None:
        print(f"Erreur : Impossible de charger l'image de la carte '{map_image_path}'.")
        return

    robot = Robot(x=100, y=100, angle=0, map_image=map_image)

    print("Utilisez les flèches directionnelles pour déplacer le robot. Appuyez sur 'esc' pour quitter.")

    while True:
        mesure = robot.capteur.capte()
        print(mesure)

        distance_avance_possible = mesure.distance > 0

        avancer = keyboard.is_pressed('up')
        reculer = keyboard.is_pressed('down')
        gauche = keyboard.is_pressed('left')
        droite = keyboard.is_pressed('right')

        if avancer and reculer:
            robot.ne_rien_faire()
        elif avancer and gauche:
            robot.avancer(distance_avance_possible)
            robot.tourner_gauche(facteur_vitesse=0.5)
        elif avancer and droite:
            robot.avancer(distance_avance_possible)
            robot.tourner_droite(facteur_vitesse=0.5)
        elif reculer and gauche:
            robot.reculer()
            robot.tourner_gauche(facteur_vitesse=0.5)
        elif reculer and droite:
            robot.reculer()
            robot.tourner_droite(facteur_vitesse=0.5)
        elif avancer:
            robot.avancer(distance_avance_possible)
        elif reculer:
            robot.reculer()
        elif gauche:
            robot.tourner_gauche()
        elif droite:
            robot.tourner_droite()
        else:
            robot.ne_rien_faire()

        if keyboard.is_pressed('esc'):
            print("Programme terminé par l'utilisateur.")
            break

        time.sleep(0.1)


if __name__ == "__main__":
    main()