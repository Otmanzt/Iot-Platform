#e2e encryption

import random
import time

import secrets
import scrypt

import base64

import os.path

from paho.mqtt import client as mqtt_client
from cryptography.fernet import Fernet

broker = 'mqttgroupthree.cloud.shiftr.io'
port = 1883
username = 'mqttgroupthree'
password = 'AWjxTOFOIULLmgF9'

deviceList = {}

def decrypt_message(encrypted_message):

    key = load_key()
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message)

    return decrypted_message.decode()

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

def subscribe(client: mqtt_client, topic):
    def on_message(client, userdata, msg):
    
        deviceID = msg.topic[5:]
        key = deviceList.get(deviceID)
        msg_decrypt = decrypt_message(msg.payload, key)
        print(f"Received '{msg_decrypt}' from '{msg.topic}' topic")
        
        
    client.subscribe(topic)
    client.on_message = on_message
            
def run():

    task = -1
    topicOption = -1

    client_id = f'client-platform'

    while task != "0" and task != "1":
        print("What do you want to do?")
        print("0 - Select topics to listen.")
        print("1 - List devices. (NOT  IMPLEMENTED YET)")
        print("2 - Register new device.")
        task = input()

        if task == "0":

            print("Please write the name of topic or 0 if you want to listen all existent topics.")
            topicOption = input()

            if topicOption == "0":
                client = connect_mqtt(client_id)
                subscribe(client, "#")
                client.loop_forever()
            else:
                client = connect_mqtt(client_id)
                subscribe(client, "/"+topicOption)
                client.loop_forever()
                
        if task == "2":

            platformP = random.randint(0, 1000)
            platformAlpha = random.randint(0, 1000)
            platformSecretKey = random.randint(0, 1000)
            
            platformPartialKey = (int(platformAlpha)**int(platformSecretKey))%int(platformP)
            
            print("The platform public key is "+str(platformPartialKey)+" and p = "+str(platformP)+" and alpha = "+str(platformAlpha))
            
            print("Please write the device ID you want to register.")
            deviceID = input()
            
            print("Write the device public key.")
            devicePublicKey = input()

            key = (int(devicePublicKey)**int(platformSecretKey))%int(platformP)
            key = base64.urlsafe_b64decode(key*109034850923845)
            print(key)
            
            deviceList[deviceID] = key

if __name__ == '__main__':
    run()