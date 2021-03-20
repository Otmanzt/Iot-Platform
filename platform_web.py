from paquetes.mqtt import *
from paquetes.keyUtils import *
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
import hmac
from hashlib import md5

#Este controlador tiene las mismas funcionalidades que platfor.py, pero esta adaptado a la version web con algunas pequeñas modificaciones, y ademas esta orientado a objetos.
def subscribe(client: mqtt_client, topic, device_list=None, key=None, nonceMsg = None):
    def on_message(client, userdata, msg):

        #Al llegarle un mensaje mira el topic.
        topic = msg.topic
        #Si es un mensaje
        if "message" in topic:
            #Seleccionamos el client_id
            if topic[0] != '/':
                msg_client_id = topic[6:16]
            else:
                msg_client_id = topic[7:17]
            try:
                #Busca la clave para desencriptar el mensaje
                key = device_list[msg_client_id]

                #Intenta descomprimir el mensaje usando AHEAD
                try:
                    #Adapta la clave
                    key = key.decode()
                    key = key[1:33]
                    key = key.encode()

                    #Busca el nonce del mensaje
                    nonce = nonceMsg[msg_client_id]

                    # Variables para autenticacion HMAC
                    private_shared_key = b'bc12b46'
                    mensajeDict = eval(msg.payload)
                    # Calculo del hmac local para compararlo con el que llega
                    hmacLocal = hmac_md5(private_shared_key, mensajeDict['msg_encriptado'])
                    hmacLocal = base64.b64encode(hmacLocal.digest()).decode()

                    #Si el HMAC coincide, va a desencriptar el mensaje y mostrarlo
                    if KeyUtils.decrypt_message_aes(mensajeDict['msg_encriptado'], key, nonce, mensajeDict['hmac'],
                                                    hmacLocal) is not None:
                        print("HMAC correcto, se ha verificado la autenticacion")
                        print(f"Recibido '{KeyUtils.decrypt_message_aes(mensajeDict['msg_encriptado'], key, nonce, mensajeDict['hmac'], hmacLocal)}' del topic '{topic}'")
                        # Variables que se van a mostrar en el topic
                        clienteArray = eval(msg.payload)
                        client.message = KeyUtils.decrypt_message_aes(clienteArray['msg_encriptado'], key, nonce, mensajeDict['hmac'], hmacLocal)
                        client.topic_client = topic
                        client.id_msg_cliente = msg_client_id
                    else:
                        #Si no coincide, no se desencripta.
                        print("Los HMAC no coinciden no se ha podido verificar la autenticacion.")

                #Si no se puede por AHEAD, se hace por Fernet.
                except KeyError:
                     # Variables para autenticacion HMAC
                    private_shared_key = b'bc12b46'
                    mensajeDict = eval(msg.payload)
                    # Calculo del hmac local para compararlo con el que llega
                    hmacLocal = hmac_md5(private_shared_key, mensajeDict['msg_encriptado'])
                    hmacLocal = base64.b64encode(hmacLocal.digest()).decode()
                    #Obtenemos la clave para desencriptar
                    key = device_list[msg_client_id]
                    #Si el HMAC coincide, va a desencriptar el mensaje y mostrarlo
                    if KeyUtils.decrypt_message(mensajeDict['msg_encriptado'], key, mensajeDict['hmac'],
                                                hmacLocal) is not None:
                        print("HMAC correcto, se ha verificado la autenticacion")
                    else:
                        #Si no coincide, no se desencripta.
                        print("Los HMAC no coinciden no se ha podido verificar la autenticacion.")
                    nonce = None
                    print(f"Recibido '{KeyUtils.decrypt_message(mensajeDict['msg_encriptado'], key, mensajeDict['hmac'], hmacLocal)}' del topic '{topic}'")
                    # variables que se van a usar para mostrar en el topic
                    clienteArray = eval(msg.payload)
                    client.message = KeyUtils.decrypt_message(clienteArray['msg_encriptado'], key, mensajeDict['hmac'], hmacLocal)
                    client.topic_client = topic
                    client.id_msg_cliente = msg_client_id
                    pass

            except KeyError:
                key = None
                pass
        # Para la confirmacion de la autenticacion
        elif "auth/ack" in topic:
            if topic[0] != '/':
                msg_client_id = topic[6:16]
            else:
                msg_client_id = topic[7:17]

            try:
                client.auth_ack = KeyUtils.decrypt_message(msg.payload, Platform().master_key)
            except KeyError:
                key = None
                pass
        # Para la confirmacion de la autenticacion
        elif "auth" in topic:
            if topic[0] != '/':
                msg_client_id = topic[6:16]
            else:
                msg_client_id = topic[7:17]

            try:
                client.clave_auth = KeyUtils.decrypt_message(msg.payload, Platform().master_key)
            except KeyError:
                key = None
                pass

        else:
            #Si el topic contiene nonce, lo que va a hacer es guardarla para desencriptar el mensaje y enviar un ACK.
            if topic == "topic/" + topic[6:16] + "/nonce":
                nonceMsg[topic[6:16]] = msg.payload
                Mqtt.publish(client, "ACK", "topic/" + topic[6:16] + "/ack")
            else:
                #Si el topic contiene request, lo que hace es guardar el cliente que quiere conectarse.
                if topic == "/topic/request":
                    clienteArray = eval(msg.payload)
                    client.client_id = clienteArray['client_id']
                    client.tipo_escenario = clienteArray['tipoEscenario']
                    print("Found new device: " + client.client_id + ". Connecting...")
                #Si el topic contiene publicDevice, lo que hace es guardar la clave publica que estamos recibiendo para crear la clave privada con la nuestra pública.
                if topic == "/topic/newConnect/" + client.client_id + "/publicDevice":
                    client.b_public_key = int(msg.payload)

    client.subscribe(topic)
    client.on_message = on_message

# funcion para calcular el hmac
def hmac_md5(key, msg):
    return hmac.HMAC(key, msg, md5)

class Platform:
    #Creamos una plataforma.
    parameters = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())
    client_id = f'client-platform'

    #Inicializamos todas las variables que vamos a necesitar.
    def __init__(self):
        self.a_private_key = self.parameters.generate_private_key()
        self.a_public_key = self.a_private_key.public_key()
        self.client = Mqtt.connect_mqtt(self.client_id)
        self.device_list = {}
        self.master_key = KeyUtils().load_key()
        self.nonceMsg = {}

    #Sirve para recoger los parámetros usados para crear la key y devolverla al device.
    def export_parameters(self):
        params_pem = self.parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
        return params_pem

    #Borra los parámetros 'client_id' y 'b_public_key'
    def re_init_params(self):
        delattr(self.client, 'client_id')
        delattr(self.client, 'b_public_key')

    #Borra los parámetros 'message' y 'topic_client'
    def re_init_buffer(self):
        delattr(self.client, 'message')
        delattr(self.client, 'topic_client')

    #Elimina la key de la lista de dispositivos para que no lea mas mensajes de ese dispositivo.
    def delete_item(self, key):
        self.device_list.pop(key)

    #Reconecta a un cliente.
    def reboot_client(self):
        delattr(self, 'client')
        self.client = Mqtt.connect_mqtt(self.client_id)
