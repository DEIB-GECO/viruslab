import time
from vcf_downloads.vcf_generator import save_compressed_vcf_from_json


def setupMailConfig(app, CONF):
    app.config['MAIL_SERVER']='smtp.aol.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = CONF["mail_address"]
    app.config['MAIL_PASSWORD'] = CONF["mail_password"]
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True


def computeVCF(data, folder, id):
    file_path = folder + id + ".vcf.gz"
    save_compressed_vcf_from_json(data, file_path)
    f = open(file_path, "w")
    f.write("file containing VCF - request id " + id)
    f.close()