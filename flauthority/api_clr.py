import os
from flask_restful import Resource, Api
from flask_restful_swagger import swagger
from flask_restful import reqparse
from flask import Flask, request, send_from_directory, send_file
from flauthority import api, app, auth, appconfig, appconfig

class SendCrl(Resource):
    @swagger.operation(
        notes='this is where the crl lives',
        nickname='crl',
        responseMessages=[
            {
                "code": 200,
                "message": "you got the crl"
            },
            {
                "code": 400,
                "message": "stuff happened"
            }
        ]
    )
    def get(self):
        flask_clr_path = appconfig['flask_clr_path']
        crl_file = os.path.join(flask_clr_path, "flauthority_clr.pem")
        return send_file(crl_file, mimetype="application/pkix-crl, application/x-pkcs7-crl")

api.add_resource(SendCrl, '/api/crl')
