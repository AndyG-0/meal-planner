# Meal Planner

A comprehensive meal planning application with multi-user support, recipe management, calendar-based meal planning, and grocery list generation.

## Features

- **User Management**: Registration, authentication with JWT tokens, and multi-user support
- **Recipe Management**: Create, edit, and organize recipes with detailed information
- **Calendar Planning**: Plan meals by day with calendar view
- **Grocery Lists**: Auto-generate shopping lists from planned meals
- **Groups & Sharing**: Share calendars and recipes with groups

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL (with SQLite support for development)
- **ORM**: SQLAlchemy with Alembic migrations
- **Authentication**: JWT tokens with bcrypt password hashing
- **Caching**: Redis
- **Package Management**: uv

### Frontend
- **Framework**: React 18 with Vite
- **UI Library**: Material-UI (MUI)
- **State Management**: Zustand
- **Routing**: React Router
- **HTTP Client**: Axios

### DevOps
- **Containerization**: Docker and Docker Compose
- **CI/CD**: GitHub Actions
- **Database Migrations**: Alembic

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for local development)
- uv package manager

### Running with Docker Compose

1. Clone the repository:
```bash
git clone https://github.com/AndyG-0/meal-planner.git
cd meal-planner
```

2. Create environment file:
```bash
cp .env.example .env
# Edit .env and update SECRET_KEY and other settings
```

3. Start all services:
```bash
docker-compose up -d
```

4. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Local Development

#### Backend

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies with uv:
```bash
uv pip install -e .
uv pip install -e ".[dev]"
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the development server:
```bash
uvicorn app.main:app --reload
```

#### Frontend

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

## Running Tests

### Backend Tests
```bash
cd backend
pytest tests/ --cov=app
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## Linting

### Backend
```bash
cd backend
ruff check app/
mypy app/
```

### Frontend
```bash
cd frontend
npm run lint
```

## Database Migrations

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Environment Variables

See `.env.example` for all available configuration options.

### Key Variables

- `SECRET_KEY`: Secret key for JWT token generation (change in production!)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins

## API Documentation

The API documentation is automatically generated and available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
meal-planner/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API endpoints
│   │   ├── models/              # Database models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── utils/               # Utility functions
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   └── main.py              # FastAPI app
│   ├── tests/                   # Backend tests
│   ├── alembic/                 # Database migrations
│   ├── pyproject.toml           # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API services
│   │   ├── store/               # State management
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .github/workflows/           # CI/CD pipelines
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.