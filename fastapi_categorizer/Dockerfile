FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

COPY . .

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r fastapi_categorizer/requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt
#RUN make

EXPOSE 8010
EXPOSE 6379

#CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8010"]
