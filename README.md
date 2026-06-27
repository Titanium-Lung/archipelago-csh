# CSH Archipelago

An Archipelago hosting website for the Computer Science House

## How to run

First, choose with branch you want to run. The default branch is `dev`, but `main` is the most stable version. 

Clone this project, then go into the `backend` folder and create a `.env` file. 

This contains: 

```
OIDC_ISSUER=https://sso.csh.rit.edu/auth/realms/csh
OIDC_REDIRECT_URI=http://localhost:5001/redirect_uri
OIDC_CLIENT_ID=client_id
OIDC_CLIENT_SECRET=client_secret
```

Reach out to an RTP for the client id and secret. 

In the `frontend` folder, create a `.env` file with: `VITE_BACKEND_URL=http://localhost:5001`. 

This URL can be changed if you prefer, but the backend Dockerfile and docker-compose.yml have port 5001 exposed. 

### Run with Docker

Once you have the .env files, go to the root of the project in your terminal and enter: 

`docker-compose up --build` 

Then visit http://localhost:5173 to view the website. Note that logging in with Google will not work. 

### Run without Docker

Once you have the .env files, go to the `backend` folder in your terminal and enter the following. If you wish to use a venv, activate it first. 

`pip install -r requirements.txt`

Then go to the `frontend` folder and enter: 

`npm install`

In the `backend`, run `python3 app.py` to start the backend. You will need to use a version of Python above 3.11.9 but below 3.14 due to the Archipelago source code.

In the `frontend`, run `npm run dev`. 

Then visit http://localhost:5173 to view the website. Note that logging in with Google will not work. 
