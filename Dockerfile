FROM python:3.8-buster

RUN apt-get update && apt-get install -y wget git libxslt-dev iptables kmod swig3.0
RUN ln -s /usr/bin/swig3.0 /usr/bin/swig


RUN mkdir /usr/src/bounty
WORKDIR /usr/src/bounty

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -r requirements-dev.txt

ENV PYTHONPATH="/usr/src/bounty"
CMD [ "python3", "bounty_agent.py" ]
