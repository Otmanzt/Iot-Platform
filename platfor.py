from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from paquetes.mqtt import *
from paquetes.keyUtils import *

deviceList = {}
nonceMsg = {}
optionEncyption = 0

def subscribe(client: mqtt_client, topic, key=None):
    def on_message(client, userdata, msg):    

        topic = msg.topic
        
        if "message" in topic:
            msg_client_id = topic[7:17]
            try:
                key = deviceList[msg_client_id]

                try:
                    key = key.decode()
                    key = key[1:33]
                    key = key.encode()

                    nonce = nonceMsg[msg_client_id]
                    print(f"Received '{KeyUtils.decrypt_message_aes(msg.payload, key, nonce)}' from '{topic}' topic")
                except KeyError:

                    key = deviceList[msg_client_id]
                    nonce = None
                    print(f"Received '{KeyUtils.decrypt_message(msg.payload, key)}' from '{topic}' topic")
                    pass

            except KeyError:
                key = None
                pass
        else:

            if topic == "topic/" + topic[6:16] + "/nonce":
                nonceMsg[topic[6:16]] = msg.payload
                Mqtt.publish(client, "ACK", "topic/" + topic[6:16] + "/ack")
            else:
                if topic == "/topic/request":
                    client.client_id = msg.payload.decode()
                    print("Found new device: "+client.client_id+". Connecting...")
                if topic == "/topic/newConnect/" + client.client_id + "/publicDevice":
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

    params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)

    # No hace falta random number, solo hay una plataforma
    name = f'client-platform'

    task = -1

    while True:

        task = -1

        while task != "0" and task != "1":
            print("\nWhat do you want to do?")
            print("0 - Select topics to listen.")
            print("1 - List/remove devices.")
            print("2 - Register new device.")
            task = input()

            client = Mqtt.connect_mqtt(name)
            client.nonce = ""

            if task == "0":

                print("Please write the name of topic or 0 if you want to listen all existent topics.")
                topicOption = input()

                print("What kind of decryption method do you want to use? (0-> Fernet, 1->AHEAD)")
                optionEncyption = int(input())

                if optionEncyption == 0:
                    if topicOption == "0":
                        subscribe(client, "/topic/*/message")
                        client.loop_forever()
                    else:
                        subscribe(client, "/topic/"+topicOption+"/message" "/")
                        client.loop_forever()
                else:
                    if topicOption == "0":
                        subscribe(client, "/topic/*/message")
                        subscribe(client, "topic/*/nonce")
                        client.loop_forever()
                    else:
                        subscribe(client, "topic/" + client.client_id + "/message")
                        subscribe(client, "topic/" + client.client_id + "/nonce")
                        client.loop_forever()
            
            if task == "1":

                print("List of registred devices:")
                i = 1

                for clave in deviceList.keys():
                    print(str(i)+". "+clave)
                    i=i+1
                
                if i!=1:
                    print("\nDo you want to remove any device? Just write the number of the device to remove it or 0 if you don't want to remove a device.")
                    optionSelected = int(input())

                    if optionSelected != 0:
                        del deviceList[tuple(deviceList.items())[optionSelected-1][optionSelected-1]]

            if task == "2":
                topic_request = "/topic/request"
                client.loop_start()
                subscribe(client, topic_request)  # Topic para esperar la respuesta con los parametros de la plataforma
                print("Esperando Cliente nuevo")
                while not mensaje_recibido and time_init < time_out:
                    if hasattr(client, 'client_id'):
                        mensaje_recibido = True
                    time.sleep(1)
                    time_init += 1
                client.loop_stop()
                
                if mensaje_recibido:
                    mensaje_recibido = False

                    topic_new_params = "/topic/newConnect/" + client.client_id + "/params"
                    topic_new_pb_plat = "/topic/newConnect/" + client.client_id + "/publicPlatform"
                    topic_new_pb_device = "/topic/newConnect/" + client.client_id + "/publicDevice"
                    topic_message = "/topic/" + client.client_id + "/message"
                    topic_nonce= "topic/" + client.client_id + "/nonce"
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
                        if hasattr(client, 'b_public_key'):
                            mensaje_recibido = True
                        time.sleep(1)
                        time_init += 1
                    client.loop_stop()

                    mensaje_recibido = False

                    peer_public_numbers = dh.DHPublicNumbers(client.b_public_key, parameters.parameter_numbers())
                    b_public_key = peer_public_numbers.public_key(default_backend())
                    a_shared_key = a_private_key.exchange(b_public_key)

                    key = KeyUtils.convert_key(a_shared_key)
                    deviceList[client.client_id] = key
                    
                    print("Connected to device. Select a topic to listen the messages.")
                else:
                    print("Device not found.")


if __name__ == '__main__':
    run()