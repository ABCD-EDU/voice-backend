# Speech Separation Backend
To run the server on development mode, use the following commands on the root folder:

### Job API
`python -m uvicorn job.main:app --port 8000 --reload`

### Models API
`python -m uvicorn models.main:app --port 8001 --reload`

> Access the server by going to `127.0.0.1:8000` and `127.0.0.1:8001` <br/>
