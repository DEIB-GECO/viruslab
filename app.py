import gzip
import json
import os
import time
import urllib
import uuid
from io import BytesIO

import flask
from flask import Flask, abort, redirect, request, render_template, send_from_directory, send_file
from flask_executor import Executor
from flask_cors import CORS
from flask_mail import Mail, Message

from support import setupMailConfig, computeVCF

import consensus_analysis as ca

# Import Configuration
with open('config.json') as json_file:
    CONF = json.load(json_file)

    if CONF["debug"]:
        os.environ["FLASK_DEBUG"] = "1"

    CONF["jsonApi"] = CONF["host"] + CONF["base_url"] + "/api/json/"

# Setup Flask APP
app = Flask(__name__,static_url_path=CONF["base_url"] + '', static_folder='./static')
cors = CORS(app, resources={r"/virusurf-eit/api/*": {"origins": "*"}})

executor = Executor(app)

with app.app_context():
    logger = flask.current_app.logger
    STATUS = dict()
    JSON = dict()

    VCF = dict()

    VCF_TEMP_DIR = "tmp_vcf/"

    setupMailConfig(app, CONF)
    mail = Mail(app)

# Redirect to /virusviz-eit
@app.route('/')
def hello():
    return redirect(CONF["base_url"], code=302)

# Serve static content
@app.route(CONF["base_url"] + '/')
def root():
    return app.send_static_file('index.html')

# Generatea unique ID associated to each computation
def generateUUID():
    return str(uuid.uuid4())

# Set the JSON result of a computation and notify the user
def setJSON(id, pythonDictionary):
    JSON[id] = json.dumps(pythonDictionary, cls=ca.NpEncoder);
    STATUS[id]["ready"] = True;

    sendEmail(id, True)

# Set the error status for a compuation and notify the user
def setError(id, errorMessage) :
    STATUS[id]["failed"] = "True"
    STATUS[id]["failedMessage"] = errorMessage

    sendEmail(id, False)


def setParsedSequences(id, num) :
    STATUS[id]["parsedSequences"] = num


# Handle files upload and start the computation
@app.route(CONF["base_url"] + '/api/vcf-download/', methods=['POST'])
def getVCF():
    variants_json = request.form.get('json')
    variants = json.loads(variants_json)

    id = generateUUID()
    logger.debug(id)

    JSON[id] = {
        "ready": False,
        "failed": False,
    }

    def async_function():
        try:
            # do computation here
            computeVCF(variants, VCF_TEMP_DIR, id)

            JSON[id] = {
                "ready": True
            }
        except Exception as e:
            JSON[id] = {
                "ready": False,
                "failed": True,
                "failedMessage": "VCF could not be generated."
            }
            logger.error("Async error", e)
            raise e

    executor.submit(async_function)

    return json.dumps({"id": id})

# Handle files upload and start the computation
@app.route(CONF["base_url"] + '/api/upload/', methods=['POST'])
def upload():
    email = request.form.get('emailAddress')
    fasta = request.form.get('fastaText')
    meta = request.form.get('metaText')

    id = generateUUID()
    logger.debug(id)

    STATUS[id] = {
        "ready": False,
        "failed": False,
        "failedMessage": "",
        "notifyTo": email,
        "jsonAddress": urllib.parse.quote(CONF["jsonApi"])+id,
        "virusVizAddress": CONF["virusviz"],
        "startedAt": int(round(time.time() * 1000))
    }

    JSON[id] = {"ready":False}

    def async_function():
        try:
            process(id, fasta, meta)
        except Exception as e:
            STATUS[id] = {
                "ready": False,
                "failed": True,
                "failedMessage": "Unknown server exeption"
            }
            logger.error("Async error", e)
            raise e

    # Start the asynchronous computation
    executor.submit(async_function)

    # Reply with the computation ID
    return json.dumps({"id": id})

# Process the uploaded files (@pietro,@arif)
def process(id, fastaText, metaText):

    # success: you call  setJSON(id, json_as_python_dictionary)
    # error: you call setError(id, errorMessage)
    # setParsedSequences(id, num)
    try:
        sequences, metadata = ca.parse_inputs(fastaText, metaText)
        setParsedSequences(id, len(metadata.keys()))

        pipeline_json = ca.pipeline(sequences, metadata)

        #with open("result_test.json", "w") as f:
        #    f.write(pipeline_json)

        setJSON(id, pipeline_json)
    except ca.InputException as e:
        print(f"\n\n{e.msg}\n\n")
        setError(id, e.msg)
    except Exception as e:
        print(type(e))
    # EXAMPLE:
    #setParsedSequences(id, 2)

    #try:
    #    with open('./static/big_result.json') as json_file:
    #        data = json.load(json_file)
    #        time.sleep(20)
    #        setJSON(id,data)
    #except:
    #    setError(id, "Error reading the example JSON file");


# Get the result of a computation (VirusViz will call this)
@app.route(CONF["base_url"] + '/api/json/<string:id>', methods=['GET'])
def getJson(id):
    if id in JSON:
        return JSON[id]
    else:
        abort(404)

# Get the status of a computation
@app.route(CONF["base_url"] + '/api/upload/status/<string:id>', methods=['GET'])
def getStatus(id):
    logger.debug("asking status")
    logger.debug(id)
    if id in STATUS:
        return STATUS[id]
    else:
        abort(404)

# Get the status of a computation
@app.route(CONF["base_url"] + '/api/vcf-download/status/<string:id>', methods=['GET'])
def getStatusVCF(id):
    logger.debug("asking vcf status")
    logger.debug(id)
    if id in JSON:
        return JSON[id]
    else:
        abort(404)

# Download VCF file
@app.route(CONF["base_url"] + '/api/vcf-download/<string:id>')
def downloadVCF(id):
    logger.debug("asking download")
    logger.debug(id)

    path = VCF_TEMP_DIR+id+".vcf.gz"

    memory_file = BytesIO()

    with open(path, 'rb') as file:
        memory_file.write(file.read())
        memory_file.seek(0)

        return send_file(memory_file, attachment_filename='variants.vcf.gz', as_attachment=True, mimetype="application/x-compressed")


# Send a notification about the completion of a computation if an email was provided
def sendEmail(id, success):
    if not CONF["mail_enabled"]:
        logger.debug("mail is disables")
        return

    if "notifyTo" in STATUS[id] and STATUS[id]["notifyTo"].strip() != '':

        to = STATUS[id]["notifyTo"].strip()
        logger.debug("sending email to " + to)
        logger.debug(app.config['MAIL_USERNAME'])
        logger.debug(app.config['MAIL_PASSWORD'])

        landing = CONF["host"]+CONF["base_url"]+"/#!/"+id

        subject = "Processing completed." if(success) else "Execution failed."

        msg = Message(subject, sender = CONF['mail_address'], recipients = [to])
        if success:
            msg.body = "Dear User, \n your sequences were successfully processed.\n\n The results are available on this page:\n"
        else:
            msg.body = "Dear User, \n unfortunately, we were not able to process your sequences.\n\n Further details are available on this page:\n"

        msg.body = msg.body + landing

        mail.send(msg)

        logger.debug("Email Sents")


if __name__ == '__main__':
    app.run()