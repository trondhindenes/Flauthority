import platform

from helpers.flask_config_helper import ConfigHelper
import os
import time
import sys
import json
from threading import Thread
from subprocess import Popen, PIPE
import subprocess
from Queue import Queue, Empty
from datetime import datetime
from ConfigParser import SafeConfigParser
from flask import render_template
from flask import Flask, request, render_template, session, flash, redirect, url_for, jsonify
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, Api, reqparse, fields
from flask_restful_swagger import swagger
import celery.events.state
from celery import Celery
import log
from ModelClasses import AnsibleCommandModel, AnsiblePlaybookModel, AnsibleExtraArgsModel


#Setup queue for celery
io_q = Queue()

app = Flask(__name__)
auth = HTTPBasicAuth()

config = ConfigHelper.get_config_path()

try:
    appconfig = {}
    appconfig['broker_url'] = ConfigHelper.get_config_variable(config, "Default", "CELERY_BROKER_URL")
    appconfig['result_backend'] = ConfigHelper.get_config_variable(config, "Default", "CELERY_RESULT_BACKEND")
    appconfig['task_timeout'] = int(ConfigHelper.get_config_variable(config, "Default", "CELERY_TASK_TIMEOUT"))
    appconfig['work_folder'] = ConfigHelper.get_config_variable(config, "Default", "work_folder")
    appconfig['ca_config_file'] = ConfigHelper.get_config_variable(config, "Default", "ca_config_file")
    appconfig['ca_cert_file'] = ConfigHelper.get_config_variable(config, "Default", "ca_cert_file")
    appconfig['ca_key_file'] = ConfigHelper.get_config_variable(config, "Default", "ca_key_file")
    appconfig['ca_key_passphrase'] = ConfigHelper.get_config_variable(config, "Default", "ca_key_passphrase")
    appconfig['aws_key'] = ConfigHelper.get_config_variable(config, "Default", "aws_key")
    appconfig['aws_key_secret'] = ConfigHelper.get_config_variable(config, "Default", "aws_key_secret")
    appconfig['aws_bucket_name'] = ConfigHelper.get_config_variable(config, "Default", "aws_bucket_name")
    appconfig['aws_s3_host_name'] = ConfigHelper.get_config_variable(config, "Default", "aws_s3_host_name")
    appconfig['logging_level'] = ConfigHelper.get_config_variable(config, "Default", "logging_level")
    appconfig['ca_c'] = ConfigHelper.get_config_variable(config, "Default", "ca_c")
    appconfig['ca_st'] = ConfigHelper.get_config_variable(config, "Default", "ca_st")
    appconfig['ca_l'] = ConfigHelper.get_config_variable(config, "Default", "ca_l")
    appconfig['ca_o'] = ConfigHelper.get_config_variable(config, "Default", "ca_o")
    appconfig['allow_subject_names'] = ConfigHelper.get_config_variable(config, "Default", "allow_subject_names").split(",")
    appconfig['allow_cert_extension'] = ConfigHelper.get_config_variable(config, "Default", "allow_cert_extension").split(",")
    appconfig['cert_validity_days'] = int(ConfigHelper.get_config_variable(config, "Default", "cert_validity_days"))
    appconfig['auto_add_domain'] = ConfigHelper.get_config_variable(config, "Default", "auto_add_domain")
    appconfig['ca_crl_file'] = ConfigHelper.get_config_variable(config, "Default", "ca_crl_file")
    appconfig['cert_storage_folder'] = ConfigHelper.get_config_variable(config, "Default", "cert_storage_folder")
    appconfig['delete_expired_certs_from_storage_folder'] = ConfigHelper.get_config_variable(config, "Default",
                                                                       "delete_expired_certs_from_storage_folder")
    appconfig['auto_revoke_certs'] = ConfigHelper.get_config_variable(config, "Default", "auto_revoke_certs")
    appconfig['save_client_key_passphrase'] = ConfigHelper.get_config_variable(config, "Default", "save_client_key_passphrase")
    appconfig['flask_clr_path'] = ConfigHelper.get_config_variable(config, "Default", "flask_clr_path")

except:
    print "Unexpected error:", sys.exc_info()[0]
    raise ValueError(str.format("error reading value from config. Missing setting?"))

logging_level = appconfig['logging_level']
try:
    computer_name = os.environ['COMPUTERNAME']
except:
    import platform
    computer_name = platform.node()

logger = log.setup_custom_logger(logging_level)

api = swagger.docs(Api(app), apiVersion='0.1')

celery = Celery(app.name, broker=appconfig['broker_url'], backend=appconfig['result_backend'])

celery.conf.update(appconfig)

'''
inventory_access = []


def get_inventory_access(username, inventory):
    if username == "admin":
        return True
    result = False
    with open("rbac.json") as rbac_file:
        rbac_data = json.load(rbac_file)
    user_list = rbac_data['rbac']
    for user in user_list:
        if user['user'] == username:
            inventory_list = user['inventories']
            if inventory in inventory_list:
                result = True
    return result
'''

@auth.verify_password
def verify_password(username, password):
    result = False
    with open("rbac.json") as rbac_file:
        rbac_data = json.load(rbac_file)
    user_list = rbac_data['rbac']
    for user in user_list:
        if user['user'] == username:
            if user['password'] == password:
                result = True
                inventory_access = user['inventories']
    return result

#routes
import flauthority.api_task_output
import flauthority.api_task_status
import flauthority.api_generatecertificate
import flauthority.api_updatecrl
import flauthority.api_clr
