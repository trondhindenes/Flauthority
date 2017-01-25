### Flauthority  
A lightweight CA with a rest api, built with Flask, Celery and redis. 

Make a http/json request to flauthority, get a link back to a zip file containing the generated certificate, key, passphrase, root ca. All the things. Fully swaggerized.

### Run as container
- Use docker-compose to spin up 3 containers; frontend, backend, redis

Frontend: Where the web app runs
Backend: This is the "ca server", and executes certificate signing requests using celery
Redis: Database for celery


- Required configuration
You can specify confiration either using config.ini or env variables. If they collide, env variables will win.
If you just want to test this thing, here's what you HAVE to change

AWS S3: flauthority uses aws s3 for cert storage, and crl temp storage. You need to fill inn 
an access key, secret, bucket name and region, either in the env vars section in docker compose, or in config ini 
(make sure to remove the empty env vars from the compose file if using config.ini). 
You can use separate keys for frontend and backend. Backend must have 
write access to the bucket, both need list/read/download access to the bucket 

# Recommended configuration
- Make sure you protect the ca key passphrase. The default config.ini sets this to `pass:hello`, but you can also use
openssl syntax `path:<full path to text file>`, which is a much better option

- Make sure you use a persistent volume for the backend container and map it to the /opt/flauthority path, 
so that you don't lose your CA data! If recreating/scaling the frontend you should make sure you 
hit the `POST:/api/updatecrl` against each of the frontend containers, as this will download an actual copy of the crl
and make it available for the frontend.

- Logging: Use the environmental value log_level to control logging level, valid options are 
warning (default), info, debug.   
If you change the loglevel using config.ini (and not the env variable), celery itself will 
run with the default loglevel of warning

### Generate a CA using the default openssl file
Run this inside the backend container after it's started the first time in order to generate the certificate:  

Get into the container by issuing `docker exec -it <backend-container-id> /bin/bash`

Note that you have to make sure that the Country/state/locality/Company name you type in when you enter the commands below
are the same as the one in the config.ini file! By default those will be:
```
CA cert key passphrase: hello
Country: NO
State or Province: Norway
Locality Name: Oslo
Organization Name: Test
Common Name: TestCA
(the other options can be left blank)
```

Then run (command by command, the openssl commands dont work well with multi-line pasteing):
```
cp /opt/flauthority_app/utils/test_ca.conf /opt/flauthority/openssl.cnf
cd /opt/flauthority
mkdir newcerts
mkdir private
mkdir certs
mkdir crl
openssl genrsa -aes256 -out /opt/flauthority/private/ca.key.pem 4096   
openssl req -config openssl.cnf \
      -key private/ca.key.pem \
      -new -x509 -days 7300 -sha256 -extensions v3_ca \
      -out certs/ca.cert.pem
touch index.txt
touch index.txt.attr
echo 1000 > serial
echo "01" > crlnumber
openssl ca -config openssl.cnf -cert certs/ca.cert.pem -gencrl -out /opt/flauthority/crl/ca.crl.pem \
    -keyfile /opt/flauthority/private/ca.key.pem
```

### Access it
Get to know the default stuff using the included swagger ui:
http://<frontend_ip>:<frontend_port>/api/spec.html

In essence the important bits are:
- /api/generatecertificate: Generate a certificate. This operation outputs a job id which you use to 
grab the url of the zip containing the generated cert
- updatecrl: regenerate the crl and copy it to the frontend
- /api/crl: This serves as the revocation list endpoint, and this url should be added to the 
cert "templates" in `/opt/flauthority/openssl.cnf` on the backend server, for instance:
```
[ server_cert ]
# ... snipped ...
crlDistributionPoints = URI:http://mystuff.com/api/crl
```
the default username and password of the web interface is admin:admin, 
a better role based access system is in the works!

### Resources
https://blogs.technet.microsoft.com/pki/2006/11/30/basic-crl-checking-with-certutil/
https://jamielinux.com/docs/openssl-certificate-authority/create-the-root-pair.html
https://skippylovesmalorie.wordpress.com/2010/02/12/how-to-generate-a-self-signed-certificate-using-pyopenssl/
http://russellsimpkins.blogspot.no/2015/10/consul-adding-tls-using-self-signed.html
https://datacenteroverlords.com/2012/03/01/creating-your-own-ssl-certificate-authority/
http://www.shellhacks.com/en/HowTo-Create-CSR-using-OpenSSL-Without-Prompt-Non-Interactive
http://www.gettingcirrius.com/2012/06/automating-creation-of-certificate.html
