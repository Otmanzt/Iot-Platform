from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

class KeyUtils:

    @staticmethod
    def generate_key():
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)

    @staticmethod
    def load_key():
        return open("secret.key", "rb").read()

    @staticmethod
    def encrypt_message(message, key):

        #key = load_key()
        encoded_message = message.encode()
        f = Fernet(key)
        encrypted_message = f.encrypt(encoded_message)

        return encrypted_message

    @staticmethod
    def decrypt_message(encrypted_message, key):

        #key = load_key()
        f = Fernet(key)
        decrypted_message = f.decrypt(encrypted_message)

        return decrypted_message.decode()

    @staticmethod
    def convert_key(shared_key):
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'handshake data',
        ).derive(shared_key)

        key = base64.urlsafe_b64encode(derived_key)

        return key
