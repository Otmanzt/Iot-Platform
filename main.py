
from flask import Flask, render_template, request, redirect, url_for, session
from platform_web import *
import json
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

    platform.client.loop_start()
    subscribe(platform.client, topic)
    platform.client.loop_stop()
    '''
    if mensaje_recibido:
        response = {
            "client_id": str(platform.client.client_id),
            "mensaje": "Cliente nuevo encontrado",
            "estado": True
        }
    else:
        response = {
            "mensaje": "No hay peticiones nuevas",
            "estado": False
        }
    '''
    response = {
        "topic": topic,
        "estado": False
    }
    response = json.dumps(response)
    return response


@app.route('/registrarDispositivo', methods=["POST"])
def peticion_nuevo_dispositivo():
    topic_request = "/topic/request"
    mensaje_recibido = False
    time_out = 20
    time_init = 0

    platform.client.loop_start()
    subscribe(platform.client, topic_request)  # Topic para esperar la respuesta con los parametros de la plataforma
    print("Esperando Cliente nuevo")
    while not mensaje_recibido and time_init < time_out:
        if hasattr(platform.client, 'client_id') and platform.client.client_id is not None:
            mensaje_recibido = True
        time.sleep(1)
        time_init += 1
    platform.client.loop_stop()

    if mensaje_recibido:
        response = {
            "client_id": str(platform.client.client_id),
            "mensaje": "Cliente nuevo encontrado",
            "estado": True
        }
    else:
        response = {
            "mensaje": "No hay peticiones nuevas",
            "estado": False
        }

    response = json.dumps(response)
    return response

@app.route('/intercambio', methods=["POST"])
def intercambio_claves():
    mensaje_recibido = False
    time_out = 20
    time_init = 0

    topic_new_params = "/topic/newConnect/" + platform.client.client_id + "/params"
    topic_new_pb_plat = "/topic/newConnect/" + platform.client.client_id + "/publicPlatform"
    topic_new_pb_device = "/topic/newConnect/" + platform.client.client_id + "/publicDevice"
    topic_message = "/topic/" + platform.client.client_id + "/message"

    # Parametros
    params_pem = platform.export_parameters()
    Mqtt.publish(platform.client, params_pem, topic_new_params)
    # Clave publica de la plataforma
    Mqtt.publish(platform.client, platform.a_public_key.public_numbers().y, topic_new_pb_plat)
    # Se queda escuchando la clave publica del dispositivo
    mensaje_recibido = False
    time_init = 0
    platform.client.loop_start()
    subscribe(platform.client, topic_new_pb_device)
    print("Esperando clave pública del dispositivo...")
    while not mensaje_recibido and time_init < time_out:
        if hasattr(platform.client, 'b_public_key') and platform.client.b_public_key is not None:
            mensaje_recibido = True
        time.sleep(1)
        time_init += 1
    platform.client.loop_stop()
    print(platform.client.b_public_key)
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
    platform.re_init_params()
    response = json.dumps(response)
    return response


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

