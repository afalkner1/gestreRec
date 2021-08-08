from flask import Flask, render_template,request
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['host']='0.0.0.0'
app.debug = True
socketio = SocketIO(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    # if request.method == 'POST':
    #     print('request data', request.data)
    return render_template('websocket_test.html')

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)

@socketio.on('json')
def handle_json(json):
    print('received json: ' + str(json))

if __name__ == '__main__':
    socketio.run(app)