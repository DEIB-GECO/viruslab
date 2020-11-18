import json
import os
import time
import urllib
import uuid
from urllib.request import urlopen

import flask
from flask import Flask, abort, redirect, request
from flask_executor import Executor
from flask_cors import CORS
from flask_mail import Mail, Message

CONF = {
    "host":  "http://127.0.0.1:5000/",
    "base_url" : "/virusurf-eit",
    "virusviz" : "http://genomic.elet.polimi.it/virusviz/static/#!/home",
    "mail_enabled" : True,
    "mail_address" : "virusurf@aol.com",
    "mail_password" : "pvrmfhswyzhfvled"
}

CONF["jsonApi"] =  CONF["host"]+CONF["base_url"]+"/api/json/"

os.environ["FLASK_DEBUG"] = "1"


app = Flask(__name__,static_url_path=CONF["base_url"] + '', static_folder='./static')
cors = CORS(app, resources={r"/virusurf-eit/api/*": {"origins": "*"}})

# MAIL CONFIG
app.config['MAIL_SERVER']='smtp.aol.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = CONF["mail_address"]
app.config['MAIL_PASSWORD'] = CONF["mail_password"]
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

executor = Executor(app)

with app.app_context():
    logger = flask.current_app.logger
    STATUS = dict()
    JSON = dict()

    mail = Mail(app)

# Redirect to /virusviz-eit
@app.route('/')
def hello():
    return redirect(CONF["base_url"], code=302)


# Serve static content
@app.route(CONF["base_url"] + '/')
def root():
    return app.send_static_file('index.html')


def generateUUID():
    return str(uuid.uuid4())

def setJSON(id, pythonDictionary):
    JSON[id] = json.dumps(pythonDictionary);
    STATUS[id]["ready"] = True;

    sendEmail(id, True)


def setError(id, errorMessage) :
    STATUS[id]["failed"] = "True"
    STATUS[id]["errorMessage"] = "True"

    sendEmail(id, False)



def sendEmail(id, success):
    if not CONF["mail_enabled"]:
        logger.debug("mail is disables")
        return
    if "notifyTo" in STATUS[id] and STATUS[id]["notifyTo"].strip() != '':

        to = STATUS[id]["notifyTo"].strip()
        logger.debug("sending email to " + to)
        logger.debug(app.config['MAIL_USERNAME'])
        logger.debug(app.config['MAIL_PASSWORD'])

        status = 'SUCCESS' if success else 'FAILED'
        landing = CONF["host"]+CONF["base_url"]+"/"+id
        msg = Message('ViruSurf-EIT Execution '+to, sender = CONF['mail_address'], recipients = [to])
        msg.body = "Dear User, \n the execution status of your computation has changed to "+status+"."
        if success :
            msg.body = msg.body + "\n\n  The result is available at the following address: \n "
        msg.body = msg.body +landing

        mail.send(msg)
        logger.debug("SENT")


# Long computation goes here
# success: you call  setJSON(id, json_as_python_dictionary)
# error: you call setError(id, errorMessage)
def compute(id, fastaText, metaText):

    time.sleep(5)

    # Here I am just loading an example json from file
    try:
        with open('./static/result.json') as json_file:

            data = json.load(json_file)
            setJSON(id,data)

    except:
        # if it fails:
        setError(id, "Error reading the example JSON file");




# UPLOAD API
@app.route(CONF["base_url"] + '/api/upload/', methods=['POST'])
def upload():
    email = request.form.get('emailAddress')
    fasta = request.form.get('fastaText')
    meta = request.form.get('metaText')

    id = generateUUID()

    logger.debug(id)
    logger.debug(email)

    STATUS[id] = {
        "ready": False,
        "failed": False,
        "failedMessage": "",
        "notifyTo": email,
        "jsonAddress": urllib.parse.quote(CONF["jsonApi"])+id,
        "virusVizAddress": CONF["virusviz"]
    }

    def async_function():
        try:
            compute(id, fasta, meta)

        except Exception as e:
            STATUS[id] = {
                "ready": False,
                "failed": True,
                "failedMessage": "Unknown server exeption"
            }

            logger.error("Exeption occurred in the executor. ")
            logger.error("Async error", e)

            raise e

    executor.submit(async_function)

    return json.dumps(
        {"id": id}
    )

@app.route(CONF["base_url"] + '/api/json/<string:id>', methods=['GET'])
def getJson(id):
    if id in JSON:
        return JSON[id]
    else:
        abort(404)

@app.route(CONF["base_url"] + '/api/upload/status/<string:id>', methods=['GET'])
def getStatus(id):
    logger.debug("asking status")
    logger.debug(id)
    if id in STATUS:
        return STATUS[id]
    else:
        abort(404)


if __name__ == '__main__':
    app.run()
