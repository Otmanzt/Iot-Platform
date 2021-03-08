import random
import os.path
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import load_pem_parameters
from paquetes.mqtt import *
from paquetes.keyUtils import *

randomNumber = random.randint(100, 999)
client_id = f'client-{randomNumber}'


def subscribe(client: mqtt_client, topic, key=None):
    def on_message(client, userdata, msg):

        if msg.topic == "/topic/newConnect/" + client_id + "/params":
            client.params_b = msg.payload.decode()
        if msg.topic == "/topic/newConnect/" + client_id + "/publicPlatform":
            client.a_public_key = int(msg.payload)

    client.subscribe(topic)
    client.on_message = on_message

def run():

    mensaje_recibido = False
    time_out = 20
    time_init = 0

    option = -1
    task = -1
    topicOption = -1
    changekey = -1
    
    # TOPICS
    topic_new_params = "/topic/newConnect/"+client_id+"/params"
    topic_new_pb_plat = "/topic/newConnect/" + client_id + "/publicPlatform"
    topic_new_pb_device = "/topic/newConnect/" + client_id + "/publicDevice"
    topic_request = "/topic/request"   
    topic_message = "/topic/" + client_id + "/message"
    
    # Conexion con MQTT
    client = Mqtt.connect_mqtt(client_id)

    Mqtt.publish(client, client_id, topic_request)  # Topic para enviar la peticion de conexion nueva con la plataform

    client.loop_start()
    subscribe(client, topic_new_params)  # Topic para esperar la respuesta con los parametros de la plataforma
    subscribe(client, topic_new_pb_plat)  # Topic para esperar la respuesta con los parametros de la plataforma
    print("Connecting with platform... Please wait")
    
    while not mensaje_recibido and time_init < time_out:
        if hasattr(client, 'a_public_key') and hasattr(client, 'params_b'):
            mensaje_recibido = True
        time.sleep(1)
        time_init += 1

    client.loop_stop()
    
    params_b = load_pem_parameters(str(client.params_b).encode(), backend=default_backend())
    
    b_private_key = params_b.generate_private_key()
    b_public_key = b_private_key.public_key()
    
    
    Mqtt.publish(client, b_public_key.public_numbers().y, topic_new_pb_device)
    peer_public_numbers = dh.DHPublicNumbers(client.a_public_key, params_b.parameter_numbers())
    a_public_key = peer_public_numbers.public_key(default_backend())
    b_shared_key = b_private_key.exchange(a_public_key)

    message = "Test"
    key = KeyUtils.convert_key(b_shared_key)    
    mensaje_enc = KeyUtils.encrypt_message(message,key)
    while True:
        Mqtt.publish(client, mensaje_enc, topic_message)
        time.sleep(1)
    
if __name__ == '__main__':
    run()
