# Troubleshooting Guide

## Common Issues and Solutions

### Frontend Issues

#### Port 3080 is already in use
If you see "Port 3080 is in use", Vite will automatically use the next available port (e.g., 3081).

**Solution:**
- Use the port shown in the terminal output
- Or stop the other process using port 3080
- Update `vite.config.js` to use a different port

#### Cannot connect to API
**Symptoms:**
- Login fails with network error
- "Failed to load recipes" errors

**Solutions:**
1. Verify backend is running:
   ```bash
   curl http://localhost:8180/api/v1/docs
   ```

2. Check `.env` file in frontend:
   ```
   VITE_API_URL=http://localhost:8180/api/v1
   ```

3. Check browser console for CORS errors
4. Verify proxy settings in `vite.config.js`

#### White screen / App won't load
**Solutions:**
1. Check browser console for errors
2. Clear browser cache and local storage
3. Rebuild frontend:
   ```bash
   cd frontend
   rm -rf node_modules dist
   npm install
   npm run build
   ```

### Backend Issues

#### Database connection errors
**Symptoms:**
- "could not connect to server"
- "database does not exist"

**Solutions:**
1. For Docker setup, ensure database is healthy:
   ```bash
   docker-compose ps
   docker-compose logs db
   ```

2. For local setup, ensure PostgreSQL is running:
   ```bash
   psql -U mealplanner -d mealplanner
   ```

3. Check DATABASE_URL in `.env`

#### Migration errors
**Symptoms:**
- "Target database is not up to date"
- Table doesn't exist errors

**Solutions:**
1. Check migration status:
   ```bash
   cd backend
   alembic current
   alembic history
   ```

2. Run migrations:
   ```bash
   alembic upgrade head
   ```

3. If migrations are corrupted:
   ```bash
   # Backup data first!
   alembic downgrade base
   alembic upgrade head
   ```

#### Import errors
**Symptoms:**
- ModuleNotFoundError
- Cannot import name

**Solutions:**
1. Ensure virtual environment is activated:
   ```bash
   source backend/.venv/bin/activate
   ```

2. Reinstall dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Docker Issues

#### Services won't start
**Solutions:**
1. Check Docker is running:
   ```bash
   docker info
   ```

2. Check service logs:
   ```bash
   docker-compose logs backend
   docker-compose logs db
   ```

3. Rebuild containers:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

#### Database data lost after restart
**Solution:**
Ensure you're not using `docker-compose down -v` which removes volumes.

To preserve data:
```bash
docker-compose down  # WITHOUT -v flag
docker-compose up -d
```

### Authentication Issues

#### "Invalid credentials" on login
**Solutions:**
1. Verify username (not email) is being used
2. Register a new account if needed
3. Check backend logs for authentication errors

#### Token expired errors
**Solutions:**
1. Logout and login again
2. Clear browser local storage
3. Check token expiration settings in backend `.env`

### Development Issues

#### Changes not reflecting
**Frontend:**
1. Ensure dev server is running with `--reload`
2. Clear browser cache
3. Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)

**Backend:**
1. Ensure using `--reload` flag with uvicorn
2. Check for Python syntax errors in logs
3. Restart the server

#### CORS errors
**Symptoms:**
- "blocked by CORS policy" in browser console

**Solutions:**
1. Check `BACKEND_CORS_ORIGINS` in backend `.env`:
   ```
   BACKEND_CORS_ORIGINS=["http://localhost:3080","http://localhost:5173","http://localhost:3081"]
   ```

2. Restart backend after changing CORS settings

### Performance Issues

#### Slow page loads
**Solutions:**
1. Check API response times in Network tab
2. Ensure database indices exist (check migrations)
3. Monitor container resources:
   ```bash
   docker stats
   ```

#### High memory usage
**Solutions:**
1. Limit Docker memory in Docker Desktop settings
2. Check for memory leaks in browser console
3. Reduce number of simultaneous recipes loaded

## Getting Help

1. Check application logs:
   ```bash
   # Docker
   docker-compose logs -f backend
   docker-compose logs -f frontend
   
   # Local
   # Check terminal where services are running
   ```

2. Check browser console (F12)

3. Verify API is working:
   - Visit http://localhost:8180/docs
   - Try API endpoints directly

4. GitHub Issues:
   - Search existing issues
   - Create new issue with:
     - Steps to reproduce
     - Error messages
     - Environment info (OS, Docker version, etc.)

## Reset Everything

If all else fails, start fresh:

```bash
# Stop all containers
docker-compose down -v

# Remove all Docker images
docker-compose down --rmi all

# Remove frontend dependencies
rm -rf frontend/node_modules frontend/dist

# Remove backend environment
rm -rf backend/.venv
rm backend/meal_planner.db

# Start over
./start.sh  # For Docker
# or
./setup-local.sh  # For local dev
```

⚠️ **Warning:** This will delete all data! Backup first if needed.
