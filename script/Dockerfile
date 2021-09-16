FROM bioformat:latest

RUN apk add py3-pip
RUN pip3 --version 

WORKDIR /app
COPY app/requirements.txt . 
RUN pip3 install -r requirements.txt
COPY app/manager.py ./manager.py 