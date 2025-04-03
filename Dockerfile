FROM amazonlinux:latest

RUN dnf install -y python3 python3-pip
RUN dnf update -y

RUN mkdir /terpsearch_msml
WORKDIR /terpsearch_msml


COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . /terpsearch_msml
RUN pip3 install -e /terpsearch_msml

ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
ENV FLASK_APP=app.py

EXPOSE 5000
EXPOSE 8000
EXPOSE 8001

CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=5000"]