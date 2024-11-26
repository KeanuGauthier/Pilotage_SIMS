class Mesure:
    def __init__(self, id, x, y, date_heure, angle, distance, vitesse_moteur_droit, vitesse_moteur_gauche):
        self.id = id
        self.x = x
        self.y = y
        self.date_heure = date_heure
        self.angle = angle
        self.distance = distance
        self.vitesse_moteur_droit = vitesse_moteur_droit
        self.vitesse_moteur_gauche = vitesse_moteur_gauche

    def __str__(self):
        return (f"Mesure(ID: {self.id}, X: {self.x}, Y: {self.y}, Angle: {self.angle}, "
                f"Distance: {self.distance}, Vitesse Droit: {self.vitesse_moteur_droit}, "
                f"Vitesse Gauche: {self.vitesse_moteur_gauche})")