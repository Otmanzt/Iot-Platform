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

# Numero que va a servir como id del dispositivo
randomNumber = random.randint(100, 999)
client_id = f'client-{randomNumber}'
# Master key estatica que tienen de forma compartida el dispositivo y la plataforma
master_key = KeyUtils().load_key()


def subscribe(client: mqtt_client, topic, key=None):
    def on_message(client, userdata, msg):
        # Topic para recibir los parametros de la plataforma
        if msg.topic == "/topic/newConnect/" + client_id + "/params":
            client.params_b = msg.payload.decode()
        # Topic para recibir la clave publica de la plataforma
        if msg.topic == "/topic/newConnect/" + client_id + "/publicPlatform":
            client.a_public_key = int(msg.payload)
        # Topic recibir el ack de confirmacion del recibimiento del nonce por parte de la plataforma
        # (AHEAD)
        if msg.topic == "topic/" + client_id + "/ack":
            client.ack = True
        # Topic para recibir el mensaje encriptado con la master key para verificar la autenticacion
        if msg.topic == "/topic/" + client_id + "/auth":
            client.clave_auth = msg.payload
        # Topic para recibir el ack de que la plataforma ha conseguido descifrar correctamente el mensaje
        # y se ha verificado la autenticacion
        if msg.topic == "/topic/" + client_id + "/auth/ack":
            client.auth_ack = msg.payload

    client.subscribe(topic)
    client.on_message = on_message
    
def hmac_md5(key, msg):
    return hmac.HMAC(key, msg, md5)

