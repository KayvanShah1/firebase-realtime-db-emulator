# FireMongo

![Landing Page](/docs/imgs/landing-page.png)

## About
FireMongo is a project aimed at integrating the functionalities of Firebase Realtime Database with the robust querying and indexing capabilities of MongoDB. The goal is to create a seamless data management system that leverages the strengths of both databases while emulating the RESTful functionalities of Firebase. This project was developed to simplify data operations, enhance data retrieval efficiency, and provide a flexible yet powerful backend for various applications.

## Description

### Main Features

1. **Data Model Design**: Implemented a data model that effectively utilizes MongoDB's querying and indexing features while replicating the JSON structure of Firebase.
2. **RESTful API Endpoints**: Developed comprehensive RESTful API endpoints (GET, POST, PUT, PATCH, DELETE) to manage data operations seamlessly, emulating Firebase's CRUD functionalities.
3. **Rules Configuration**: Configured and managed rules for setting indexes and modifying them to ensure data integrity and optimize query performance.
4. **Automatic API Documentation**: Utilized OpenAPI specification for automatic API documentation, making it easy for developers to understand and use the API.
5. **Deployment**: Packages a lightweight multi-stage Docker image, publishes it to GitHub Container Registry, and deploys it to Render.
6. **Testing**: Uses deterministic pytest unit and integration suites, with an opt-in test against a real MongoDB database.

### Implementations

- **Data Modeling**: Designed two versions of data models. The initial version used a nested document structure, which was later optimized to improve read and write operations.
- **API Development**: Created RESTful API endpoints to handle CRUD operations efficiently, closely following the RESTful functionalities of Firebase.
- **Rules Configuration**: Implemented server-side logic for rules configuration to set and modify indexes, ensuring optimal performance and data integrity.
- **Server-Side Logic**: Implemented complex data filtering and querying to optimize performance.
- **Deployment and Testing**: Deployed the application using Docker, ensuring it is easily portable and manageable across different environments. Conducted extensive testing to ensure reliability and performance.

### Purpose of RESTful API Endpoints

- **GET**: Retrieve data from the database with support for complex filtering and querying.
- **POST**: Create new entries in the database with a flexible data structure.
- **PUT**: Update existing entries with new data, ensuring data integrity and consistency.
- **PATCH**: Partially update specific fields in an existing entry.
- **DELETE**: Remove entries from the database securely and efficiently.
- **Rules Configuration**: Set and modify indexes to optimize query performance and maintain data integrity.

![Landing Page](/docs/imgs/swagger-docs.png)

### Summary

FireMongo aims to bridge the gap between Firebase Realtime Database's JSON structure and MongoDB's powerful querying capabilities, while emulating the RESTful functionalities of Firebase. By leveraging the strengths of both databases, this project provides a robust backend solution for managing complex data operations. The RESTful API endpoints offer a flexible and efficient way to interact with the database, making it a versatile tool for developers. The application is packaged as a multi-stage Docker image and delivered through GitHub Container Registry and Render.

<!-- This project is a REST API for storing and retrieving data documents. It allows
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
and prevent unexpected errors. -->

# Getting Started

## Setup of development environment

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).

2. Create the Python 3.12 environment and install all locked dependencies.

    ```bash
    uv sync
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
    uv run uvicorn app.main:app --reload
    ```

3. Run with Uvicorn multiple workers

    ```bash
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    ```

4. Run with Gunicorn & Uvicorn
    ```bash
    uv run gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    ```

## Tests

The pytest suite runs in-process with an isolated MongoDB-compatible database. It does not use the configured Atlas database or require a running API server.

```bash
uv run pytest
uv run pytest -m unit
uv run pytest -m integration
```

The real-database test is opt-in. It reads `MONGODB_URI`, creates a uniquely named temporary database, verifies the `/health` endpoint and original v2 demo flow, and removes every temporary collection when it finishes:

```bash
uv run pytest -m real_db --real-mongodb
```

The application exposes `GET /health` as a readiness check. It returns HTTP 200 only when MongoDB responds to a ping; unavailable database connections return HTTP 503. The Docker image uses this endpoint for its container health check.

The original university presentation walkthrough is preserved in [docs/university-demo.md](docs/university-demo.md). Its CRUD, query, and index examples are automated in `tests/integration/test_demo_flow.py`.

## Containers and deployment

### Run with Docker Compose

The Compose service builds the production `runtime` stage, listens on port 8080 by default, and reads application settings from `.env`:

```bash
docker compose up --build
```

Override `HOST_PORT`, `PORT`, `IMAGE_NAME`, or `IMAGE_TAG` when needed. The published default-branch image is available at:

```text
ghcr.io/kayvanshah1/firebase-realtime-db-emulator:latest
```

### GitHub Actions

The workflow in `.github/workflows/ci-cd.yml` performs the following gated sequence:

1. Every pull request and every branch push runs the Python 3.12 pytest suite plus Ruff lint and formatting checks.
2. Pull requests and non-default branch pushes build the `linux/amd64` runtime image without publishing it.
3. Successful `main` pushes publish `latest`, branch, and immutable commit-SHA tags to GHCR.
4. After the image is published, the default branch triggers the configured Render service and creates a GitHub deployment record.

### Configure Render

1. Connect the repository as a Render Blueprint using `render.yaml`. It defines the free Singapore `firemongo` image-backed service, its GHCR image, `/health` check, port, generated `SECRET_KEY`, and the required `MONGODB_URI` prompt.
2. If the GHCR package is private, add a GitHub registry credential in Render using a personal access token with `read:packages`. A public package needs no registry credential.
3. The container automatically binds to Render's `PORT` value. Add any additional runtime settings through the Render service environment.
4. Disable Render Auto-Deploy because GitHub Actions owns the deployment trigger.
5. In GitHub, create an environment named `render` and add `RENDER_SERVICE_ID` and `RENDER_API_KEY` as environment secrets. The service ID is shown on the Render service page; create the API key under Render Account Settings.

Until both Render secrets are added, tests and GHCR publishing continue normally and the deployment job reports that Render is not configured.

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

4. [Sebastian Ramirez et al. FastAPI. 2020. [Online].](https://fastapi.tiangolo.com/)

5. [Docker Documentation](https://docs.docker.com/)

6. [GitHub Container Registry Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

7. [Render: Deploy a Prebuilt Docker Image](https://render.com/docs/deploying-an-image)
