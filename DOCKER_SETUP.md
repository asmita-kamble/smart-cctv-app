# Docker Setup Guide

This guide will help you run the Smart CCTV application using Docker, making it easy to deploy on any system without worrying about dependencies.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose 2.0+
- **PostgreSQL 12+** installed and running on your host system
- **MongoDB 4.4+** installed and running on your host system

## Quick Start

### 1. Clone and Navigate

```bash
cd smart-cctv-app
```

### 2. Set Up Databases on Host System

**PostgreSQL Setup:**
```bash
# Create database (if not exists)
psql -U postgres -c "CREATE DATABASE smart_cctv;"

# Verify PostgreSQL is running
pg_isready
```

**MongoDB Setup:**
```bash
# Verify MongoDB is running
mongosh --eval "db.adminCommand('ping')"
```

### 3. Configure Environment Variables

Copy the example environment file and update it:

```bash
cp env.docker.example .env
```

Edit `.env` and set your values:
- `SECRET_KEY` - Generate a secure random key
- `JWT_SECRET_KEY` - Generate a secure random key
- `POSTGRES_HOST` - Use `host.docker.internal` (macOS/Windows) or your host IP (Linux)
- `POSTGRES_USER` - Your PostgreSQL username
- `POSTGRES_PASSWORD` - Your PostgreSQL password
- `MONGODB_HOST` - Use `host.docker.internal` (macOS/Windows) or your host IP (Linux)

**Generate secure keys:**
```bash
# On macOS/Linux
python3 -c "import secrets; print(secrets.token_hex(32))"

# Or use openssl
openssl rand -hex 32
```

### 4. Build and Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5001
- **API Health Check**: http://localhost:5001/api/health

### 6. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database data)
docker-compose down -v
```

## Service Details

### Services Included

1. **Backend** - Flask API (port 5001) - connects to host databases
2. **Frontend** - React app served via Nginx (port 3000)

### Database Configuration

**Important:** This Docker setup uses databases installed on your host system, not containerized databases.

- **PostgreSQL** - Must be installed and running on your host system
- **MongoDB** - Must be installed and running on your host system

The backend container connects to host databases using:
- **macOS/Windows Docker Desktop**: `host.docker.internal`
- **Linux**: `host.docker.internal` (via extra_hosts) or use `network_mode: host`

### Volumes

- `./backend/uploads` - Uploaded files (mounted from host)
- `./uploads` - Alternative upload location

## Common Commands

### View Running Containers

```bash
docker-compose ps
```

### Restart a Service

```bash
docker-compose restart backend
docker-compose restart frontend
```

### Rebuild After Code Changes

```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Rebuild all services
docker-compose build
docker-compose up -d
```

### Execute Commands in Containers

```bash
# Access backend container shell
docker-compose exec backend bash

# Access PostgreSQL (from host system)
psql -U postgres -d smart_cctv

# Access MongoDB (from host system)
mongosh
```

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend

# Follow logs
docker-compose logs -f backend
```

## Creating Admin User

After starting the services, create an admin user:

```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "Admin123!",
    "role": "admin"
  }'
```

## Development Workflow

### Hot Reload (Development)

For development with hot reload, you can mount your code:

1. Modify `docker-compose.yml` to add volume mounts for code:

```yaml
backend:
  volumes:
    - ./backend:/app
    - ./backend/uploads:/app/uploads
```

2. Use a development Dockerfile or override the command:

```yaml
backend:
  command: python run.py
  environment:
    FLASK_ENV: development
```

### Running Tests

```bash
# Run tests in backend container
docker-compose exec backend python -m pytest
```

## Troubleshooting

### Services Won't Start

1. **Check logs:**
   ```bash
   docker-compose logs
   ```

2. **Check if ports are already in use:**
   ```bash
   # macOS/Linux
   lsof -i :5001
   lsof -i :3000
   lsof -i :5432
   lsof -i :27017
   ```

3. **Rebuild containers:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Database Connection Issues

1. **Verify databases are running on host:**
   ```bash
   # Check PostgreSQL
   pg_isready
   
   # Check MongoDB
   mongosh --eval "db.adminCommand('ping')"
   ```

2. **Verify database credentials in `.env`:**
   - Ensure `POSTGRES_HOST` is set correctly:
     - macOS/Windows: `host.docker.internal`
     - Linux: `host.docker.internal` or your host IP (e.g., `172.17.0.1`)
   - Ensure `MONGODB_HOST` is set correctly
   - Verify database credentials match your host system

3. **For Linux users:** If `host.docker.internal` doesn't work:
   ```bash
   # Option 1: Find your Docker host IP
   ip addr show docker0 | grep inet
   
   # Option 2: Use network_mode: host in docker-compose.yml
   # Add to backend service:
   network_mode: host
   ```

4. **Check backend logs for connection errors:**
   ```bash
   docker-compose logs backend
   ```

### Backend Build Fails (dlib/face-recognition)

The Dockerfile includes all necessary build dependencies. If it still fails:

1. **Clear Docker cache:**
   ```bash
   docker-compose build --no-cache backend
   ```

2. **Check available disk space:**
   ```bash
   docker system df
   ```

### Frontend Can't Connect to Backend

1. **Check network:**
   ```bash
   docker network ls
   docker network inspect smart-cctv-app_smart-cctv-network
   ```

2. **Verify backend is running:**
   ```bash
   curl http://localhost:5001/api/health
   ```

3. **Check nginx configuration** in `frontend/nginx.conf`

### Permission Issues with Uploads

```bash
# Fix permissions
sudo chown -R $USER:$USER backend/uploads
sudo chown -R $USER:$USER uploads
```

## Production Deployment

### Security Considerations

1. **Change all default passwords** in `.env`
2. **Use strong SECRET_KEY and JWT_SECRET_KEY**
3. **Set FLASK_ENV=production**
4. **Use reverse proxy** (nginx/traefik) in front of services
5. **Enable HTTPS** with SSL certificates
6. **Restrict database ports** (don't expose 5432, 27017 publicly)
7. **Use secrets management** (Docker secrets, AWS Secrets Manager, etc.)

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Backup Strategy

```bash
# Backup PostgreSQL (from host system)
pg_dump -U postgres smart_cctv > backup.sql

# Backup MongoDB (from host system)
mongodump --db smart_cctv_metadata --out ./backup

# Backup uploads
tar -czf uploads-backup.tar.gz backend/uploads uploads
```

## Cleanup

### Remove Everything

```bash
# Stop and remove containers, networks
docker-compose down

# Remove images
docker-compose down --rmi all

# Note: Database data on host system is not affected
```

### Clean Docker System

```bash
# Remove unused containers, networks, images
docker system prune

# Remove everything including volumes (WARNING: destructive)
docker system prune -a --volumes
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- Backend Setup: See `backend/SETUP.md`
- Frontend Setup: See `frontend/README.md`

