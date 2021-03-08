from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from paquetes.mqtt import *
from paquetes.keyUtils import *

deviceList = {}

def subscribe(client: mqtt_client, topic, key=None):
    def on_message(client, userdata, msg):
        if key is not None:
            print(f"Received '{KeyUtils.decrypt_message(msg.payload, key)}' from '{msg.topic}' topic")
        else:
            print(f"Received '{msg.payload.decode()}' from '{msg.topic}' topic")
            if msg.topic == "/topic/newConnect/" + client.client_id + "/publicDevice":
                client.b_public_key = int(msg.payload)

    client.subscribe(topic)
    client.on_message = on_message

def run():
    mensaje_recibido = False
    time_out = 20
    time_init = 0
    parameters = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())

    # Generate private keys.
    a_private_key = parameters.generate_private_key()
    a_public_key = a_private_key.public_key()

    print("Esta es mi clave privada: %d" % a_private_key.private_numbers().x)
    print("Esta es mi clave pública: %d" % a_public_key.public_numbers().y)

    params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)

    # No hace falta random number, solo hay una plataforma
    client_id = f'client-platform'

    client = Mqtt.connect_mqtt(client_id)

    task = -1
    changekey = -1
    '''
    while changekey != "0" and changekey != "1" and os.path.isfile("secret.key"):
        print("Do you want to generate another key? (0/1)")
        changekey = input()

    if changekey == "1" or os.path.isfile("secret.key") == False:
        print("Generating a new Fender key...")
        generate_key()
    '''

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
                subscribe(client, "#")
                client.loop_forever()
            else:
                subscribe(client, "/"+topicOption)
                client.loop_forever()

        if task == "2":
            topic_request = "/topic/request"
            client.msg_payload = []
            client.b_public_key = 0
            client.loop_start()

            Mqtt.subscribe(client, topic_request)  # Topic para esperar la respuesta con los parametros de la plataforma
            print("Esperando Cliente nuevo")
            while not mensaje_recibido and time_init < time_out:
                if client.msg_payload:
                    mensaje_recibido = True
                time.sleep(1)
                time_init += 1
            client.loop_stop()

            if client.msg_payload:
                client.client_id = str(client.msg_payload[0])
                topic_new_params = "/topic/newConnect/" + client.client_id + "/params"
                topic_new_pb_plat = "/topic/newConnect/" + client.client_id + "/publicPlatform"
                topic_new_pb_device = "/topic/newConnect/" + client.client_id + "/publicDevice"
                topic_message = "/topic/" + client.client_id + "/message"
                # Parametros
                Mqtt.publish(client, params_pem, topic_new_params)
                # Clave publica de la plataforma
                Mqtt.publish(client, a_public_key.public_numbers().y, topic_new_pb_plat)
                # Se queda escuchando la clave publica del dispositivo
                mensaje_recibido = False
                time_init = 0
                client.loop_start()
                subscribe(client, topic_new_pb_device)
                print("Esperando clave pública del dispositivo...")
                while not mensaje_recibido and time_init < time_out:
                    if client.b_public_key:
                        mensaje_recibido = True
                    time.sleep(1)
                    time_init += 1
                client.loop_stop()

                peer_public_numbers = dh.DHPublicNumbers(client.b_public_key, parameters.parameter_numbers())
                b_public_key = peer_public_numbers.public_key(default_backend())
                a_shared_key = a_private_key.exchange(b_public_key)

                key = KeyUtils.convert_key(a_shared_key)
                '''
                client.loop_start()
                subscribe(client, topic_message, key)
                time.sleep(10)
                client.loop_stop()
                '''
                deviceList[client.client_id] = key

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