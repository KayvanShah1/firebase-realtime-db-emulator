# Firebase Realtime Database Emulator

## Setup of development environment

1. Create a new Python environment and activate.

    **Conda** (from scratch)

    ```bash
    export PYTHON_VERSION=3.10.4
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

-   You can the `example.env` file in the root directory
-   Create a new environment file named `.env`
-   Copy the contents of the file and paste it into the `.env` file created
    above
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
