import os
import secrets

FRONTEND_URL = os.environ.get('FRONTEND_URL',
                               'http://localhost:5173')

SECRET_KEY = os.environ.get('SESSION_KEY',
                            default=''.join(secrets.token_hex(16)))

# OpenID Connect SSO config
OIDC_ISSUER = os.environ.get('OIDC_ISSUER',
                             'https://sso.csh.rit.edu/auth/realms/csh')

OIDC_REDIRECT_URI = os.environ.get('OIDC_REDIRECT_URI',
                                   'http://localhost:5001/api/redirect_uri')
OIDC_CLIENT_CONFIG = {
    'client_id': os.environ.get('OIDC_CLIENT_ID', ' '),
    'client_secret': os.environ.get('OIDC_CLIENT_SECRET', ' '),
}

GOOGLE_CLIENT_CONFIG = {
    'client_id': os.environ.get('GOOGLE_CLIENT_ID', ' '),
    'client_secret': os.environ.get('GOOGLE_CLIENT_SECRET', ' '),
}

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER',
                               "uploads")

SERVER_PORT = os.environ.get('SERVER_PORT',
                             38281)
PORT_RANGE = os.environ.get('PORT_RANGE',
                            20)
RETRY = os.environ.get('RETRY',
                       PORT_RANGE)