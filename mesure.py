class Mesure:
    def __init__(self, id, x, y, date_heure, angle, distance0, distance1, distance2, distance3, distance4,
                 vitesse_moteur_droit, vitesse_moteur_gauche):
        # Identifiant unique pour distinguer chaque mesure
        self.id = id
        # Position du robot au moment de la mesure
        self.x = x
        self.y = y
        # Horodatage exact de la mesure
        self.date_heure = date_heure
        # Orientation du robot au moment de la mesure
        self.angle = angle
        # Distances mesurées par les capteurs dans différentes directions
        self.distance0 = distance0
        self.distance1 = distance1
        self.distance2 = distance2
        self.distance3 = distance3
        self.distance4 = distance4
        # Vitesses actuelles des moteurs droit et gauche du robot
        self.vitesse_moteur_droit = vitesse_moteur_droit
        self.vitesse_moteur_gauche = vitesse_moteur_gauche

    def __str__(self):
        # Génère une représentation lisible de l'objet pour faciliter le débogage et le suivi
        return (f"Mesure(ID: {self.id}, X: {self.x}, Y: {self.y}, Angle: {self.angle}, "
                f"Distance0: {self.distance0}, Distance1: {self.distance1}, Distance2: {self.distance2}, "
                f"Distance3: {self.distance3}, Distance4: {self.distance4}, Vitesse Droit: {self.vitesse_moteur_droit}, "
                f"Vitesse Gauche: {self.vitesse_moteur_gauche})")