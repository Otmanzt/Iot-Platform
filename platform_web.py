from paquetes.mqtt import *
from paquetes.keyUtils import *
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
import hmac
from hashlib import md5


def subscribe(client: mqtt_client, topic, device_list=None, key=None, nonceMsg = None):
    def on_message(client, userdata, msg):

        topic = msg.topic
        if "message" in msg.topic:
            if topic[0] != '/':
                msg_client_id = topic[6:16]
            else:
                msg_client_id = topic[7:17]
            try:
                key = device_list[msg_client_id]

                try:
                    key = key.decode()
                    key = key[1:33]
                    key = key.encode()

                    nonce = nonceMsg[msg_client_id]

                    private_shared_key = b'bc12b46'
                    mensajeDict = eval(msg.payload)
                    hmacLocal = hmac_md5(private_shared_key, mensajeDict['msg_encriptado'])
                    hmacLocal = base64.b64encode(hmacLocal.digest()).decode()

                    if KeyUtils.decrypt_message_aes(mensajeDict['msg_encriptado'], key, nonce, mensajeDict['hmac'],
                                                    hmacLocal) is not None:
                        print("HMAC correcto, se ha verificado la autenticacion")
                        print(f"Recibido '{KeyUtils.decrypt_message_aes(mensajeDict['msg_encriptado'], key, nonce, mensajeDict['hmac'], hmacLocal)}' del topic '{topic}'")
                        clienteArray = eval(msg.payload)
                        client.message = KeyUtils.decrypt_message_aes(clienteArray['msg_encriptado'], key, nonce, mensajeDict['hmac'], hmacLocal)
                        client.topic_client = topic
                        client.id_msg_cliente = msg_client_id
                    else:
                        print("Los HMAC no coinciden no se ha podido verificar la autenticacion.")


                except KeyError:
                    private_shared_key = b'bc12b46'
                    mensajeDict = eval(msg.payload)
                    hmacLocal = hmac_md5(private_shared_key, mensajeDict['msg_encriptado'])
                    hmacLocal = base64.b64encode(hmacLocal.digest()).decode()
                    key = device_list[msg_client_id]
                    if KeyUtils.decrypt_message(mensajeDict['msg_encriptado'], key, mensajeDict['hmac'],
                                                hmacLocal) is not None:
                        print("HMAC correcto, se ha verificado la autenticacion")
                    else:
                        print("Los HMAC no coinciden no se ha podido verificar la autenticacion.")
                    nonce = None
                    print(f"Recibido '{KeyUtils.decrypt_message(mensajeDict['msg_encriptado'], key, mensajeDict['hmac'], hmacLocal)}' del topic '{topic}'")
                    clienteArray = eval(msg.payload)
                    client.message = KeyUtils.decrypt_message(clienteArray['msg_encriptado'], key, mensajeDict['hmac'], hmacLocal)
                    client.topic_client = topic
                    client.id_msg_cliente = msg_client_id
                    pass

            except KeyError:
                key = None
                pass
        elif "auth/ack" in msg.topic:
            if topic[0] != '/':
                msg_client_id = topic[6:16]
            else:
                msg_client_id = topic[7:17]

            try:
                client.auth_ack = KeyUtils.decrypt_message(msg.payload, Platform().master_key)
            except KeyError:
                key = None
                pass
        elif "auth" in msg.topic:
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
            if topic == "topic/" + topic[6:16] + "/nonce":
                nonceMsg[topic[6:16]] = msg.payload
                Mqtt.publish(client, "ACK", "topic/" + topic[6:16] + "/ack")
            else:
                if topic == "/topic/request":
                    clienteArray = eval(msg.payload)
                    client.client_id = clienteArray['client_id']
                    client.tipo_escenario = clienteArray['tipoEscenario']
                    print("Found new device: " + client.client_id + ". Connecting...")
                if topic == "/topic/newConnect/" + client.client_id + "/publicDevice":
                    client.b_public_key = int(msg.payload)



    client.subscribe(topic)
    client.on_message = on_message


def hmac_md5(key, msg):
    return hmac.HMAC(key, msg, md5)

class Platform:
    parameters = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())
    client_id = f'client-platform'

    def __init__(self):
        self.a_private_key = self.parameters.generate_private_key()
        self.a_public_key = self.a_private_key.public_key()
        self.client = Mqtt.connect_mqtt(self.client_id)
        self.device_list = {}
        self.master_key = KeyUtils().load_key()
        self.nonceMsg = {}

    def export_parameters(self):
        params_pem = self.parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
        return params_pem

    def re_init_params(self):
        delattr(self.client, 'client_id')
        delattr(self.client, 'b_public_key')

    def re_init_buffer(self):
        delattr(self.client, 'message')
        delattr(self.client, 'topic_client')

    def delete_item(self, key):
        self.device_list.pop(key)

    def reboot_client(self):
        delattr(self, 'client')
        self.client = Mqtt.connect_mqtt(self.client_id)
