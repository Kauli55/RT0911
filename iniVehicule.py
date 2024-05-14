import json
import lireCarte as lCarte

#On récupère la liste des troncons.
troncon = lCarte.getTroncons()

#Fonction permettant de vérifier si les valeurs du trajet donnés sont valides, c'est-à-dire que tous les troncons parcourus par le véhicule sont valides.
def valTroncons(liste):

    res = True

    for i in range(0,len(liste)-1):
        tron=liste[i].split(',')
        tron.extend(liste[i+1].split(','))
        a = lCarte.validerTroncon(int(tron[0]),int(tron[1]),int(tron[2]),int(tron[3]),troncon)

        if (a == "-1"):
            res = False
            break

    return res

#Création fichier du vehicule initial.
# 1 --> Réussite
# -1 --> Fail
def initialiserVehicule(identifiant:int,vitesse:int,v_type:int,dire:int,posX:int,posY:int,itineraire:list):
    testTroncon = valTroncons(itineraire)
    code = 1
    if testTroncon == True:
        pos = str(posX)+","+str(posY)
        #Toutes les données demandées pour un véhicule.
        data = {
            "id":identifiant,
            "vtype":v_type,
            "start":pos,
            "posActu":pos,
            "dir":dire,
            "speed":vitesse,
            "etapeActu":0,
            "hop":len(itineraire),
            "hops":itineraire
            }
        #On écrit les données dans le fichier "vehicule.json"
        with open("./vehicule.json", 'w+', encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    else:
        code = -1
    return code

# Fonction permettant la création d'un fichier nommé "messageVehicule.json" qui est au foSSrmat demandé par le broker MQTT.
def infoJSONVehicule():

    with open("./vehicule.json", 'r', encoding="utf-8") as file:
        data = json.load(file)
        ident = data["id"]
        pos = data["posActu"].split(",")
        vitesse = data["speed"]
        direction = data["dir"]
        typeVehicule = data["vtype"]

        #On formatte les données pour qu'elles respectent le format demandé par le broker MQTT.
        donnee = {
            "id":str(ident),
            "vtype":int(typeVehicule),
            "x":int(pos[0]),
            "y":int(pos[1]),
            "dir":int(direction),
            "speed":int(vitesse)
            }

    # On écrit le tout dans le fichier "messageVehicule.json"
    with open("./messageVehicule.json", 'w+', encoding="utf-8") as file:
        json.dump(donnee, file, indent=4)

    return 1

# Fonction permettant de vérifier si les coordonnées données sont dans la carte.
def verifCoordonnees(posX:int,posY:int):
    valide=True
    if (posX<0 or posX>100):
        valide=False
    elif (posY<0 or posY>100):
        valide=False
    return valide

# Fonction permettant la création d'un dictionnaire reflétant l'état du véhicule dans le fichier "vehicule.json"
def getDataMsg():
    
    #Récupération des données
    with open("./vehicule.json", 'r', encoding="utf-8") as file:
        data = json.load(file)
        ident = data["id"]
        vtype = data["vtype"]
        pos = data["posActu"].split(",")
        direction = data["dir"]
        vitesse = data["speed"]
    
    #Création du dictionnaire
    retour = {
            "id":str(ident),
            "vtype":int(vtype),
            "x":int(pos[0]),
            "y":int(pos[1]),
            "dir":int(direction),
            "speed":int(vitesse)
            }
    
    return retour

# Fonction permettant de bouger le véhicule. Elle respecte toutes les règles demandées (Ne sors pas des troncons, respecte la vitesse, change de direction quand nécessaire.)
def bougerVehicule():
    retour = 1
    
    #Trouver son étape actuelle + récupération de la position :
    with open("./vehicule.json", 'r', encoding="utf-8") as file:
        data = json.load(file)
        numeroEtape = data["etapeActu"]
        itineraire = data["hops"]
        vitesse = data["speed"]
        #On regarde si le véhicule n'est pas déjà à sa destination.
        if numeroEtape>=data["hop"]:
            retour = 2
        else:
            posCible = itineraire[numeroEtape]
            posActu = data["posActu"]
            pos = posCible.split(",")
            posX = int(pos[0])
            posY = int(pos[1])
            posA = posActu.split(",")
            posXactu = int(posA[0])
            posYactu = int(posA[1])
            direction = data["dir"]

    if retour == 1:
        #Vérification des coordonnées de la destination.
        if (verifCoordonnees(posX, posY)==False):
            raise Exception("Erreur : destination incorrecte. posX et posY sont en dehors de la carte.")
            
        #Calcul de la nouvelle position à atteindre.
        #Hop a forcément un X ou Y en commun avec position actuelle. Dans ce cas là, il faudra modifier le X ou Y qui n'est pas commun.
        if (posX==posXactu):
            
            #Cas où objectif posY > posYactu
            if (posY>posYactu):
                #Il ne faudra modifier que posY dans ce cas là
                if (posYactu + vitesse)>=posY:
                    posYactu=posY
                    numeroEtape = numeroEtape + 1
                else :
                    posYactu=posYactu + vitesse
                direction=1 #Nord
            #Cas où objectif posY < posYactu
            else:
                if (posYactu - vitesse)<=posY:
                    posYactu=posY
                    numeroEtape = numeroEtape + 1
                else :
                    posYactu=posYactu - vitesse
                direction=3 #Sud
        elif (posY==posYactu):
            #Cas où objectif posX > posXactu
            if (posX>posXactu):
                #Il ne faudra modifier que posX dans ce cas là
                if (posXactu + vitesse)>=posX:
                    posXactu=posX
                    numeroEtape = numeroEtape + 1
                else:
                    posXactu=posXactu + vitesse
                direction=0 #Est
            #Cas où objectif posX < posXactu
            else:
                if (posXactu - vitesse)<=posX:
                    posXactu=posX
                    numeroEtape = numeroEtape + 1
                else:
                    posXactu=posXactu - vitesse
                direction = 2 #Ouest
        else:
            raise Exception("Erreur : destination incorrecte. posX et posY ne donnent pas une intersection.")
        
        #Insertion des nouvelles coordonnées dans le json
        nouvPosActu=str(posXactu)+","+str(posYactu)
        data["posActu"]=nouvPosActu
        data["etapeActu"]=numeroEtape
        data["dir"]=direction
        with open("./vehicule.json", 'w+', encoding="utf-8") as file:
            json.dump(data, file, indent=4)
    
    return retour
