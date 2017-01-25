import os
import shutil
from celery import Celery
import subprocess
from subprocess import Popen, PIPE
from helpers import util_functions
from flauthority import api, app, celery, appconfig
from helpers.util_functions import sign, upload_to_s3, get_utc_string
import zipfile
import logging


logger = logging.getLogger('flauthority')

task_timeout = appconfig['task_timeout']

@celery.task(bind=True)
def generate_certificate(self, task, type='flauthority'):
    with app.app_context():
        has_error = False
        result = None
        output = ""

        self.update_state(state='PROGRESS',
                          meta={'output': output,
                                'description': "",
                                'returncode': None})

        subject_name = task['subject_name']
        cert_extension = task['cert_extension']

        work_folder = appconfig['work_folder']
        ca_config_file = appconfig['ca_config_file']
        ca_cert_file = appconfig['ca_cert_file']
        ca_key_file = appconfig['ca_key_file']
        ca_key_passphrase = appconfig['ca_key_passphrase']
        client_private_key_password = util_functions.randomword(10)
        temp_folder_name = util_functions.randomword(10)
        ca_c = appconfig['ca_c']
        ca_st = appconfig['ca_st']
        ca_l = appconfig['ca_l']
        ca_o = appconfig['ca_o']
        cert_validity_days = appconfig['cert_validity_days']
        auto_add_domain = appconfig['auto_add_domain']
        cert_storage_folder = appconfig['cert_storage_folder']

        if auto_add_domain and auto_add_domain != "":
            subject_name = subject_name + auto_add_domain

        if appconfig['auto_revoke_certs'].lower() == "yes":
            #Check if the cert already exists
            logger.info("Checking for revokeable certificates")
            old_cert_folders = [f for f in os.listdir(cert_storage_folder) if f.startswith(subject_name + "__")]
            if len(old_cert_folders) > 0:
                for folder in old_cert_folders:
                    folder_full_path = os.path.join(cert_storage_folder, folder)
                    logger.debug("revoking old cert in folder " + folder_full_path)
                    old_cert_file = os.path.join(folder_full_path, subject_name + ".cert.pem")
                    # Revoke certificate
                    revoke_command = str.format('cd {0}'
                                                '&&openssl ca -config {1} -revoke {2} -passin {3}',
                                                folder_full_path, ca_config_file, old_cert_file, ca_key_passphrase)
                    logger.debug(str.format("About to execute: {0}", revoke_command))
                    proc = Popen([revoke_command], stdout=PIPE, stderr=subprocess.STDOUT, shell=True)

                    for line in iter(proc.stdout.readline, ''):
                        logger.debug(str(line))
                        output = output + line
                        meta = {'output': '', 'description': "", 'returncode': None}
                        self.update_state(state='PROGRESS', meta=meta)

                    return_code = proc.poll()

                    if return_code is not 0:
                        logger.error("error revoking cert returned exit code " + str(return_code))
                        raise RuntimeError("error revoking cert returned exit code " + str(return_code))
                    if appconfig['delete_expired_certs_from_storage_folder'].lower() == "yes":
                        logger.info("deleting foler " + folder_full_path)
                        shutil.rmtree(folder_full_path)


        cmd = str.format('cd {0}'
                             '&& mkdir {4}'
                             '&& cd {4}'
                             '&& echo generating client private key passphrase'
                             '&& echo {3} > {1}.passphrase.txt'
                             '&& echo generating client private key'
                             '&& openssl genrsa -aes256 -out {1}.key.pem -passout file:{1}.passphrase.txt 2048'
                             '&& echo generating client csr'
                             '&& openssl req -config {2} -key {1}.key.pem -new -sha256 -out {1}.csr.pem -passin file:{1}.passphrase.txt -subj "/C={7}/ST={8}/L={9}/O={10}/CN={1}"'
                             '&& echo signing cert'
                             '&& openssl ca -config {2} -extensions {6} -days {11} -notext -md sha256 -in {1}.csr.pem -out {1}.cert.pem -passin {5} -batch -notext',
                             work_folder, subject_name, ca_config_file, client_private_key_password,
                             temp_folder_name, ca_key_passphrase, cert_extension, ca_c, ca_st, ca_l, ca_o,
                             str(cert_validity_days))


        logger.debug(str.format("About to execute: {0}", cmd))
        proc = Popen([cmd], stdout=PIPE, stderr=subprocess.STDOUT, shell=True)
        for line in iter(proc.stdout.readline, ''):
            logger.debug(str(line))
            output = output + line
            meta = {'output': '', 'description': "", 'returncode': None}
            self.update_state(state='PROGRESS', meta=meta)

        return_code = proc.poll()

        if return_code is not 0:
            logger.error("error generating cert returned exit code " + str(return_code))
            raise RuntimeError("error generating cert returned exit code " + str(return_code))
        if return_code is 0:
            #fail
            pass

            aws_key = appconfig['aws_key']
            aws_key_secret = appconfig['aws_key_secret']
            aws_bucket_name = appconfig['aws_bucket_name']
            work_folder = appconfig['work_folder']
            aws_s3_host_name = appconfig['aws_s3_host_name']
            cert_storage_folder = appconfig['cert_storage_folder']

            current_dir = os.path.join(work_folder, temp_folder_name)
            if os.path.isdir(current_dir):
                pass
            else:
                raise ValueError(str.format("directory {0} does not exist!!", current_dir))

            zip_file = os.path.join(current_dir, 'certificate.zip')
            logger.debug("zip_file:" + zip_file)
            zf = zipfile.ZipFile(zip_file, mode='w')
            zf.write(os.path.join(current_dir, subject_name + ".cert.pem"), subject_name + ".cert.pem")
            zf.write(os.path.join(current_dir, subject_name + ".key.pem"), subject_name + ".key.pem")
            zf.write(os.path.join(current_dir, subject_name + ".passphrase.txt"), subject_name + ".passphrase.txt")
            zf.write(os.path.join(current_dir, subject_name + ".csr.pem"), subject_name + ".csr.pem")
            zf.write(ca_cert_file, "root.ca.pem")

            zf.close()

            url = upload_to_s3(access_key=aws_key, access_key_secret=aws_key_secret, bucket_name=aws_bucket_name,
                         file_path=zip_file, dest_file_name=subject_name + ".zip",
                         aws_s3_host_name=aws_s3_host_name, sign=True)

            os.remove(zip_file)

            if appconfig['save_client_key_passphrase'].lower() == "yes":
                pass
            else:
                passphrase_file = os.path.join(current_dir, subject_name + ".passphrase.txt")
                logger.info("removing passphrase file: " + passphrase_file)
                os.remove(passphrase_file)



            cert_dest_folder = get_utc_string()
            cert_dest_folder = subject_name + "__" + cert_dest_folder
            dest_folder = os.path.join(cert_storage_folder, cert_dest_folder)
            shutil.copytree(current_dir, dest_folder)
            shutil.rmtree(current_dir)

            meta = {'output': url, 'description': "", 'returncode': return_code}
            self.update_state(state='FINISHED', meta=meta)

        else:
            meta = {'output': "", 'description': str.format("Celery ran the task, but {0} reported error", type),
                    'returncode': return_code}
            self.update_state(state='FAILED', meta=meta)

        return meta

