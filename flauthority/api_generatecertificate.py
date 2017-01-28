import os
from flask_restful import Resource, Api
from flask_restful_swagger import swagger
from flask_restful import reqparse
from flauthority import api, app, auth, appconfig, appconfig
from flask import make_response
from ModelClasses import RequestResultModel, GenerateCertificateModel
from helpers import util_functions
import celery_runner
import logging

logger = logging.getLogger('flauthority')

class GenerateCertificate(Resource):
    @swagger.operation(
        notes='Generate certificate',
        nickname='generatecertificate',
        responseClass=RequestResultModel.__name__,
        parameters=[
            {
              "name": "body",
              "description": "Inut object",
              "required": True,
              "allowMultiple": False,
              "dataType": GenerateCertificateModel.__name__,
              "paramType": "body"
            }
          ],
        responseMessages=[
            {
              "code": 200,
              "message": "Certificate generation command started"
            },
            {
              "code": 400,
              "message": "Invalid input"
            }
          ]
    )


    @auth.login_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('subject_name', type=str, help='need to specify certificate subject name', required=True)
        parser.add_argument('cert_extension', type=str, help='need to specify certificate extension', required=True)
        parser.add_argument('cert_lifetime_days', type=int, help='need to specify certificate extension', required=False)
        args = parser.parse_args()
        subject_name = args['subject_name'].lower()
        cert_extension = args['cert_extension']

        max_cert_lifetime = int(appconfig['max_cert_lifetime'])

        if args['cert_lifetime_days']:
            cert_lifetime_days = int(args['cert_lifetime_days'])
        else:
            default_cert_lifetime = int(appconfig['default_cert_lifetime'])
            cert_lifetime_days = default_cert_lifetime


        if cert_lifetime_days > max_cert_lifetime:
            msg = str.format("Cert lifetime requested ({0})is larger than max cert lifetime",
                                      str(cert_lifetime_days), str(max_cert_lifetime))
            logger.warning(msg)
            return make_response(msg, 400)

        curr_user = auth.username()

        task_timeout = appconfig['task_timeout']
        task_obj = {
            'subject_name': subject_name,
            'cert_extension': cert_extension,
            'validity_days': str(cert_lifetime_days)
        }

        allow_cert_extension = appconfig['allow_cert_extension']
        allow = [x for x in allow_cert_extension if x.strip() == cert_extension]
        if len(allow) == 0:
            logger.warning(str.format("Template requested: {1}, allowed extension: {1}", cert_extension,
                                      str(allow_cert_extension)))
            return make_response("Invalid cert extension", 400)

        task_result = celery_runner.generate_certificate.apply_async([task_obj], soft=task_timeout, hard=task_timeout)
        result = {'task_id': task_result.id}
        return result

api.add_resource(GenerateCertificate, '/api/generatecertificate')
