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

```
docker-compose up --build
```

Then visit http://localhost:5173 to view the website. Note that logging in with Google will not work. 

### Run without Docker

Once you have the .env files, go to the `backend` folder in your terminal and enter the following. If you wish to use a venv, activate it first. 

```
pip install -r requirements.txt
```

Then go to the `frontend` folder and enter: 

```
npm install
```

In the `backend`, run `python3 app.py` to start the backend. You will need to use a version of Python above 3.11.9 but below 3.14 due to the Archipelago source code.

In the `frontend`, run `npm run dev`. 

Then visit http://localhost:5173 to view the website. Note that logging in with Google will not work. 

## Architecture

This project uses a React frontend to make calls to a Flask backend. 

The frontend takes in a zip file and sends it to the backend, which extracts it and stores it. As a subprocess, the backend runs MultiServer.py (in the Archipelago source code) using the .archipelago file contained in the zip to start up an archipelago server. All save data from the archipelago server is written by the Archipelago source to a .apsave file in the same directory as the .archipelago. The .apsave and .archipelago files are read by the backend to send information about the archipelago to the frontend. 

### Restarting the rooms

All archipelago rooms that are stored are restarted when the program boots up, using the information the backend writes to a json file in the same directory as the .archipelago and .apsave for each room. 

## Planned features

* Collapsible tables
* Store information about users such as amount of checks gotten 
* Make the autoscrolling for the log not stupid