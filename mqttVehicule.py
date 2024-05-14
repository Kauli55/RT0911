import paho.mqtt.client as mqtt
import time
import iniVehicule as vehic
import lireCarte as lCarte
import json


# MQTT broker details
addresse = "194.57.103.203"  # Adresse publique du broker MQTT générant les files.
port = 1883  # Port par défaut
topic = "vehicle"  # Nom de la file pour envoyer les données de notre véhicule
topic2 = "positions" # Nom de la file pour récupérer les informations de tous les véhicules présents sur la carte. Rafraîchit régulièrement par le broker MQTT.
topic3 = "lights" # Nom de la file pour récupérer les informations de tous les feux tricolores présents sur la carte. Rafraîchit régulièrement par le borker MQTT.
topic4 = "top" # Nom de la file émettant le top départ.
topic5 = "UT" # Nom de la file demandant les données de l'Upper Tester d'un véhicule
topic6 = "RESP" # Nom de la file où un véhicule enverra ses données d'Upper Tester au broker MQTT.

#Création du client MQTT et initialisation des données
client = mqtt.Client()

feux = {}
posVehicules={}
top= {}
ut={}
iden=4
start = 0
posFeux = lCarte.getLights()

#Comportement lors de la connexion au broker MQTT.
#Ici, on ira donc s'abonner à toutes les files du broker MQTT.
def on_connect(client, userdata, flags, rc):
    print("Connection réussie. CODE : " + str(rc))
    client.subscribe(topic)
    client.subscribe(topic2)
    client.subscribe(topic3)
    client.subscribe(topic4)
    client.subscribe(topic5)
    client.subscribe(topic6)

#Fonction permettant de récupérer les données demandées par l'Upper Tester quand nous recevons un message demandant celles-ci
def traiterUT():
    #On récupère le temps local pour le fournir au broker MQTT.
    temps = time.time() - start
    #On récupère les informations de notre véhicule.
    with open("./vehicule.json", 'r', encoding="utf-8") as file:
        data = json.load(file)
        ident = data["id"]
        pos = data["posActu"].split(",")
    #On isole les positions X et Y afin d'être conforme au format imposé par le broker MQTT.
    valX = int(pos[0])
    valY = int(pos[1])

    #On se mets au format demandé par le broker MQTT.
    msg = {"id":str(ident),
           "temps":temps,
           "x":valX,
           "y":valY}

    msg = json.dumps(msg)

    return msg

#Comportement lors de la réception d'un message d'une file dans laquelle nous sommes abonnés.
def on_message(client, userdata, message):
    #On regarde sur quelle file nous venons de recevoir un message.
    match message.topic:
        #Cas des feux tricolores
        case "lights":
            #Mise à jour des données locales des feux sur la carte. (Leurs états.)
            feux = json.loads(message.payload.decode())
            print(f"Message du topic '{message.topic}' : '{message.payload.decode()}'")
        #Cas de la position des véhicules
        case "positions":
            #Mise à jour des données locales des différents véhicules sur la carte.
            posVehicules = json.loads(message.payload.decode())
            print(f"Message du topic '{message.topic}' : '{message.payload.decode()}'")
        #Cas du top départ
        case "top":
            top["oui"] = "non"
        #Cas de l'upper tester
        case "UT":
            ut = json.loads(message.payload.decode())
            #Si le message nous est adressé, alors nous fournissons les informations et les envoyons sur la file RESP.
            if ut["id"]==iden:
                message_to_publish = traiterUT()
                client.publish(topic6, message_to_publish)
            print(f"Message du topic '{message.topic}' : '{message.payload.decode()}'")
        #Cas autre où l'on affichera uniquement le message, sans faire de traitement interne.
        case _:
            print(f"Message reçu : '{message.payload.decode()}' du topic '{message.topic}'")

#Fonction permettant de récupérer les données du json messageVehicule pour le mettre en format str.
#Ce message sera bien formatté afin qu'il puisse être lu par le broker MQTT.
def jsonDataToString():

    with open("./messageVehicule.json", 'r') as file:
        data = json.load(file)

    msg=json.dumps(data)

    return msg

