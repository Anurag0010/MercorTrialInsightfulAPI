# Mercor Trial Time Tracker

## Project Overview
A Flask-based API service for time tracking, inspired by Insightful, with support for Azure PostgreSQL and Azure Blob Storage.

## Tech Stack
- Backend: Flask (Python)
- Database: Azure PostgreSQL / SQLite (local development)
- Storage: Azure Blob Storage
- ORM: SQLAlchemy
- Migration: Flask-Migrate

## Local Development Setup

### Prerequisites
- Python 3.8+
- pip
- virtualenv

### Setup Steps
1. Clone the repository
   ```bash
   git clone https://github.com/your-username/mercor-time-tracker.git
   cd mercor-time-tracker
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables
   - Create a `.env` file in the project root
   - Add necessary configuration (database URL, secret keys)

5. Initialize the database
   ```bash
   flask db upgrade
   ```

6. Run the application
   ```bash
   flask run
   ```

## Running Tests
```bash
python -m pytest tests/
```

## Deployment
- Configured for Azure App Service
- Use `requirements.txt` for dependency management

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push and create a Pull Request

## License
[Specify your license here]

# Existing instructions already cover environment variables

```bash
flask db upgrade
```

6. Run the application
```bash
flask run
```

## API Endpoints
- `/api/health`: Health check endpoint
- `/api/employees`: Employee management
- `/api/projects`: Project management
- `/api/tasks`: Task management
- `/api/timelogs`: Time tracking
- `/api/screenshots`: Screenshot management

## Azure Configuration
- Set `AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_KEY` for Blob Storage
- Configure `DATABASE_URL` for PostgreSQL in production

## Testing
```bash
# Run tests
python -m pytest
```

## Deployment
- Use `gunicorn` for production
- Set `FLASK_ENV=production`
- Use Azure App Service or similar PaaS
