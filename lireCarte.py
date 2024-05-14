from configparser import ConfigParser
from math import floor

#Lecture du fichier de la carte
config = ConfigParser()
config.read('carte.ini')

#Nombre de feux et de tronçons. id commençant à 1 et finissant à 29
nb_feux = config.getint('generalInfo','nbTrafficLight')
nb_troncons =  config.getint('generalInfo','nbHops')

# On récupère tous les tronçons de la carte.
def getTroncons():

    troncons = dict()

    for i in range(1,nb_troncons+1):
        x = config.get('trip',str(i)).split(',')
        troncons[str(i)] = x

    return troncons

# On récupère tous les feux tricolores de la carte.
def getLights():

    light = dict()

    for i in range(1,nb_feux+1):
        x = config.get('trafficLight',str(i)).split(',')
        light[str(i)] = x

    return light

# On regarde si une position X et Y correspond à un feu dans une liste de feux tricolores.
def isLight(posX,posY,light):

    res = "-1"
    for feu in light:
        if (posX == int(light[feu][0]) and posY == int(light[feu][1])):
            res = feu

    return str(res)

# On regarde si les positions X et Y données correspondent à un tronçon (on rappelle que un troncon est caractérisé par deux positions X et Y de début de troncon et deux positions X et Y de fin de troncons. Voir carte.ini pour le format)
def validerTroncon(posXt,posYt,posXobj,posYobj,lTroncons):

    idTroncon="-1"
    for troncon in lTroncons:
        if (posXt == int(lTroncons[troncon][0]) and posYt == int(lTroncons[troncon][1]) and posXobj == int(lTroncons[troncon][2]) and posYobj == int(lTroncons[troncon][3])):
            idTroncon = troncon

    return idTroncon


#TESTS:
#getTroncons()
#print(isLight(20,10,getLights()))
#print(getLights())
#print(validerTroncon(60,90,70,90,getTroncons()))