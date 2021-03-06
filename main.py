
from flask import Flask, render_template, request, redirect, url_for, session
from platform_web import *
from datetime import datetime
import json
from paquetes.keyUtils import *

app = Flask(__name__, static_url_path='/static')
platform = Platform()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/registrar')
def registrar():
    datos = {'pk_pub': platform.a_public_key.public_numbers().y}

    return render_template('registrar.html', datos=datos) 

@app.route('/listar')
def listar():
    lista_dev = platform.device_list
    num_items = len(platform.device_list)
    return render_template('listar.html', datos=lista_dev, num_items=num_items)

@app.route('/borrarDispositivo/<key_disp>')
def borrar(key_disp):
    platform.delete_item(key_disp)
    num_items = len(platform.device_list)
    lista_dev = platform.device_list
    return render_template('listar.html', datos=lista_dev, num_items=num_items)


@app.route('/selecTopic')
def selecTopic():
    return render_template('selecTopic.html')


@app.route('/escucharTopic', methods=["POST"])
def escuchar():
    topic = request.form['topic']
    mensaje_recibido = []
    mensaje_client = []
    time_out = 20
    time_init = 0

    platform.client.loop_start()
    subscribe(platform.client, topic, platform.device_list,None,platform.nonceMsg)
    if topic[0] != '/':
        msg_client_id = topic[6:16]
    else:
        msg_client_id = topic[7:17]
    subscribe(platform.client, "topic/" + msg_client_id + "/nonce",platform.device_list,None,platform.nonceMsg)

    while time_init < time_out:
        if hasattr(platform.client, 'message') and platform.client.message is not None:
            mensaje_recibido.append(platform.client.message)
            mensaje_client.append(platform.client.id_msg_cliente)
        time.sleep(1)
        time_init += 1
    platform.client.loop_stop()

    if mensaje_recibido:
        response = {
            "topic": platform.client.topic_client,
            "clientes": mensaje_client,
            "messages": mensaje_recibido,
            "estado": True
        }
        platform.re_init_buffer()
    else:
        response = {
            "messages": [],
            "estado": False
        }

    response = json.dumps(response)
    return response


@app.route('/registrarDispositivo', methods=["POST"])
def peticion_nuevo_dispositivo(): #Funciona asincrona que hace la suscripcion al topic de request y se queda esperando como maximo 20seg para ver si se intenta conectar un nuevo dispositivo
    topic_request = "/topic/request"
    mensaje_recibido = False
    time_out = 20
    time_init = 0
    platform.reboot_client()
    platform.client.loop_start()
    subscribe(platform.client, topic_request)  # Topic para esperar la respuesta con los parametros de la plataforma
    print("Esperando Cliente nuevo")
    while not mensaje_recibido and time_init < time_out:
        if hasattr(platform.client, 'client_id') and hasattr(platform.client, 'tipo_escenario'):
            mensaje_recibido = True
        time.sleep(1)
        time_init += 1
    platform.client.loop_stop()

    #Si se ha recibido un mensaje con los parametros del cliente, se construye un objeto que despues se pasa a JSON para devolverlo a la llamada AJAX de la vista registrar.html
    if mensaje_recibido:
        response = {
            "client_id": str(platform.client.client_id),
            "mensaje": "Cliente nuevo encontrado",
            "tipo": platform.client.tipo_escenario
        }
    else:
        response = {
            "mensaje": "No hay peticiones nuevas"
        }

    response = json.dumps(response)
    return response

@app.route('/intercambio', methods=["POST"])
def intercambio_claves(): #Esta funcion seria el siguiente paso a la peticion de un nuevo dispositivo, y se encarga de realizar la autenticacion segun el escenario y el intercambio de claves pertinente
    mensaje_recibido = False
    autenticado = "True"
    time_out = 20
    time_init = 0
    clave_auth = ''
    numero_random = None
    topic_auth = "/topic/" + platform.client.client_id + "/auth"
    topic_auth_ack = "/topic/" + platform.client.client_id + "/auth/ack"

    if 'clave_auth' in request.form: # Si el escenario es tipo 2, salida, debe leerse el input con el codigo introducico
        clave_auth = request.form['clave_auth']
    if 'numero_random' in request.form:# Si el escenario es tipo 1, entrada, se debe extraer el numero aleatorio generado en el JS
        numero_random = request.form['numero_random']

    if clave_auth != '': #Esc 2
        codigo_auth = KeyUtils().encrypt_message(clave_auth, platform.master_key)
        platform.client.loop_start()
        Mqtt.publish(platform.client, codigo_auth, topic_auth)
        subscribe(platform.client, topic_auth_ack)
        while not mensaje_recibido and time_init < time_out:
            if hasattr(platform.client, 'auth_ack'):
                mensaje_recibido = True
                autenticado = platform.client.auth_ack

            time.sleep(1)
            time_init += 1
        platform.client.loop_stop()

    if numero_random != '0': #Esc 1
        platform.client.loop_start()
        subscribe(platform.client, topic_auth)
        while not mensaje_recibido:
            if hasattr(platform.client, 'clave_auth'):
                mensaje_recibido = True
                num_descifrado = platform.client.clave_auth
                if num_descifrado != numero_random:
                    autenticado = "False"
            time.sleep(1)
            time_init += 1
        confirmacion = KeyUtils.encrypt_message(str(autenticado), platform.master_key)
        Mqtt.publish(platform.client, confirmacion, topic_auth_ack)
        platform.client.loop_stop()

    mensaje_recibido = False
    time_out = 20
    time_init = 0

    if autenticado == "True": #Si la autenticacion es correcta se procede al intercambio de las claves
        topic_new_params = "/topic/newConnect/" + platform.client.client_id + "/params"
        topic_new_pb_plat = "/topic/newConnect/" + platform.client.client_id + "/publicPlatform"
        topic_new_pb_device = "/topic/newConnect/" + platform.client.client_id + "/publicDevice"
        topic_message = "/topic/" + platform.client.client_id + "/message"

        # Se queda escuchando la clave publica del dispositivo
        mensaje_recibido = False
        time_init = 0
        platform.client.loop_start()
        # Parametros
        params_pem = platform.export_parameters()
        time.sleep(5)
        Mqtt.publish(platform.client, params_pem, topic_new_params)
        # Clave publica de la plataforma
        Mqtt.publish(platform.client, platform.a_public_key.public_numbers().y, topic_new_pb_plat)
        subscribe(platform.client, topic_new_pb_device)
        print("Esperando clave p??blica del dispositivo...")
        while not mensaje_recibido and time_init < time_out:
            if hasattr(platform.client, 'b_public_key'):
                mensaje_recibido = True
            time.sleep(1)
            time_init += 1
        platform.client.loop_stop()
        peer_public_numbers = dh.DHPublicNumbers(platform.client.b_public_key, platform.parameters.parameter_numbers())
        b_public_key = peer_public_numbers.public_key(default_backend())
        a_shared_key = platform.a_private_key.exchange(b_public_key)

        key = KeyUtils.convert_key(a_shared_key)
        platform.device_list[platform.client.client_id] = key

        if mensaje_recibido:
            response = {
                "pub_key": b_public_key.public_numbers().y,
                "topic": topic_message,
                "estado": True
            }
        else:
            response = {
                "estado": False
            }

    else:
        response = {
            "estado": False
        }
    platform.re_init_params()
    response = json.dumps(response)
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

