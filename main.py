import keyboard
import time
import cv2
from robot import Robot


def main():
    map_image_path = "map_image.png"  # Remplacez par le chemin correct de votre image
    map_image = cv2.imread(map_image_path, cv2.IMREAD_GRAYSCALE)

    if map_image is None:
        print(f"Erreur : Impossible de charger le fichier {map_image_path}")
        return

    robot = Robot(x=100, y=100, angle=0, map_image=map_image)

    print("Utilisez les flèches directionnelles pour déplacer le robot. Appuyez sur 'esc' pour quitter.")

    while True:
        mesure = robot.capteur.capte()
        print(mesure)

        if keyboard.is_pressed('up'):
            robot.avancer()
        elif keyboard.is_pressed('down'):
            robot.reculer()
        elif keyboard.is_pressed('left'):
            robot.tourner_gauche()
        elif keyboard.is_pressed('right'):
            robot.tourner_droite()
        else:
            robot.ne_rien_faire()

        if keyboard.is_pressed('esc'):
            print("Programme terminé par l'utilisateur.")
            break

        time.sleep(0.1)


if __name__ == "__main__":
    main()