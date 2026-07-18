# Environment Variables

The list of environment variables that can be used for this project are listed below. These can be placed in a `.env` file in the correct folder (backend or frontend). 

## Backend

**FRONTEND_URL**

Default: http://localhost:5173

The URL that the frontend is being hosted at. 

**OIDC_ISSUER**

Default: https://sso.csh.rit.edu/auth/realms/csh

The URL that the CSH credentials for auth are hosted at (probably something like that).

**OIDC_REDIRECT_URI**

Default: http://localhost:5001/api/redirect_uri

A valid redirect uri for CSH auth.

**OIDC_CLIENT_ID**

The client id of the CSH auth client being used.

**OIDC_CLIENT_SECRET**

The client secret of the CSH auth client being used.

**GOOGLE_CLIENT_ID**

The client id of the Google auth client being used.

**GOOGLE_CLIENT_SECRET**

The client secret of the Google auth client being used.

**UPLOAD_FOLDER**

Default: uploads

The name of the folder to place uploaded archipelago files into.

**SERVER_PORT**

Default: 38281

The beginning of the range of ports for the archipelago servers to use.

**PORT_RANGE**

Default: 20

How many ports the archipelago servers should use. 

**RETRY**

Default: PORT_RANGE

How many times an archipelago server should try again when trying to find a port. 

**DB_HOST**

Default: db

The location that the database is being hosted at.

**DB_NAME**

Default: postgres

The name of the database.

**DB_USER**

Default: postgres

The username of the user that connections to the database will use. 

**DB_PASS**

Default: mysecretpassword

The password of the user that connections to the database will use.

## Frontend

**VITE_BACKEND_URL**

The url that the backend is being hosted at. 