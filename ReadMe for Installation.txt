Hi deleveloper, this is Dev-Jaz of MISD. I created this API using FastAPI and Python.
To use this api, you need to install python and "UVICORN FASTAPI".

Then to serve this as a server, run uvicorn main:app --host 127.0.0.1 --port [PORT] --no-server-header  (see SECURITY.md; set INTERNAL_API_KEY in .env first. --reload is for development only).
Once running, try opening it by typing the IPAddress:PORT.