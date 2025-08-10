FROM python:3-slim

COPY pbxding.py /app/
COPY requirements.txt /app/

WORKDIR /app
RUN PIP_ROOT_USER_ACTION=ignore pip install -r requirements.txt

EXPOSE 8000

# Code file to execute when the docker container starts up (`entrypoint.sh`)
ENTRYPOINT ["python", "./pbxding.py"]
