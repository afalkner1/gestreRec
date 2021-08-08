from flask import Flask, flash, redirect, request, send_file, abort, render_template, Response, stream_with_context
from flask_restful import Resource, Api, url_for
from flask_socketio import SocketIO
from werkzeug.utils import secure_filename
import json, os
import cv2
import threading
import base64
from PIL import Image
import io
import numpy as np
import time

def readb64(base64_string):
    sbuf = io.BytesIO()
    sbuf.write(base64.b64decode(base64_string))
    pimg = Image.open(sbuf)
    return cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)


UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4'}

scoreboard = []

from get_video import *


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>Gesture Recognition</title> </head>\n<body>'''
instructions = '''
    <p><em>Gesture Recognition</em>:</p>'''
home_link = '<p><a href="/">Back</a></p>\n'
footer_text = '</body>\n</html>'

jumping_jack = cv2.imread('jumping_jack.jpg')
img_str_bytes = cv2.imencode('.jpg', jumping_jack)[1].tobytes()
# EB looks for an 'application' callable by default.
application = app = Flask(__name__)
api = Api(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'secret!'
app.config['host']='0.0.0.0'
app.debug = True
socketio = SocketIO(app)
detector = Detect()

# camera = cv2.VideoCapture(0)
not_started = cv2.imread('not_started.jpg')

def gen_frames():
    while True:
        image = detector.image
        try:
            try:
                img_str = cv2.imencode('.jpg', image)[1].tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + img_str + b'\r\n')
                last_img_str = img_str
            except:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + last_img_str + b'\r\n')
        except:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + img_str_bytes + b'\r\n')

def webcam_gen_frames():
    while True:

        success, frame = True , not_started #camera.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


### https://stackoverflow.com/questions/55736527/how-can-i-yield-a-template-over-another-in-flask/55755716
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        print('request data', request.data)
        if len(request.form['YouTube URL']) > 10:
            YT_URL = request.form['YouTube URL']
            YT_watchID = YT_URL.split('v=')[1]
            print('starting detection on: ' + YT_watchID)
            variable = request.form['dances']
            detector.start(YT_watchID,variable)
        # if  len(request.form['Stop Video']) > 10 :
        #     YT_URL =request.form['YouTube URL']
        #     YT_watchID = YT_URL.split('v=')[1]
        #     detector.start(YT_watchID)
    return render_template('controls_and_stream.html')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/webcam')
def webcam():
    return Response(webcam_gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/end')
def currentstatus():
    average = round((sum(scores)/len(scores))*10,1)
    detector.stop_vid()
    return render_template('files.html', variable= average)

@socketio.on('json')
def handle_json(json_data):
    start = time.time()
    img_data = json.loads(json_data["data"])["image"].split('base64,')[1]
    # print('img_data',img_data)
    # print('json_data',json_data)
    sec_data = json_data["seconds"]
    ms_data = json_data["milliseconds"]
    epoch = json_data["epoch"]
    print('sec_data',sec_data)
    print('ms_data',ms_data)
    print('epoch',epoch)
    # img_data = json_data.split('base64,')[1].split('"}''')[0]
    # print('json_data',json_data)
    # print('img_data',img_data)

    
    t1 = time.time()
    print('epoch',epoch,'time',t1,"diff", start - t1)
    cvimg = readb64(img_data)
    t2 = time.time()
    cv2.imshow('this',cvimg)
    t3 = time.time()
    # print('split data', t1-start)
    # print('read64', t2-t1)
    # print('imshow',t3-t2)
    cv2.waitKey(1)
    # input("wait")
    # cv2.destroyAllWindows()


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    # application.debug = True
## for hppts -> https://blog.miguelgrinberg.com/post/running-your-flask-application-over-https

    # application.run()
    socketio.run(app)