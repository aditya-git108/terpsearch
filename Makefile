export DB_MODE=DEV

terpsearch: dist/ build/
	# Clean previous builds
	rm -rf dist build *.egg-info

	# Build package
	python3 -m build

	# Install locally for testing
	pip3 install .

app-prod:
	export FLASK_MODE=DEV && \
	make terpsearch && \
	hypercorn app:app --reload -b 0.0.0.0:5000
#	DB_MODE=DEV gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000

app-local:
	docker compose down --remove-orphans dynamodb-local dynamodb
	docker compose up -d --remove-orphans dynamodb-local dynamodb
	export DB_MODE=DEV
	make
	hypercorn app:app --reload -b 127.0.0.1:5000

terpsearch-test:
	export FLASK_MODE=PROD && \
	make terpsearch && \
	DB_MODE=DEV python3 -m flask run --host=0.0.0.0 --port=5000

terpsearch-dev:
	export FLASK_MODE=PROD && \
	make terpsearch && \
	DB_MODE=DEV gunicorn app:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000

terpsearch-prod:
	export FLASK_MODE=PROD && \
	make terpsearch && \
	DB_MODE=PROD gunicorn app:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000

push-to-ecr:
	aws ecr get-login-password --region us-east-1 | \
	docker login --username AWS --password-stdin 314702103122.dkr.ecr.us-east-1.amazonaws.com

	docker tag terpsearch-app:latest 314702103122.dkr.ecr.us-east-1.amazonaws.com/terpsearch:terpsearch-app
	docker tag fastapi:latest 314702103122.dkr.ecr.us-east-1.amazonaws.com/terpsearch:fastapi
	docker tag celery:latest 314702103122.dkr.ecr.us-east-1.amazonaws.com/terpsearch:celery

	# Push each image to ECR
	docker push 314702103122.dkr.ecr.us-east-1.amazonaws.com/terpsearch:terpsearch-app
	docker push 314702103122.dkr.ecr.us-east-1.amazonaws.com/terpsearch:fastapi
	docker push 314702103122.dkr.ecr.us-east-1.amazonaws.com/terpsearch:celery

compose-db:
	docker compose up -d --remove-orphans dynamodb-local dynamodb


install_requirements: requirements.txt
	pip3 install -r requirements.txt