from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from paquetes.mqtt import *
from paquetes.keyUtils import *
import hmac
from hashlib import md5

deviceList = {}
nonceMsg = {}
optionEncyption = 0
tipoEscenario = 0 
# Master key
master_key = KeyUtils().load_key()

def subscribe(client: mqtt_client, topic, key=None):
    def on_message(client, userdata, msg):    

        topic = msg.topic
        
        if "message" in topic:
            if topic[0] != '/':
                msg_client_id = topic[6:16]
            else:
                msg_client_id = topic[7:17]
            try:
                key = deviceList[msg_client_id]

                try:
                    key = key.decode()
                    key = key[1:33]
                    key = key.encode()
                    
                    nonce = nonceMsg[msg_client_id]
                                           
                    private_shared_key = b'bc12b46'
                    mensajeDict = eval(msg.payload)
                    hmacLocal = hmac_md5(private_shared_key, mensajeDict['msg_encriptado'])
                    hmacLocal = base64.b64encode(hmacLocal.digest()).decode()
                    
                    if KeyUtils.decrypt_message_aes(mensajeDict['msg_encriptado'], key,nonce, mensajeDict['hmac'], hmacLocal) is not None:
                        print("HMAC correcto, se ha verificado la autenticacion")
                        print(f"Received '{KeyUtils.decrypt_message_aes(mensajeDict['msg_encriptado'], key, nonce, mensajeDict['hmac'], hmacLocal)}' from '{topic}' topic")
                    else:
                        print("Los HMAC no coinciden no se ha podido verificar la autenticacion.")
                        
                    
                except KeyError:
                    private_shared_key = b'bc12b46'
                    mensajeDict = eval(msg.payload)
                    hmacLocal = hmac_md5(private_shared_key, mensajeDict['msg_encriptado'])
                    hmacLocal = base64.b64encode(hmacLocal.digest()).decode()
                    key = deviceList[msg_client_id]
                    if KeyUtils.decrypt_message(mensajeDict['msg_encriptado'], key, mensajeDict['hmac'], hmacLocal) is not None:
                        print("HMAC correcto, se ha verificado la autenticacion")
                    else:
                        print("Los HMAC no coinciden no se ha podido verificar la autenticacion.")
                    nonce = None
                    print(f"Recibido '{KeyUtils.decrypt_message(mensajeDict['msg_encriptado'], key, mensajeDict['hmac'], hmacLocal)}' del topic '{topic}'")
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
                client.auth_ack = KeyUtils.decrypt_message(msg.payload, master_key)
            except KeyError:
                key = None
                pass
        else:
            if topic == "topic/" + topic[6:16] + "/nonce":
                nonceMsg[topic[6:16]] = msg.payload
                Mqtt.publish(client, "ACK", "topic/" + topic[6:16] + "/ack")
            else:
                if topic in "/topic/request":
                    clienteDict = eval(msg.payload)
                    client.client_id = clienteDict['client_id']
                    tipoEscenario = clienteDict['tipoEscenario']
                    print("Found new device: "+client.client_id+". Connecting...")
                if topic == "/topic/newConnect/" + client.client_id + "/publicDevice":
                    client.b_public_key = int(msg.payload)
            

            
    client.subscribe(topic)
    client.on_message = on_message
    
def hmac_md5(key, msg):
    return hmac.HMAC(key, msg, md5)

def run():
    mensaje_recibido = False
    time_out = 20
    time_init = 0
    parameters = dh.generate_parameters(generator=2, key_size=512, backend=default_backend())
    
    autenticado = True

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
            print("\n¿Qué quieres hacer?")
            print("0 - Seleccionar topic para leer.")
            print("1 - Listar/eliminar dispositivos.")
            print("2 - Registrar nuevo dispositivo.")
            task = input()

            client = Mqtt.connect_mqtt(name)
            client.nonce = ""

            if task == "0":

                print("Por favor escribe el nombre del topic a escuchar o 0 si quieres escuchar todos.")
                topicOption = input()

                if topicOption == "0":
                    subscribe(client, "/topic/*/message")
                    subscribe(client, "topic/*/nonce")
                    client.loop_forever()
                else:
                    subscribe(client, "/topic/" + client.client_id + "/message")
                    subscribe(client, "topic/" + client.client_id + "/nonce")
                    client.loop_forever()
            
            if task == "1":

                print("Lista de dispositivos registrados:")
                i = 1

                for clave in deviceList.keys():
                    print(str(i)+". "+clave)
                    i=i+1
                
                if i!=1:
                    print("\n¿Quieres eliminar algún dispositivo? Escribe el número del dispositivo a eliminar o 0 si no quieres eliminar ninguno.")
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
                time_out = 20
                time_init = 0
                
                if tipoEscenario == 0: 
                    if mensaje_recibido:
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
 
                elif tipoEscenario == 2:
                    mensaje_recibido = False
                    print("Introduce el numero aleatorio: ")
                    clave_auth = input()
                    
                    if clave_auth != '':
                        codigo_auth = KeyUtils().encrypt_message(clave_auth, master_key)
                        topic_auth = "/topic/" + client.client_id + "/auth"
                        topic_auth_ack = "/topic/" + client.client_id + "/auth/ack"
                        client.loop_start()
                        Mqtt.publish(client, codigo_auth, topic_auth)
                        subscribe(client, topic_auth_ack)
                        while not mensaje_recibido and time_init < time_out:
                            if hasattr(client, 'auth_ack'):
                                mensaje_recibido = True
                                autenticado = client.auth_ack
                
                            time.sleep(1)
                            time_init += 1
                        client.loop_stop()
                    mensaje_recibido = False
                    time_out = 20
                    time_init = 0  
                    if autenticado == "True":
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
                    
                    print("Conectado.")
                else:
                    print("Dispositivo no encontrado.")


if __name__ == '__main__':
    run()