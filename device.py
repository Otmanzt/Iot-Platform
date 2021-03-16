import random
#import os.path
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import load_pem_parameters
from paquetes.mqtt import *
from paquetes.keyUtils import *
import hmac
from hashlib import md5
import json 

randomNumber = random.randint(100, 999)
master_key = KeyUtils().load_key()
client_id = f'client-{randomNumber}'


def subscribe(client: mqtt_client, topic, key=None):
    def on_message(client, userdata, msg):

        if msg.topic == "/topic/newConnect/" + client_id + "/params":
            client.params_b = msg.payload.decode()
        if msg.topic == "/topic/newConnect/" + client_id + "/publicPlatform":
            client.a_public_key = int(msg.payload)
        if msg.topic == "topic/" + client_id + "/ack":
            client.ack = True
        if msg.topic == "/topic/" + client_id + "/auth":
            client.clave_auth = msg.payload

    client.subscribe(topic)
    client.on_message = on_message
    
def hmac_md5(key, msg):
    return hmac.HMAC(key, msg, md5)

def run():

    mensaje_recibido = False
    time_out = 20
    time_init = 0
    autenticado = True
    
    optionEncyption = 0
    option = -1
    task = -1
    topicOption = -1
    changekey = -1
    tipoEscenario = 0
    
    # Eleccion de escenario
    print("Elija el tipo de escenario:")
    print("0 - Sin entrada ni salida.")
    print("1 - Entrada.")
    print("2 - Salida.")
    tipoEscenario = int(input())

    # TOPICS
    topic_new_params = "/topic/newConnect/"+client_id+"/params"
    topic_new_pb_plat = "/topic/newConnect/" + client_id + "/publicPlatform"
    topic_new_pb_device = "/topic/newConnect/" + client_id + "/publicDevice"
    topic_request = "/topic/request"   
    topic_message = "/topic/" + client_id + "/message"
    topic_nonce = "topic/" + client_id + "/nonce"
    topic_ack = "topic/" + client_id + "/ack"
    topic_auth = "/topic/" + client_id + "/auth"
    topic_auth_ack = "/topic/" + client_id + "/auth/ack"

    
    # Conexion con MQTT
    client = Mqtt.connect_mqtt(client_id)
    client.ack = False
    
    # Creamos un nuevo dict para anadir el tipo de escenario para comunicarlo a la plataforma
    cliente = {}
    cliente['client_id'] = client_id
    cliente['tipoEscenario'] = tipoEscenario

    Mqtt.publish(client, str(cliente), topic_request)  # Topic para enviar la peticion de conexion nueva con la plataform

    if tipoEscenario == 2:
        numero_random = str(random.randint(1000, 9999))
        print("Clave aleatoria es: " + numero_random)
        client.loop_start()
        subscribe(client, topic_auth)  # Topic para esperar la respuesta con los parametros de la plataforma
        while not mensaje_recibido:
            if hasattr(client, 'clave_auth'):
                mensaje_recibido = True
                num_descifrado = KeyUtils().decrypt_message(client.clave_auth, master_key)
                if num_descifrado != numero_random:
                    autenticado = False
            time.sleep(1)
            time_init += 1

        client.loop_stop()

    confirmacion = KeyUtils.encrypt_message(str(autenticado), master_key)
    Mqtt.publish(client, confirmacion, topic_auth_ack)

    if autenticado:
        client.loop_start()
        subscribe(client, topic_new_params)  # Topic para esperar la respuesta con los parametros de la plataforma
        subscribe(client, topic_new_pb_plat)  # Topic para esperar la respuesta con los parametros de la plataforma
        print("Conectando a la plataforma... Espere por favor.")

        mensaje_recibido = False
        time_out = 20
        time_init = 0

        while not mensaje_recibido and time_init < time_out:
            if hasattr(client, 'a_public_key') and hasattr(client, 'params_b'):
                mensaje_recibido = True
            time.sleep(1)
            time_init += 1

        client.loop_stop()

        mensaje_recibido = False

        params_b = load_pem_parameters(str(client.params_b).encode(), backend=default_backend())

        b_private_key = params_b.generate_private_key()
        b_public_key = b_private_key.public_key()


        Mqtt.publish(client, b_public_key.public_numbers().y, topic_new_pb_device)
        peer_public_numbers = dh.DHPublicNumbers(client.a_public_key, params_b.parameter_numbers())
        a_public_key = peer_public_numbers.public_key(default_backend())
        b_shared_key = b_private_key.exchange(a_public_key)

        key = KeyUtils.convert_key(b_shared_key)

        # Variables para autenticacion HMAC
        private_shared_key = b'bc12b46'
        mensaje = {}

        message = "Test"
        print("¿Qué tipo de encriptación quieres usar? (0-> Fernet, 1->AHEAD)")
        optionEncyption = int(input())

        if optionEncyption == 0:

            mensaje_enc = KeyUtils.encrypt_message(message,key)

            # HMAC
            hmac = hmac_md5(private_shared_key, mensaje_enc)

            mensaje['msg_encriptado'] = mensaje_enc
            mensaje['hmac'] = base64.b64encode(hmac.digest()).decode()

            while True:
                Mqtt.publish(client, str(mensaje), topic_message)
                time.sleep(1)
        else:

            key = key.decode()
            key = key[1:33]
            key = key.encode()


            mensaje_enc, nonce = KeyUtils.encrypt_message_aes(message,key)
            mensaje['msg_encriptado'] = mensaje_enc
            # HMAC
            hmac = hmac_md5(private_shared_key, mensaje_enc)

            mensaje['hmac'] = base64.b64encode(hmac.digest()).decode()
            while True:

                Mqtt.publish(client, nonce, topic_nonce)

                client.loop_start()
                subscribe(client, topic_ack)
                while not client.ack and time_init < time_out:
                    time.sleep(1)
                    time_init += 1

                client.loop_stop()

                if(client.ack):
                    Mqtt.publish(client, str(mensaje), topic_message)

                time.sleep(1)

if __name__ == '__main__':
    run()
