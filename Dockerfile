FROM python:3.10.10-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt ./

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# this is to help prevent installing requirements everytime we update our
# source code, this is cause docker has a caching system.
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# uvicorn app.main:app --host 0.0.0.0 --port 8000 
CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080" ]