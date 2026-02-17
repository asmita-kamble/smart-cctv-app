#!/bin/bash

# Smart CCTV Docker Quick Start Script

set -e

echo "🚀 Smart CCTV Docker Setup"
echo "=========================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL..."
if command -v pg_isready &> /dev/null; then
    if pg_isready &> /dev/null; then
        echo "✅ PostgreSQL is running"
    else
        echo "⚠️  PostgreSQL is not running. Please start PostgreSQL first."
        echo "   macOS: brew services start postgresql@14"
        echo "   Linux: sudo systemctl start postgresql"
        exit 1
    fi
else
    echo "⚠️  pg_isready not found. Please ensure PostgreSQL is installed and running."
fi

# Check if MongoDB is running
echo "🔍 Checking MongoDB..."
if command -v mongosh &> /dev/null; then
    if mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
        echo "✅ MongoDB is running"
    else
        echo "⚠️  MongoDB is not running. Please start MongoDB first."
        echo "   macOS: brew services start mongodb-community"
        echo "   Linux: sudo systemctl start mongod"
        exit 1
    fi
else
    echo "⚠️  mongosh not found. Please ensure MongoDB is installed and running."
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    if [ -f env.docker.example ]; then
        cp env.docker.example .env
        
        # Generate secure keys
        echo "🔐 Generating secure keys..."
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
        JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
        
        # Update .env file with generated keys
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
            sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env
        else
            # Linux
            sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
            sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env
        fi
        
        echo "✅ .env file created with secure keys"
        echo "⚠️  Please review and update .env file if needed:"
        echo "   - Database credentials (POSTGRES_USER, POSTGRES_PASSWORD)"
        echo "   - Database host (POSTGRES_HOST, MONGODB_HOST)"
        echo "   - On Linux, you may need to set host IP instead of host.docker.internal"
    else
        echo "❌ env.docker.example not found. Please create .env manually."
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi

# Create uploads directories
echo "📁 Creating upload directories..."
mkdir -p backend/uploads
mkdir -p uploads
echo "✅ Upload directories created"

# Clean up existing containers and images
echo ""
echo "🧹 Cleaning up existing containers and images..."
# Stop and remove containers, networks, and images built by docker-compose
docker-compose down --rmi local 2>/dev/null || true
echo "✅ Existing containers and images removed"

# Build and start services
echo ""
echo "🔨 Building Docker images (fresh build)..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

# Check backend
if curl -f http://localhost:5001/api/health &> /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend is starting up (this may take a minute)"
fi

# Check frontend
if curl -f http://localhost:3000 &> /dev/null; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️  Frontend is starting up"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo ""
echo "📍 Access Points:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:5001"
echo "   Health Check: http://localhost:5001/api/health"
echo ""
echo "📋 Useful Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart: docker-compose restart"
echo ""
echo "📖 For more information, see DOCKER_SETUP.md"
echo "=========================================="

