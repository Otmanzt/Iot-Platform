from paquetes.mqtt import *
from paquetes.keyUtils import *
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding


def subscribe(client: mqtt_client, topic, key=None):
    def on_message(client, userdata, msg):

        topic = msg.topic
        if "message" in topic:
            msg_client_id = topic[6:16]

            try:
                key = device_list[msg_client_id]
                print(f"Received '{KeyUtils.decrypt_message(msg.payload, key)}' from '{topic}' topic")
            except KeyError:
                key = None
                pass
        else:
            if topic == "/topic/request":
                client.client_id = msg.payload.decode()
                print("Found new device: " + client.client_id + ". Connecting...")
            if topic == "/topic/newConnect/" + client.client_id + "/publicDevice":
                client.b_public_key = int(msg.payload)

    client.subscribe(topic)
    client.on_message = on_message


class Platform:
    parameters = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())
    client_id = f'client-platform'

    def __init__(self):
        self.a_private_key = self.parameters.generate_private_key()
        self.a_public_key = self.a_private_key.public_key()
        self.client = Mqtt.connect_mqtt(self.client_id)
        self.device_list = {}

    def export_parameters(self):
        params_pem = self.parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
        return params_pem

    def re_init_params(self):
        self.client.client_id = None
        self.client.b_public_key = None

    def delete_item(self, key):
        self.device_list.pop(key)
