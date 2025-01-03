from app import create_app
from OpenSSL import SSL
from pathlib import Path
try:
    context = SSL.Context(SSL.TLSv1_2_METHOD)
    certs = Path('certs')
    assert certs.exists(), "Cert directory not found"

    context.use_privatekey_file( certs / 'server_key.key')
    context.use_certificate_file(certs / 'server_cert.crt')
except SSL.Error as e:
    print(f"Error loading SSL context: {e}")
    context = None

app = create_app()

if __name__ == '__main__':
    context = None
    if context:
        app.run(debug=True, host='0.0.0.0', port=4000, 
                # ssl_context=context
                ssl_context=('certs/server_cert.crt', 'certs/server_key.key')
                )
    else:
        app.run(debug=True, host='0.0.0.0', port=4000)
