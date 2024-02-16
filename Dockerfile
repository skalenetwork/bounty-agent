FROM python:3.11-bookworm

RUN apt update && apt install build-essential libssl-dev swig --yes


RUN mkdir /usr/src/bounty
WORKDIR /usr/src/bounty

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -r requirements-dev.txt

ENV PYTHONPATH="/usr/src/bounty"
CMD [ "python3", "bounty_agent.py" ]
