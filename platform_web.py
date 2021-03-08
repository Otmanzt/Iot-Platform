from paquetes.mqtt import *
from paquetes.keyUtils import *
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding


class Platform:
    parameters = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())
    client_id = f'client-platform'

    def __init__(self):
        self.a_private_key = self.parameters.generate_private_key()
        self.a_public_key = self.a_private_key.public_key()
        self.client = Mqtt.connect_mqtt(self.client_id)
        self.client.msg_payload = []
        self.client.b_public_key = 0

    def export_parameters(self):
        params_pem = self.parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
        return params_pem