def run():
    # Variable que va a indicar si se ha recibido mensaje de la suscripcion de algun topic
    mensaje_recibido = False
    # Tiempo maximo de espera para la escucha de un topic
    time_out = 20
    time_init = 0
    # variable de autenticacion
    autenticado = "True"
    
    # Tipo de cifrado
    optionEncyption = 0
    
    # Tipo de escenario del dispositivo
    tipoEscenario = 0
    
    # Eleccion de escenario
    print("Elija el tipo de escenario:")
    print("0 - Sin entrada ni salida.")
    print("1 - Entrada.")
    print("2 - Salida.")
    tipoEscenario = int(input())

    # TOPICS
    # Topic: parametros para DH
    topic_new_params = "/topic/newConnect/"+client_id+"/params"
     # Topic para recibir la clave publica de la plataforma
    topic_new_pb_plat = "/topic/newConnect/" + client_id + "/publicPlatform"
     # Topic para enviar la clave publica del dispositivo
    topic_new_pb_device = "/topic/newConnect/" + client_id + "/publicDevice"
    # Topic para solicitar nueva conexion
    topic_request = "/topic/request"  
    # Topic para enviar mensajes 
    topic_message = "/topic/" + client_id + "/message"
    # Topic para enviar el nonce (AHEAD)
    topic_nonce = "topic/" + client_id + "/nonce"
    # Topic para enviar o recibir ack de conexion
    topic_ack = "topic/" + client_id + "/ack"
    # Topic para iniciar la autenticacion
    topic_auth = "/topic/" + client_id + "/auth"
    # Topic para recibir o enviar ack de autenticacion
    topic_auth_ack = "/topic/" + client_id + "/auth/ack"

    
    # Conexion con MQTT
    client = Mqtt.connect_mqtt(client_id)
    client.ack = False
    
    # Creamos un nuevo dict para anadir el tipo de escenario para comunicarlo a la plataforma
    cliente = {'client_id': client_id, 'tipoEscenario': tipoEscenario}
    
    # Topic para enviar la peticion de conexion nueva con la plataform
    Mqtt.publish(client, str(cliente), topic_request)   
    
    # Escenario 1 de entrada
    if tipoEscenario == 1:
        # Codigo para la autenticacion
        print("Introduce el codigo de autenticacion de la plataforma: ")
        numero_random = int(input())
        
        # Encriptacion del codigo aleatorio para la autenticacion
        codigo_auth = KeyUtils().encrypt_message(str(numero_random), master_key)
        
        client.loop_start()
        
        # Envia el mensaje encriptado a la plataforma
        Mqtt.publish(client, codigo_auth, topic_auth)
        # Suscripcion para recibir el ack de la autenticacion
        subscribe(client, topic_auth_ack)
        while not mensaje_recibido and time_init < time_out:
            if hasattr(client, 'auth_ack'):
                mensaje_recibido = True
                # Desencripta el mensaje recibido con la master key y devuelve true o false si es igual o no
                autenticado = KeyUtils().decrypt_message(client.auth_ack, master_key)
            time.sleep(1)
            time_init += 1
        client.loop_stop()

    elif tipoEscenario == 2:
        # Generacion del numero aleatorio para la autenticacion
        numero_random = str(random.randint(1000, 9999))
        print("Clave aleatoria es: " + numero_random)
        client.loop_start()
        # Suscripcion para recibir el ack de la autenticacion
        subscribe(client, topic_auth)
        while not mensaje_recibido:
            if hasattr(client, 'clave_auth'):
                mensaje_recibido = True
                # Descifrado del mensaje
                num_descifrado = KeyUtils().decrypt_message(client.clave_auth, master_key)
                # Comparacion si coincide con el numero aleatorio para comprobar la autenticacion
                if num_descifrado != numero_random:
                    autenticado = False
            time.sleep(1)
            time_init += 1

        client.loop_stop()
        
    # Confirmacion de si se coincide o no el mensaje de autenticacion
    confirmacion = KeyUtils.encrypt_message(str(autenticado), master_key)
    # Envio de la confirmacion
    Mqtt.publish(client, confirmacion, topic_auth_ack)
    
    # Si se verifica la autenticacion se procede si no no
    if autenticado == "True":
        client.loop_start()
        # Topic para esperar la respuesta con los parametros de la plataforma
        subscribe(client, topic_new_params)  
        # Topic para esperar la respuesta con los parametros de la plataforma
        subscribe(client, topic_new_pb_plat)  
        print("Conectando a la plataforma... Espere por favor.")

        mensaje_recibido = False
        time_out = 20
        time_init = 0
        
        # Espera hasta la recepcion de la clave publica y de los parametros de DH
        while not mensaje_recibido and time_init < time_out:
            if hasattr(client, 'a_public_key') and hasattr(client, 'params_b'):
                mensaje_recibido = True
                print("Paquete recibido")
            time.sleep(1)
            time_init += 1

        client.loop_stop()

        mensaje_recibido = False
        
        # Parametros necesarios para el calculo de las claves en ambas partes
        params_b = load_pem_parameters(str(client.params_b).encode(), backend=default_backend())
        
        # Claves publicas y privadas
        b_private_key = params_b.generate_private_key()
        b_public_key = b_private_key.public_key()

        # Envio de la clave publica del dispositivo
        Mqtt.publish(client, b_public_key.public_numbers().y, topic_new_pb_device)
        # Parametros DH
        peer_public_numbers = dh.DHPublicNumbers(client.a_public_key, params_b.parameter_numbers())
        a_public_key = peer_public_numbers.public_key(default_backend())
        # Calculo de la clave simetrica compartida
        b_shared_key = b_private_key.exchange(a_public_key)
        
        # Conversion de la clave simetrica para usarlo en los cifrados fernet
        key = KeyUtils.convert_key(b_shared_key)

        # Variables para autenticacion HMAC
        private_shared_key = b'bc12b46'
        mensaje = {}
        
        # Mensaje que se envia al topic
        message = "Test"
        print("¿Qué tipo de encriptación quieres usar? (0-> Fernet, 1->AHEAD)")
        optionEncyption = int(input())
        
        # Tipo de cifrado fernet
        if optionEncyption == 0:
            # Cifrar el mensaje
            mensaje_enc = KeyUtils.encrypt_message(message,key)

            # Calculo del HMAC
            hmac = hmac_md5(private_shared_key, mensaje_enc)

            mensaje['msg_encriptado'] = mensaje_enc
            mensaje['hmac'] = base64.b64encode(hmac.digest()).decode()

            while True:
                # Envio del mensaje cifrado y HMAC
                Mqtt.publish(client, str(mensaje), topic_message)
                time.sleep(1)
        # Tipo de cifrado AHEAD
        else:
            # Adaptacion de la clave a 32 bits para AHEAD
            key = key.decode()
            key = key[1:33]
            key = key.encode()

            # Cifrado y guardando el nonce
            mensaje_enc, nonce = KeyUtils.encrypt_message_aes(message,key)
            mensaje['msg_encriptado'] = mensaje_enc
            # HMAC
            hmac = hmac_md5(private_shared_key, mensaje_enc)

            mensaje['hmac'] = base64.b64encode(hmac.digest()).decode()
            # Envio continuo del mensaje cifrado
            while True:
                
                # Envio el nonce del mensaje
                Mqtt.publish(client, nonce, topic_nonce)

                client.loop_start()
                # Espera del ack para confirmar que la plataforma ha recibido el nonce
                subscribe(client, topic_ack)
                while not client.ack and time_init < time_out:
                    time.sleep(1)
                    time_init += 1

                client.loop_stop()
                
                # Si se ha recibido el ack
                if(client.ack):
                    # Envio mensaje cifrado
                    Mqtt.publish(client, str(mensaje), topic_message)

                time.sleep(1)

if __name__ == '__main__':
    run()
