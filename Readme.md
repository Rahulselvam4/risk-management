# Setup Instructions

## Prerequisites
- Python 3.8+
- Docker Desktop
- MySQL Server

## Installation Steps

### 1. Clone and Setup Virtual Environment
```bash
cd risk-management-dashboard
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env and fill in your actual values:
# - Database credentials (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD)
# - JWT secret key
# - Email SMTP settings (for Gmail, use App Password)
```

### 4. Initialize Database
```bash
# Run the init.sql script in your MySQL server
mysql -u root -p < init.sql
```

## Running the Application

Open **4 separate terminals** and run the following commands:

### Terminal 1: Docker (Kafka & Zookeeper)
```bash
docker-compose up -d 
```

### Terminal 2: Backend API
```bash
venv\Scripts\activate
cd backend
python main.py
```

### Terminal 3: Kafka Consumer
```bash
venv\Scripts\activate
cd backend
python kafka_consumer.py
```

### Terminal 4: Frontend Dashboard
```bash
venv\Scripts\activate
cd frontend
python app.py
```

## Access the Application

- **Frontend Dashboard**: http://localhost:8050
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Stopping the Application

1. Press `Ctrl+C` in each terminal to stop the services
2. Stop Docker containers:
   ```bash
   docker-compose down
   ```

## Troubleshooting

- **Kafka connection issues**: Ensure Docker containers are fully started before running backend/consumer
- **Database errors**: Verify MySQL is running and credentials in .env are correct
- **Port conflicts**: Check if ports 8000, 8050, 29092 are available
