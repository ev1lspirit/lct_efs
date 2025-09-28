FROM python:3.12-bullseye

WORKDIR /app

COPY /deployments/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY /fsm /app/fsm
# todo: rm
COPY /deployments/deploy.sh /app/deployments/deploy.sh

RUN chmod +x /app/deployments/deploy.sh
ENTRYPOINT ["sh", "./deployments/deploy.sh"]
