import os
from flask_restful import Resource, Api
from flask_restful_swagger import swagger
from flask_restful import reqparse
from flauthority import api, app, auth, appconfig, appconfig
from ModelClasses import RequestResultModel, GenerateCertificateModel
from helpers import util_functions
import celery_runner

class UpdateCrl(Resource):
    @swagger.operation(
        notes='updates the crl',
        nickname='updatecrl',
        responseMessages=[
            {
                "code": 200,
                "message": "CRL updating completed"
            },
            {
                "code": 400,
                "message": "stuff happened"
            }
        ]
    )
    @auth.login_required
    def post(self):
        ca_config_file = appconfig['ca_config_file']
        ca_crl_file = appconfig['ca_crl_file']
        ca_key_passphrase = appconfig['ca_key_passphrase']
        aws_key = appconfig['aws_key']
        aws_key_secret = appconfig['aws_key_secret']
        aws_bucket_name = appconfig['aws_bucket_name']
        aws_s3_host_name = appconfig['aws_s3_host_name']
        flask_clr_path = appconfig['flask_clr_path']

        task_timeout = appconfig['task_timeout']
        command = str.format('openssl ca -config {0} -gencrl -out {1} -passin {2}',
                             ca_config_file, ca_crl_file, ca_key_passphrase)

        task = celery_runner.update_crl.delay(command)
        #result = task.wait(timeout=None, interval=0.2)
        #task_result = celery_runner.update_crl.AsyncResult(task.id)
        #task_result.get()
        #output = task_result['output']

        task.get(timeout=1)


        util_functions.download_from_s3(access_key=aws_key, access_key_secret=aws_key_secret,
                                        bucket_name=aws_bucket_name, src_file_name="flauthority_clr.pem"
                                        , dest_file_name="flauthority_clr.pem", dest_file_path=flask_clr_path,
                                        aws_s3_host_name=aws_s3_host_name)
        print(task)

api.add_resource(UpdateCrl, '/api/updatecrl')