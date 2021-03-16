from paho.mqtt import client as mqtt_client
from paquetes.keyUtils import *
import time

broker = 'mqttgroupthree.cloud.shiftr.io'
port = 1883
username = 'mqttgroupthree'
password = 'AWjxTOFOIULLmgF9'

class Mqtt:
    @staticmethod
    def connect_mqtt(client_id):
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Conectado al broker!")
            else:
                print("Fallo al conectar, código %d\n", rc)

        client = mqtt_client.Client(client_id)
        client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.connect(broker, port)
        return client

    @staticmethod
    def publish(client, msg, topic, key=None):

        result = client.publish(topic, msg)

        status = result[0]
        if status == 0:
            if "message" in topic:
                if len(msg) >= 20:
                    print(f"Mensaje '{msg[1:20]}'... enviado al topic '{topic}'")
                else:
                    print(f"Mensaje '{msg}' enviado al topic '{topic}'")
        else:
            print(f"Fallo al enviar el mensaje al topic {topic}")
