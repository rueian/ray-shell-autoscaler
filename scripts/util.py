import random
import OpenSSL
import tempfile

def generate_tls_certificate(ou, cn):
    cert_seconds_to_expiry = 60 * 60 * 3  # 3 hours
    key = OpenSSL.crypto.PKey()
    key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
    cert = OpenSSL.crypto.X509()
    cert.get_subject().OU = ou
    cert.get_subject().CN = cn
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(cert_seconds_to_expiry)
    cert.set_serial_number(random.getrandbits(64))
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    return {
        'key': OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key),
        'crt': OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    }

def tempwrite(data):
    f = tempfile.NamedTemporaryFile()
    f.write(data)
    f.flush()
    return f