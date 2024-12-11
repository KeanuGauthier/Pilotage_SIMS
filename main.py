import keyboard
import time
import cv2
from robot import Robot
from database import Database

def main():
    map_image_path = "map_image.png"
    map_image = cv2.imread(map_image_path, cv2.IMREAD_GRAYSCALE)

    if map_image is None:
        print(f"Erreur : Impossible de charger l'image de la carte '{map_image_path}'.")
        return

    db = Database()
    db.clear_table()

    robot = Robot(x=100, y=100, angle=0, map_image=map_image)

    print("Utilisez les flèches directionnelles pour déplacer le robot. Appuyez sur 'esc' pour quitter.")

    try:
        while True:
            # Capture les données du capteur
            mesure = robot.capteur.capte()
            print(mesure)
            db.insert_mesure(mesure)

            # Détection des touches
            avancer = keyboard.is_pressed('up')
            reculer = keyboard.is_pressed('down')
            gauche = keyboard.is_pressed('left')
            droite = keyboard.is_pressed('right')

            # Logique des mouvements du robot
            if avancer and reculer:
                robot.ne_rien_faire()
            elif avancer and gauche and mesure.distance0 > 11:
                robot.tourner_gauche(avancer=True)
            elif avancer and droite and mesure.distance0 > 11:
                robot.tourner_droite(avancer=True)
            elif reculer and gauche:
                robot.tourner_gauche(reculer=True)
            elif reculer and droite:
                robot.tourner_droite(reculer=True)
            elif avancer and mesure.distance0 > 11:
                robot.avancer()
            elif reculer:
                robot.reculer()
            elif gauche:
                robot.tourner_gauche()
            elif droite:
                robot.tourner_droite()
            else:
                robot.ne_rien_faire()

            # Quitter le programme
            if keyboard.is_pressed('esc'):
                print("Programme terminé par l'utilisateur.")
                break

            time.sleep(0.03)
    finally:
        db.close()

if __name__ == "__main__":
    main()