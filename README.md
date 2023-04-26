# FireMongo

This project is a REST API for storing and retrieving data documents. It allows
users to create new data documents by sending a POST request to the API
endpoint.

The API supports the creation of multiple data documents at once, each
identified by a unique ID. The created documents are stored in a MongoDB
database.

The API also supports retrieving data documents by their ID, using a GET request
to the appropriate endpoint. The project uses Python and the FastAPI web
framework, with asynchronous programming using the asyncio library. It also uses
the PyMongo library for interfacing with MongoDB.

The API includes error handling and input validation to ensure data integrity
and prevent unexpected errors.

# Getting Started

## Setup of development environment

1. Create a new Python environment and activate.

    **Conda** (from scratch)

    ```bash
    export PYTHON_VERSION=3.10.10
    conda create --name fastapi python=PYTHON_VERSION
    conda activate fastapi
    ```

    **Conda environment.yml file**

    ```bash
    conda env create -f conda-environment.yml
    ```

    **Virtual environment**

    ```bash
    python -m venv ENV
    source ENV/bin/activate
    ```

2. Install dependencies in your environments

    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    ```

## Setup Environment Variables for the App

### Requirements

-   You need have you own MongoDB Atlas Cluster
-   Get the connection details including the URI, username and password

### Creating a .env file

-   Create a new environment file named `.env`
-   Copy the environment variables from `example.env` file from the root
    directory and paste it into the `.env` file created above
-   Add the MongoDB Atlas URI with username and password next to the
    `MONGODB_URI` environment variable
-   To generate a the secret key, run the following command:
    ```bash
    openssl rand -hex 32
    ```

## Run the APP

### Locally

Run the command below in the terminal

1. Linux

    ```bash
    scripts/server.sh
    ```

2. Windows

    ```cmd
    uvicorn app.main:app --reload
    ```

3. Run with Uvicorn multiple workers

    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    ```

4. Run with Gunicorn & Uvicorn
    ```bash
    gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    ```

## Deploy

## Deploy on Docker

-   Build the docker image with the following tag

    ```bash
    docker build . -t {DOCKERHUB_USERNAME}/firebase-realtime-db-emulator:latest
    ```

-   Create and run the container

    ```bash
    docker compose up
    ```

## Deploy on Okteto

```bash
okteto login
okteto deploy --build
```

# About

The theme of this semester’s project was emulation where the goal was to develop
a prototype system that emulates the interface and working of a big data system.

Project Developed for `DSCI 551: Foundations of Data Management` | Spring 2023

Developed By `Kayvan Shah` | `M.S. in Applied Data Science` |
`University of Southern California`

# References

1. [Firebase. (n.d.). Use the Firebase Realtime Database REST API](https://firebase.google.com/docs/database/rest/start)

2. [The MongoDB documentation](https://docs.mongodb.com/)

3. [MongoDB Atlas. (2021). Cloud-hosted MongoDB](https://www.mongodb.com/cloud/atlas)

4. [Okteto. (2021). Okteto Cloud Documentation. Okteto Cloud.](https://okteto.com/docs/home)

5. [Sebastian Ramirez et al. FastAPI. 2020. [Online].](https://fastapi.tiangolo.com/)

6. [Deta. (n.d.). Deta Space Documentation](https://docs.deta.sh/docs/space/about)

7. [Docker. (2021). Docker Documentation](https://docs.docker.com/)
