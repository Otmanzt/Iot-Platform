
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
    return render_template('listar.html')


@app.route('/selecTopic')
def selecTopic():
    return render_template('selecTopic.html')

@app.route('/registrarDispositivo', methods=["POST"])
def peticion_nuevo_dispositivo():
    topic_request = "/topic/request"
    mensaje_recibido = False
    time_out = 20
    time_init = 0

    platform.client.loop_start()
    Mqtt.subscribe(platform.client, topic_request)  # Topic para esperar la respuesta con los parametros de la plataforma
    print("Esperando Cliente nuevo")
    while not mensaje_recibido and time_init < time_out:
        if platform.client.msg_payload:
            mensaje_recibido = True
        time.sleep(1)
        time_init += 1
    platform.client.loop_stop()

    response = {
        "client_id": str(platform.client.msg_payload[0])
    }

    response = json.dumps(response)
    return response

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