# On établit le comportement lorsque l'on se connecte au broker MQTT et lorsque nous recevons un message de celui-ci.
client.on_connect = on_connect
client.on_message = on_message

# Connexion au broker MQTT :
client.connect(addresse, port, 60)
#On crée une boucle afin de récupérer les nouveaux messages. Cela permet de ne pas se déconnecter directement après avoir envoyé ou lu un message.
client.loop_start()

# On attend un moment afin de s'assurer que la connexion s'établisse bien.
time.sleep(2)

#Création de notre véhicule.
vit=5
direction=0
vtype=1
posX=0
posY=0
itineraire=["0,0","0,10","20,10","40,10","40,20","40,30","60,30"]
vehic.initialiserVehicule(iden, vit, vtype, direction, posX, posY, itineraire)
message_to_publish = jsonDataToString()


#Pour les positions : {"1":{"id":1,"vtype":1,...},"29":{"id":29,...},...}
#Pour les lights : {"1": "0,0,0,0","2": "0,1,1,0",...,"29": "0,0,0,0"}

# Boucle principale permettant d'envoyer des messages régulièrement
try:
    # Comportement avant le top départ
    attente = 0
    #Tant que nous ne recevons pas de top (et que donc que notre liste top est vide)
    while (attente==0):
        if len(top)>0:
            attente=1
            start=time.time()
            print("Top Départ.")

    #On envoie nos informations sur la file "vehicle"
    client.publish(topic, message_to_publish)
    while True:
        time.sleep(1)
        #Tant que notre vitesse est différente de 0, alors il faut bouger le véhicule.
        if vit != 0:
            vehic.bougerVehicule()
        
        #On récupère les données du véhicule après avoir bougé. (Même si nous n'avons pas bougé.)
        donnee = vehic.getDataMsg()

        #Condition pour regarder si nous sommes éventuellement sur une intersection (dans ce cas il faudra regarder les feux tricolores.)
        if (int(donnee["x"])%10==0 and int(donnee["y"])%10==0):
            #On regarde si nous sommes à un feu.
            stop = lCarte.isLight(donnee["x"],donnee["y"],posFeux)
            if stop != "-1" :
                #Si le broker MQTT ne nous a donné aucune information sur les feux tricolores depuis notre connexion, alors on considère que tous les feux sont rouges.
                #Rappel : si un feu a une valeur égale à 0, alors ce feu est rouge. Sinon, le feu est vert.
                if len(feux)==0:
                    feuActuel = "0,0,0,0"
                else:
                    feuActuel = feux[stop]
                #On récupère l'état du feu tricolore où nous nous situons
                etatsFeu = feuActuel.split(",")
                #On récupère notre direction actuelle afin de voir quel feu nous devons regarder.
                match donnee["dir"]:
                    case 0: # Direction du véhicule : EST
                        if etatsFeu[2]=="0": # Direction du feu à regarder : OUEST
                            vit=0
                        else:
                            vit=5
                    case 1: # Direction du véhicule : NORD
                        if etatsFeu[3]=="0": # Direction du feu à regarder : SUD
                            vit=0
                        else:
                            vit=5
                    case 2: # Direction du véhicule : OUEST
                        if etatsFeu[0]=="0": # Direction du feu à regarder : EST
                            vit=0
                        else:
                            vit=5
                    case 3: # Direction du véhicule : SUD
                        if etatsFeu[1]=="0": # Direction du feu à regarder : NORD
                            vit=0
                        else:
                            vit=5

        #On met à jours les données à envoyer.
        vehic.infoJSONVehicule()
        message_to_publish = jsonDataToString()
        client.publish(topic, message_to_publish)
#Sortie de la boucle uniquement en utilisant Ctrl + C
except KeyboardInterrupt:
    # On se déconnecte de la file en utilisant Ctrl + C
    client.disconnect()
    client.loop_stop()
    print("Déconnexion du MQTT.")