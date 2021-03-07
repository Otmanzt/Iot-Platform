#e2e encryption

import random
import time

import secrets
import scrypt

import base64

import os
import os.path

from paho.mqtt import client as mqtt_client
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

broker = 'mqttgroupthree.cloud.shiftr.io'
port = 1883
username = 'mqttgroupthree'
password = 'AWjxTOFOIULLmgF9'

def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

def load_key():
    return open("secret.key", "rb").read()

def encrypt_message(message, key):

    encoded_message = message.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(encoded_message)

    return encrypted_message

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

def publish(client, msg, topic, key):

    while True:
        time.sleep(1)

        cif_msg = encrypt_message(msg, key)
        result = client.publish(topic, cif_msg)

        status = result[0]
        if status == 0:
            print(f"Send encrypted message '{msg}' to topic '{topic}'")
        else:
            print(f"Failed to send message to topic {topic}")
            

def run():

    print("Please write the platform public key, the value of p and the value of alpha.")
    platformPublicKey = input()
    deviceP = input()
    deviceAlpha = input()
    
    deviceID = random.randint(0, 1000)
    
    deviceSecretKey = random.randint(0, 1000)   
    devicePartialKey = (int(deviceAlpha)**int(deviceSecretKey))%int(deviceP)
    
    print("The ID client is: "+str(deviceID)+" and the public key is "+str(devicePartialKey)) 
    input("Press Enter to continue...")
    
    key = (int(platformPublicKey)**int(deviceSecretKey))%int(deviceP)
    key = str(key)
    
    salt = os.urandom(16)
    print(salt)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=str.encode("0"), iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(key))
    
    client_id = f'client-{deviceID}'

    msg = 'Test'
    topic = "/topic"+str(deviceID)

    client = connect_mqtt(client_id)
    client.loop_start()
    publish(client, msg, topic, key)

if __name__ == '__main__':
    run()