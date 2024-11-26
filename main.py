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
    db.clear_table()  # Supprime toutes les données existantes avant de commencer

    robot = Robot(x=100, y=100, angle=0, map_image=map_image)

    print("Utilisez les flèches directionnelles pour déplacer le robot. Appuyez sur 'esc' pour quitter.")

    try:
        while True:
            mesure = robot.capteur.capte()
            print(mesure)
            db.insert_mesure(mesure)  # Insérer la mesure dans la base de données

            avancer = keyboard.is_pressed('up')
            reculer = keyboard.is_pressed('down')
            gauche = keyboard.is_pressed('left')
            droite = keyboard.is_pressed('right')

            # Gestion des combinaisons de touches
            if avancer and reculer:
                robot.ne_rien_faire()  # Si on appuie sur les deux, le robot ne bouge pas
            elif avancer and gauche:
                robot.avancer()
                robot.tourner_gauche(facteur_vitesse=0.5)  # Tourne à gauche en avançant
            elif avancer and droite:
                robot.avancer()
                robot.tourner_droite(facteur_vitesse=0.5)  # Tourne à droite en avançant
            elif reculer and gauche:
                robot.reculer()
                robot.tourner_gauche(facteur_vitesse=0.5)  # Tourne à gauche en reculant
            elif reculer and droite:
                robot.reculer()
                robot.tourner_droite(facteur_vitesse=0.5)  # Tourne à droite en reculant
            elif avancer:
                robot.avancer()
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
    finally:
        db.close()

if __name__ == "__main__":
    main()