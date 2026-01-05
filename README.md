# Meal Planner

A comprehensive meal planning application with multi-user support, recipe management, calendar-based meal planning, and grocery list generation.

## Features

- **User Management**: Registration, authentication with JWT tokens, and multi-user support
- **Recipe Management**: 
  - Create, edit, and organize recipes with detailed information
  - Recipe photos/images upload support
  - Recipe ratings and reviews
  - Adjustable serving sizes
  - Nutritional information tracking (calories, protein, carbs, fat)
  - Prep time and cook time tracking
  - Difficulty levels (easy, medium, hard)
  - Recipe tagging and categorization
  - Favorite recipes
  - **NEW**: Privacy controls (Private, Group, Public)
  - **NEW**: Share recipes with groups
- **Calendar Planning**: 
  - Plan meals by day with interactive calendar view
  - Support for multiple meal types (breakfast, lunch, dinner, snack)
  - Week-by-week meal planning
  - Drag-and-drop meal scheduling
  - **NEW**: Privacy controls (Private, Group, Public)
  - **NEW**: Share calendars with groups
- **Grocery Lists**: 
  - Auto-generate shopping lists from planned meals
  - Smart ingredient consolidation
  - Category-based grouping
  - Check off items as you shop
  - **NEW**: Privacy controls (Private, Group, Public)
  - **NEW**: Share lists with groups
- **Groups & Sharing**: 
  - Create and manage groups
  - Share recipes, calendars, and grocery lists with groups
  - Group admin roles for managing content
- **Admin Dashboard**: 
  - System-wide statistics
  - User management
  - Content moderation
  - Promote users to admin
- **Progressive Web App (PWA)**:
  - Install on any device (iOS, Android, Desktop)
  - Offline functionality with service worker caching
  - Native app-like experience
  - Push notifications ready
  - Auto-updates when new version deployed

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
- **PWA**: vite-plugin-pwa with Workbox

### DevOps
- **Containerization**: Docker and Docker Compose
- **CI/CD**: GitHub Actions
- **Database Migrations**: Alembic
- **Releases & Versioning**: Releases use semantic `vMAJOR.MINOR.PATCH` tags; Docker images (primary artifacts) are pushed to GHCR on tag and released via GitHub Releases (see `RELEASE.md`).

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

2. Quick start (recommended):
```bash
./start.sh
```

Or manually:

2a. Create environment file:
```bash
cp .env.example .env
# Edit .env and update SECRET_KEY and other settings
```

2b. Start all services:
```bash
docker-compose up -d
```

3. Access the application:
- Frontend: http://localhost:3080
- Backend API: http://localhost:8180
- API Documentation: http://localhost:8180/docs

**First Time Setup:**
- Create an account using the Register page
- Start by adding some recipes
- Create a calendar and plan your meals
- Generate grocery lists from your meal plans

**Setting up an Admin User:**

After registering, you can promote your user to admin:

```bash
# Using the helper script
cd backend
python create_admin.py

# Or manually in the database
docker-compose exec postgres psql -U mealplanner -d mealplanner -c "UPDATE users SET is_admin = true WHERE username = 'your_username';"
```

**Or use sample data:**
```bash
./populate-data-docker.sh
```
Then login with username: `demo` and password: `password123`

### Local Development

For local development without Docker:

1. Run the setup script:
```bash
./setup-local.sh
```

Or manually:

#### Backend

1. Navigate to backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e ".[dev]"
```

4. Run database migrations:
```bash
alembic upgrade head
```

5. Start the development server:
```bash
uvicorn app.main:app --reload --port 8180
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

The frontend will be available at http://localhost:3080

## Sample Data

To populate the database with sample recipes, users, and meal plans for testing:

**For Docker setup:**
```bash
./populate-data-docker.sh
```

**For local development:**
```bash
./populate-data.sh
```

This creates 3 users (all password: `password123`), 8 

## Progressive Web App (PWA)

The Meal Planner is a fully functional Progressive Web App that can be installed on any device.

### Testing PWA Locally

```bash
./test-pwa.sh
```

Or manually:
```bash
cd frontend
npm run build
npm run preview
```

Then open Chrome DevTools → Application tab to verify PWA functionality.

### Installing the App

**Desktop (Chrome/Edge):**
1. Visit the app URL
2. Click the install icon in the address bar
3. App opens in standalone window

**Mobile:**
- **iOS**: Safari → Share → Add to Home Screen
- **Android**: Chrome → Menu → Install app

See [PWA_GUIDE.md](PWA_GUIDE.md) for complete PWA documentation including:
- Configuration details
- Caching strategies
- Icon generation
- Production checklist
- Troubleshooting guidedetailed recipes, and pre-planned meals.  
See [SAMPLE_DATA.md](SAMPLE_DATA.md) for full details.

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
- Swagger UI: http://localhost:8180/docs
- ReDoc: http://localhost:8180/redoc

## Project Structure

```
meal-planner/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API endpoints
│   │   ├── models/              # Database models
│   │   ├── schemas/             # Pydantic schemas
│   │WA Guide**: See [PWA_GUIDE.md](PWA_GUIDE.md) for Progressive Web App documentation
- **P   ├── services/            # Business logic
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
├── start.sh                     # Quick start script
├── setup-local.sh               # Local development setup
├── FEATURES.md                  # Feature implementation details
├── TROUBLESHOOTING.md           # Common issues and solutions
├── .github/workflows/           # CI/CD pipelines
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- **Permissions System**: See [PERMISSIONS.md](PERMISSIONS.md) for detailed permissions documentation
- **Quick Start**: See [QUICKSTART_PERMISSIONS.md](QUICKSTART_PERMISSIONS.md) for permissions quick start guide
- **Sample Data**: See [SAMPLE_DATA.md](SAMPLE_DATA.md) for populating test data
- **Documentation**: See [FEATURES.md](FEATURES.md) for detailed feature list
- **Troubleshooting**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- **Issues**: For bugs and questions, please open an issue on GitHub

## License

MIT License