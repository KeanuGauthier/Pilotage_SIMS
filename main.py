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
            mesure = robot.capteur.capte()  # Capture une mesure des distances avec les obstacles
            print(mesure)  # Affiche les données de mesure dans la console
            db.insert_mesure(mesure)  # Enregistre la mesure dans la base de données MySQL

            # Lecture des touches pour contrôler les mouvements du robot
            avancer = keyboard.is_pressed('up')
            reculer = keyboard.is_pressed('down')
            gauche = keyboard.is_pressed('left')
            droite = keyboard.is_pressed('right')

            # Conditions pour les actions du robot en fonction des touches pressées
            if avancer and reculer:
                robot.ne_rien_faire()  # Annule le mouvement si les touches avancée et reculée sont pressées simultanément
            elif avancer and gauche and mesure.distance0 > 11:
                robot.tourner_gauche(avancer=True)  # Tourne à gauche tout en avançant si la voie est dégagée
            elif avancer and droite and mesure.distance0 > 11:
                robot.tourner_droite(avancer=True)  # Tourne à droite tout en avançant si la voie est dégagée
            elif reculer and gauche:
                robot.tourner_gauche(reculer=True)  # Tourne à gauche tout en reculant
            elif reculer and droite:
                robot.tourner_droite(reculer=True)  # Tourne à droite tout en reculant
            elif avancer and mesure.distance0 > 11:
                robot.avancer()  # Avance si aucun obstacle n'est détecté directement devant
            elif reculer:
                robot.reculer()  # Recule
            elif gauche:
                robot.tourner_gauche()  # Tourne à gauche
            elif droite:
                robot.tourner_droite()  # Tourne à droite
            else:
                robot.ne_rien_faire()  # Reste immobile si aucune touche n'est pressée

            # Quitte la boucle lorsque la touche 'esc' est pressée
            if keyboard.is_pressed('esc'):
                print("Programme terminé par l'utilisateur.")
                break

            time.sleep(0.03)
    finally:
        db.close()

if __name__ == "__main__":
    main()