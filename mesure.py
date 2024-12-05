class Mesure:
    def __init__(self, id, x, y, date_heure, angle, distance0, distance1, distance2, distance3, distance4,
                 vitesse_moteur_droit, vitesse_moteur_gauche):
        self.id = id
        self.x = x
        self.y = y
        self.date_heure = date_heure
        self.angle = angle
        self.distance0 = distance0
        self.distance1 = distance1
        self.distance2 = distance2
        self.distance3 = distance3
        self.distance4 = distance4
        self.vitesse_moteur_droit = vitesse_moteur_droit
        self.vitesse_moteur_gauche = vitesse_moteur_gauche

    def __str__(self):
        return (f"Mesure(ID: {self.id}, X: {self.x}, Y: {self.y}, Angle: {self.angle}, "
                f"Distance0: {self.distance0}, Distance1: {self.distance1}, Distance2: {self.distance2}, "
                f"Distance3: {self.distance3}, Distance4: {self.distance4}, Vitesse Droit: {self.vitesse_moteur_droit}, "
                f"Vitesse Gauche: {self.vitesse_moteur_gauche})")


