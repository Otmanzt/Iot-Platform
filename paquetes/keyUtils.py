from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from Crypto.Cipher import AES

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

        encoded_message = message.encode()
        f = Fernet(key)
        encrypted_message = f.encrypt(encoded_message)

        return encrypted_message

    @staticmethod
    def encrypt_message_aes(message, key):

        cipher = AES.new(key, AES.MODE_GCM)
        nonce = cipher.nonce
        encrypted_message = cipher.encrypt(message.encode()) 

        return encrypted_message, nonce

    @staticmethod
    def decrypt_message(encrypted_message, key):

        f = Fernet(key)
        decrypted_message = f.decrypt(encrypted_message)

        return decrypted_message.decode()

    @staticmethod
    def decrypt_message_aes(encrypted_message, key, nonce):

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted_data = cipher.decrypt(encrypted_message)

        return decrypted_data

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
