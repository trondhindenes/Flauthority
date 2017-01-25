cp test_ca.conf /opt/flauthority/openssl.cnf
mkdir /opt/flauthority
/opt/flauthority
mkdir certs crl newcerts private work
cd /opt/flauthority
openssl genrsa -aes256 -out private/ca.key.pem 4096
openssl req -config openssl.cnf \
      -key private/ca.key.pem \
      -new -x509 -days 7300 -sha256 -extensions v3_ca \
      -out certs/ca.cert.pem