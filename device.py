import random
import os.path
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import load_pem_parameters
from paquetes.mqtt import *
from paquetes.keyUtils import *


def subscribe(client: mqtt_client, topic, key=None):
    def on_message(client, userdata, msg):

        if key is not None:
            print(f"Received '{KeyUtils.decrypt_message(msg.payload, key)}' from '{msg.topic}' topic")
        else:
            print(f"Received '{msg.payload.decode()}' from '{msg.topic}' topic")

        client.msg_payload.append(msg.payload.decode())

    client.subscribe(topic)
    client.on_message = on_message

def run():

    option = -1
    task = -1
    topicOption = -1
    changekey = -1

    '''
    while changekey != "0" and changekey != "1" and os.path.isfile("secret.key"):
        print("Do you want to generate another key? (0/1)")
        changekey = input()

    if changekey == "1" or os.path.isfile("secret.key") == False:
        print("Generating a new Fender key...")
        generate_key()
    '''
    
    randomNumber = random.randint(0, 1000)
    client_id = f'client-{randomNumber}'
    
    topic_new_params = "/topic/newConnect/"+client_id+"/params"
    topic_new_pb = "/topic/newConnect/" + client_id + "/public"
    topic_request = "/topic/request"

    client = Mqtt.connect_mqtt(client_id)
    Mqtt.publish(client, client_id, topic_request)  # Topic para enviar la peticion de conexion nueva con la plataform
    client.msg_payload = []

    client.loop_start()
    Mqtt.subscribe(client, topic_new_params)  # Topic para esperar la respuesta con los parametros de la plataforma
    Mqtt.subscribe(client, topic_new_pb)  # Topic para esperar la respuesta con los parametros de la plataforma
    time.sleep(10)
    client.loop_stop()

    params_b = load_pem_parameters(str(client.msg_payload[0]).encode(), backend=default_backend())
    b_private_key = params_b.generate_private_key()
    b_public_key = b_private_key.public_key()
    # Enviar la clave publica del dispositivo por el topic
    print(client.msg_payload[1])
    print(type(client.msg_payload[1]))
    b_shared_key = b_private_key.exchange(client.msg_payload[1].encode())
    print(b_shared_key)
    '''
    ##################################################################################################
    parameters = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())
    params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
    print(params_pem)
    
    a_private_key = parameters.generate_private_key()
    a_public_key = a_private_key.public_key()

    print("Esta es mi clave pública: %d"%a_public_key.public_numbers().y)
    print("Introduce la clave publica de tu compañero")
    b_public_key_number = int(input())

    peer_public_numbers = dh.DHPublicNumbers(b_public_key_number, parameters.parameter_numbers())
    b_public_key = peer_public_numbers.public_key(default_backend())

    key = a_private_key.exchange(b_public_key)

    print("key: " + str(key))
    ##################################################################################################
    '''

if __name__ == '__main__':
    run()
