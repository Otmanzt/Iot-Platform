import random
import time

import secrets
import scrypt

import os.path

from paho.mqtt import client as mqtt_client
from cryptography.fernet import Fernet

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.asymmetric.dh import DHParameterNumbers
from cryptography.hazmat.primitives.serialization import load_pem_parameters

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

import base64

broker = 'mqttgroupthree.cloud.shiftr.io'
port = 1883
username = 'mqttgroupthree'
password = 'AWjxTOFOIULLmgF9'

deviceList = {}

def generate_key():
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)

def load_key():
    return open("secret.key", "rb").read()

def encrypt_message(message):

    key = load_key()
    encoded_message = message.encode()
    f = Fernet(key)
    encrypted_message = f.encrypt(encoded_message)

    return encrypted_message

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

            
def publish(client, msg, topic):

    while True:
        time.sleep(1)

        cif_msg = encrypt_message(msg)
        result = client.publish(topic, cif_msg)

        status = result[0]
        if status == 0:
            print(f"Send encrypted message '{msg}' to topic '{topic}'")
        else:
            print(f"Failed to send message to topic {topic}")
            

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

    randomNumber = random.randint(0, 1000)
    client_id = f'client-platform-{randomNumber}'

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
    
            parameters = dh.generate_parameters(generator=2, key_size=512,backend=default_backend())
    
            #Generate private keys.
            a_private_key = parameters.generate_private_key()
            a_public_key = a_private_key.public_key()

            print("Esta es mi clave privada: %d"%a_private_key.private_numbers().x)
            print("Esta es mi clave pública: %d"%a_public_key.public_numbers().y)

            params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
            params_b = load_pem_parameters(params_pem, backend=default_backend())

            b_private_key = params_b.generate_private_key()
            b_public_key = b_private_key.public_key()

            print("Esta es tu clave privada: %d"%b_private_key.private_numbers().x)
            print("Esta es tu clave pública: %d"%b_public_key.public_numbers().y)

            a_shared_key = a_private_key.exchange(b_public_key)
            b_shared_key = b_private_key.exchange(a_public_key)

            print("a_shared_key: " + str(a_shared_key))
            print("b_shared_key: " + str(b_shared_key))
           
            derived_key = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=None,
                info=b'handshake data',
            ).derive(a_shared_key)
           
            key = base64.urlsafe_b64encode(derived_key)
           
            message="Test"
            encoded_message = message.encode()
            f = Fernet(key)
            encrypted_message = f.encrypt(encoded_message)
            
            decrypted_message = f.decrypt(encrypted_message)

            print(decrypted_message.decode())
            
            #deviceList[1] = key

if __name__ == '__main__':
    run()