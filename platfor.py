import random
import os.path
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import load_pem_parameters
from paquetes.mqtt import *
from paquetes.keyUtils import *

deviceList = {}


def run():
    parameters = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())

    # Generate private keys.
    a_private_key = parameters.generate_private_key()
    a_public_key = a_private_key.public_key()

    print("Esta es mi clave privada: %d" % a_private_key.private_numbers().x)
    print("Esta es mi clave pública: %d" % a_public_key.public_numbers().y)

    params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)

    randomNumber = random.randint(0, 1000)
    client_id = f'client-platform-{randomNumber}'

    client = Mqtt.connect_mqtt(client_id)
    task = -1
    changekey = -1

    while changekey != "0" and changekey != "1" and os.path.isfile("secret.key"):
        print("Do you want to generate another key? (0/1)")
        changekey = input()

    if changekey == "1" or os.path.isfile("secret.key") == False:
        print("Generating a new Fender key...")
        generate_key()


    while task != "0" and task != "1":
        print("What do you want to do?")
        print("0 - Select topics to listen.")
        print("1 - List devices. (NOT  IMPLEMENTED YET)")
        print("2 - Register new device.")
        task = input()

        if task == "0":

            print("Please write the name of topic or 0 if you want to listen all existent topics.")
            topicOption = input()

            if topicOption == "0":
                Mqtt.subscribe(client, "#")
                client.loop_forever()
            else:
                Mqtt.subscribe(client, "/"+topicOption)
                client.loop_forever()
                
        if task == "2":
            topic_request = "/topic/request"
            client.msg_payload = []
            client.loop_start()
            Mqtt.subscribe(client, topic_request)  # Topic para esperar la respuesta con los parametros de la plataforma
            time.sleep(10)
            client.loop_stop()

            if client.msg_payload:
                topic_new_params = "/topic/newConnect/" + str(client.msg_payload[0]) + "/params"
                topic_new_pb = "/topic/newConnect/" + str(client.msg_payload[0]) + "/public"
                Mqtt.publish(client, params_pem, topic_new_params)
                Mqtt.publish(client, params_pem, topic_new_pb)
            else:
                print("Timeout 10 secs")

            '''
            parameters = dh.generate_parameters(generator=2, key_size=512,backend=default_backend())
    
            #Generate private keys.
            a_private_key = parameters.generate_private_key()
            a_public_key = a_private_key.public_key()

            print("Esta es mi clave privada: %d"%a_private_key.private_numbers().x)
            print("Esta es mi clave pública: %d"%a_public_key.public_numbers().y)

            params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
            params_b = load_pem_parameters(params_pem, backend=default_backend())

            b_private_key = params_b.generate_private_key()
            b_public_key = b_private_key.public_key()

            print("Esta es tu clave privada: %d"%b_private_key.private_numbers().x)
            print("Esta es tu clave pública: %d"%b_public_key.public_numbers().y)

            a_shared_key = a_private_key.exchange(b_public_key)
            b_shared_key = b_private_key.exchange(a_public_key)

            print("a_shared_key: " + str(a_shared_key))
            print("b_shared_key: " + str(b_shared_key))

            message="Test"

            key = KeyUtils.convert_key(a_shared_key)

            mensaje_enc = KeyUtils.encrypt_message(message,key)
            print(mensaje_enc)

            mensaje_des = KeyUtils.decrypt_message(mensaje_enc,key)
            print(mensaje_des)

            
            #deviceList[1] = key
            '''
if __name__ == '__main__':
    run()