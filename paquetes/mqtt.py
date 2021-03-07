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
                print("Connected to MQTT Broker!")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(client_id)
        client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.connect(broker, port)
        return client

    @staticmethod
    def publish(client, msg, topic, key=None):
        if key is not None:
            msg = KeyUtils.encrypt_message(msg, key)

        result = client.publish(topic, msg)

        status = result[0]
        if status == 0:
            print(f"Send encrypted message '{msg}' to topic '{topic}'")
        else:
            print(f"Failed to send message to topic {topic}")

    @staticmethod
    def subscribe(client: mqtt_client, topic, key=None):
        def on_message(client, userdata, msg):
            if key is not None:
                print(f"Received '{KeyUtils.decrypt_message(msg.payload,key)}' from '{msg.topic}' topic")
            else:
                print(f"Received '{msg.payload}' from '{msg.topic}' topic")
            return msg.payload

        client.subscribe(topic)
        client.on_message = on_message