@celery.task(bind=True)
def update_crl(self, task, type='flauthority'):
    with app.app_context():
        cmd = task
        output = ""
        self.update_state(state='PROGRESS',
                          meta={'output': output,
                                'description': "",
                                'returncode': None})
        logger.debug(str.format("About to execute: {0}", cmd))
        proc = Popen([cmd], stdout=PIPE, stderr=subprocess.STDOUT, shell=True)
        for line in iter(proc.stdout.readline, ''):
            logger.debug(str(line))
            output = output + line
            meta = {'output': output, 'description': "", 'returncode': None}
            self.update_state(state='PROGRESS', meta=meta)

        return_code = proc.poll()

        aws_key = appconfig['aws_key']
        aws_key_secret = appconfig['aws_key_secret']
        aws_bucket_name = appconfig['aws_bucket_name']
        aws_s3_host_name = appconfig['aws_s3_host_name']
        ca_crl_file = appconfig['ca_crl_file']

        logger.info("uploading crl file:" + ca_crl_file)
        url = upload_to_s3(access_key=aws_key, access_key_secret=aws_key_secret, bucket_name=aws_bucket_name,
                           file_path=ca_crl_file, dest_file_name="flauthority_clr.pem",
                           aws_s3_host_name=aws_s3_host_name, sign=True)
        meta = {'output': output, 'description': "", 'returncode': return_code}
        logger.debug("output: " + output)
        self.update_state(state='FINISHED', meta=meta)
