#!/bin/bash

# Nazarriya LLM Service Deployment Script for Hetzner
# This script sets up the LLM service on a fresh Hetzner server

set -e

echo "🚀 Starting Nazarriya LLM Service deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y curl wget git unzip

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installed successfully"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed successfully"
else
    echo "✅ Docker Compose already installed"
fi

# Create application directory
echo "📁 Setting up application directory..."
APP_DIR="/opt/nazarriya-llm"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Clone repository (if not already present)
if [ ! -d "$APP_DIR/.git" ]; then
    echo "📥 Cloning repository..."
    git clone https://github.com/yourusername/nazarriya.git $APP_DIR
    cd $APP_DIR/nazarriya-llm
else
    echo "📥 Updating repository..."
    cd $APP_DIR/nazarriya-llm
    git pull origin main
fi

# Create environment file
echo "⚙️ Creating environment configuration..."
cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_MODEL=${OPENAI_MODEL:-gpt-3.5-turbo}
OPENAI_EMBEDDING_MODEL=${OPENAI_EMBEDDING_MODEL:-text-embedding-ada-002}

# RAG Configuration
CHUNK_SIZE=${CHUNK_SIZE:-1000}
CHUNK_OVERLAP=${CHUNK_OVERLAP:-200}
MAX_TOKENS=${MAX_TOKENS:-1000}

# Server Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=false
EOF

# Create data directories
echo "📂 Creating data directories..."
mkdir -p data/pdfs data/html chroma_db

# Set proper permissions
echo "🔐 Setting permissions..."
chmod 755 data/pdfs data/html chroma_db

# Build and start the service
echo "🔨 Building and starting the service..."
docker-compose up -d --build

# Wait for service to be ready
echo "⏳ Waiting for service to be ready..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Service is healthy!"
else
    echo "❌ Service health check failed"
    echo "📋 Checking logs..."
    docker-compose logs
    exit 1
fi

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow 8001/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

# Create systemd service (optional, for auto-start)
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/nazarriya-llm.service > /dev/null << EOF
[Unit]
Description=Nazarriya LLM Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR/nazarriya-llm
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Enable and start systemd service
sudo systemctl enable nazarriya-llm.service

# Create monitoring script
echo "📊 Creating monitoring script..."
cat > monitor.sh << 'EOF'
#!/bin/bash
echo "=== Nazarriya LLM Service Status ==="
echo "Service Status:"
sudo systemctl status nazarriya-llm.service --no-pager -l
echo ""
echo "Container Status:"
docker-compose ps
echo ""
echo "Service Health:"
curl -s http://localhost:8001/health | jq . 2>/dev/null || curl -s http://localhost:8001/health
echo ""
echo "RAG Status:"
curl -s http://localhost:8001/rag/status | jq . 2>/dev/null || curl -s http://localhost:8001/rag/status
EOF

chmod +x monitor.sh

# Create backup script
echo "💾 Creating backup script..."
cat > backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/nazarriya-llm"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "Creating backup: $BACKUP_DIR/backup_$DATE.tar.gz"

# Stop service
docker-compose down

# Create backup
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz data/ chroma_db/

# Restart service
docker-compose up -d

echo "Backup completed: $BACKUP_DIR/backup_$DATE.tar.gz"

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# Final status
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Service Information:"
echo "   - Service URL: http://$(curl -s ifconfig.me):8001"
echo "   - Health Check: http://$(curl -s ifconfig.me):8001/health"
echo "   - API Docs: http://$(curl -s ifconfig.me):8001/docs"
echo ""
echo "🔧 Management Commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Restart: docker-compose restart"
echo "   - Stop: docker-compose down"
echo "   - Monitor: ./monitor.sh"
echo "   - Backup: ./backup.sh"
echo ""
echo "📚 Next Steps:"
echo "   1. Ingest your documents using the ingest script"
echo "   2. Test the API endpoints"
echo "   3. Configure your main API to use this service"
echo ""
echo "⚠️  Don't forget to:"
echo "   - Set your OpenAI API key in the .env file"
echo "   - Configure your domain and SSL if needed"
echo "   - Set up monitoring and alerting"
