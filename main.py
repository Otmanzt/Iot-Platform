
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/registrar')
def registrar():
    return render_template('registrar.html')
@app.route('/listar')
def listar():
    return render_template('listar.html')
@app.route('/selecTopic')
def selecTopic():
    return render_template('selecTopic.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

