import os
import shutil
from flauthority import app, config
from helpers.flask_config_helper import ConfigHelper
import platform

def create_dir_if_missing(path):
    print("Creating dir " + path)
    if not os.path.exists(path):
        os.makedirs(path)

frontend = False

if os.environ.get('Flauthority_Backend'):
    if os.getenv('Flauthority_Backend', 'False').lower().strip() == 'true':
        print("bootstrapping backend")
        work_folder = ConfigHelper.get_config_variable(config, "Default", "work_folder")
        cert_storage_folder = ConfigHelper.get_config_variable(config, "Default", "cert_storage_folder")
        create_dir_if_missing(work_folder)
        create_dir_if_missing(cert_storage_folder)

        ca_cert_file = ConfigHelper.get_config_variable(config, "Default", "ca_cert_file")
        ca_key_file = ConfigHelper.get_config_variable(config, "Default", "ca_key_file")
        ca_config_file = ConfigHelper.get_config_variable(config, "Default", "ca_config_file")

        if not os.path.exists(ca_cert_file):
            print("CA Certificate not found. You need to exec into the container to set up the following:")
            print("CA Cert file: " + ca_cert_file)
            print("CA key file: " + ca_key_file)
            print("Openssl CA config file: " + ca_config_file)
            print("")
            print("")
            print("")
else:
    frontend = True

if os.environ.get('Flauthority_Frontend'):
    if os.getenv('Flauthority_Frontend', 'False').lower().strip() == 'true':
        print("bootstrapping frontend")
        frontend = True

if frontend is True:
    flask_clr_path = ConfigHelper.get_config_variable(config, "Default", "flask_clr_path")
    flask_run_debug = ConfigHelper.get_config_variable(config, "Default", "flask_run_debug", default_value='false')
    if flask_run_debug.lower() == "true":
        print("running flask with Debug on")
        run_debug = True
    else:
        run_debug = False

    create_dir_if_missing(flask_clr_path)

    if __name__ == '__main__':
        app.run(debug=run_debug, host=config.get("Default", "Flask_tcp_ip"), use_reloader=False,
                port=int(config.get("Default", "Flask_tcp_port")))