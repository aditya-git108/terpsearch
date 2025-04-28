TerpSearch
TerpSearch is a scalable, FastAPI-based web application that enables users to perform real-time searches, manage user sessions, and explore trending topics.
It integrates a DynamoDB backend for storage and uses Celery for background processing, wrapped with a Dockerized deployment setup.

✨ Features
🔎 Real-time Search: Perform fast keyword-based searches with immediate results.
🧩 Basic User Authentication: Allow users to sign up and log in
📈 Trend Analysis: Explore trending topics and view trend charts.
🛠️ Background Tasks: Lightweight background processing using Celery.
🌐 DynamoDB Integration: Secure user session and data management through AWS DynamoDB.
🐳 Docker Support: Easy deployment and orchestration using Docker Compose.
🌍 Web Interface: Built with clean HTML templates and JavaScript frontend for smooth user experience.

🛠️ Project Structure
terpsearch-master/
├── app.py                # Main application entry
├── docker-compose.yml    # Orchestration for services
├── Dockerfile             # Application containerization
├── setup.py, pyproject.toml # Packaging
├── requirements.txt       # Python dependencies
├── terpsearch/             # Main application code
│   ├── website/            # Web UI (templates, static files, views)
│   ├── search/             # Search engine logic
│   ├── dynamodb/           # DynamoDB session management
│   ├── constants/          # Global constants
├── fastapi_categorizer/    # Separate service for categorization
│   ├── fastapi_app.py      # FastAPI app for categorizer
│   ├── celery_worker.py    # Background tasks
│   ├── categorizer.py      # Text categorization logic
│   └── Dockerfile
└── setup_scripts/          # Helper scripts

🚀 Quick Start
1. Clone the repository
git clone https://github.com/your_username/terpsearch.git
cd terpsearch

2. Build and Run (using Docker)
docker-compose up --build
App will run at: http://localhost:8000
Categorizer service will run separately as part of Docker setup.

3. Local Development (without Docker)
Install dependencies:
pip install -r requirements.txt
Run the app:
uvicorn app:app --reload

⚙️ Environment Variables
Make sure to configure the following environment variables when deploying:
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
DYNAMODB_REGION
You can set them manually or use a .env file.

🐳 Docker Overview
To rebuild and run containers:
docker-compose up --build
To stop containers:
docker-compose down
