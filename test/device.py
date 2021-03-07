<<<<<<< HEAD
#e2e encryption

=======
>>>>>>> 1d98aa7edb22776e3cf4d31c74ea1ba3824a7ec1
import random
import time

import secrets
import scrypt

<<<<<<< HEAD
import base64

import os
=======
>>>>>>> 1d98aa7edb22776e3cf4d31c74ea1ba3824a7ec1
import os.path

from paho.mqtt import client as mqtt_client
from cryptography.fernet import Fernet
<<<<<<< HEAD
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
=======
>>>>>>> 1d98aa7edb22776e3cf4d31c74ea1ba3824a7ec1

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

<<<<<<< HEAD
def encrypt_message(message, key):

=======
def encrypt_message(message):

    key = load_key()
>>>>>>> 1d98aa7edb22776e3cf4d31c74ea1ba3824a7ec1
    encoded_message = message.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(encoded_message)

    return encrypted_message

<<<<<<< HEAD
=======
def decrypt_message(encrypted_message):

    key = load_key()
    f = Fernet(key)
    decrypted_message = f.decrypt(encrypted_message)

    return decrypted_message.decode()

>>>>>>> 1d98aa7edb22776e3cf4d31c74ea1ba3824a7ec1
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

<<<<<<< HEAD
def publish(client, msg, topic, key):
=======
def publish(client, msg, topic):
>>>>>>> 1d98aa7edb22776e3cf4d31c74ea1ba3824a7ec1

    while True:
        time.sleep(1)

<<<<<<< HEAD
        cif_msg = encrypt_message(msg, key)
=======
        cif_msg = encrypt_message(msg)
>>>>>>> 1d98aa7edb22776e3cf4d31c74ea1ba3824a7ec1
        result = client.publish(topic, cif_msg)

        status = result[0]
        if status == 0:
            print(f"Send encrypted message '{msg}' to topic '{topic}'")
        else:
            print(f"Failed to send message to topic {topic}")
            

<<<<<<< HEAD
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
=======
def subscribe(client: mqtt_client, topic):
    def on_message(client, userdata, msg):
        print(f"Received '{decrypt_message(msg.payload)}' from '{msg.topic}' topic")

    client.subscribe(topic)
    client.on_message = on_message

def run():


    option = -1
    task = -1
    topicOption = -1
    changekey = -1

    while changekey != "0" and changekey != "1" and os.path.isfile("secret.key"):
        print("Do you want to generate another key? (0/1)")
        changekey = input()

    if changekey == "1" or os.path.isfile("secret.key") == False:
        print("Generating a new Fender key...")
        generate_key()

    while option != "0" and option != "1":
        print("Are you an IoT platform (Enter 0) or IoT Device (Enter 1)?")
        option = input()

    if option == "0":
        client_id = f'client-platform'

        while task != "0" and task != "1":
            print("What do you want to do?")
            print("0 - Select topics to listen.")
            print("1 - List devices. (NOT  IMPLEMENTED YET)")
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

    if option == "1":
        randomNumber = random.randint(0, 1000)
        client_id = f'client-{randomNumber}'
        msg = 'Test'
        topic = "/topic"+str(randomNumber)

        client = connect_mqtt(client_id)
        client.loop_start()
        publish(client, msg, topic)
>>>>>>> 1d98aa7edb22776e3cf4d31c74ea1ba3824a7ec1

if __name__ == '__main__':
    run()