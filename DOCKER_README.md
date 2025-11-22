# Toyota Bot Docker Setup

This directory contains Docker configuration for running the Toyota Telegram Bot in a containerized environment.

## Files Created

- `Dockerfile` - Main Docker image configuration
- `docker-compose.yml` - Docker Compose service definition
- `.dockerignore` - Files to exclude from Docker build context

## Prerequisites

1. **Docker** and **Docker Compose** installed
2. **Environment file** (`.env`) with your Telegram bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
# Build and run the bot
docker-compose up -d

# View logs
docker-compose logs -f toyota-bot

# Stop the bot
docker-compose down
```

### Option 2: Using Docker directly

```bash
# Build the image
docker build -t toyota-bot .

# Run the container
docker run -d \
  --name toyota_bot \
  --restart unless-stopped \
  -e TELEGRAM_BOT_TOKEN=your_token_here \
  -v ./logs:/app/logs \
  toyota-bot
```

## Features

### Docker Image Includes:
- ✅ **Python 3.11** runtime environment
- ✅ **Google Chrome** + **ChromeDriver** for JavaScript phone extraction
- ✅ **Headless browser** support with virtual display
- ✅ **Security**: Non-root user execution
- ✅ **Health checks** for monitoring
- ✅ **Resource limits** to prevent excessive memory usage

### Container Features:
- 🔄 **Auto-restart** on failure
- 📁 **Volume mounting** for persistent logs
- 🏥 **Health monitoring** with built-in checks
- 🔒 **Security** hardened with non-root user
- 📊 **Resource management** with memory limits

## Monitoring

```bash
# Check container status
docker-compose ps

# View real-time logs
docker-compose logs -f toyota-bot

# Check health status
docker inspect toyota_telegram_bot | grep Health -A 10

# Container resource usage
docker stats toyota_telegram_bot
```

## Troubleshooting

### Common Issues:

1. **Bot token not set**:
   ```bash
   # Check environment variables
   docker-compose exec toyota-bot env | grep TELEGRAM
   ```

2. **Chrome/Selenium issues**:
   ```bash
   # Check Chrome installation
   docker-compose exec toyota-bot google-chrome --version
   docker-compose exec toyota-bot chromedriver --version
   ```

3. **Permission issues with logs**:
   ```bash
   # Fix log directory permissions
   chmod 755 ./logs
   ```

4. **Memory issues**:
   ```bash
   # Monitor memory usage
   docker stats toyota_telegram_bot
   
   # Adjust memory limits in docker-compose.yml if needed
   ```

### Debug Commands:

```bash
# Execute shell inside container
docker-compose exec toyota-bot bash

# View container environment
docker-compose exec toyota-bot env

# Test Python imports
docker-compose exec toyota-bot python -c "import selenium; print('Selenium OK')"
```

## Configuration

### Environment Variables:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (required)
- `PYTHONUNBUFFERED=1` - Ensure real-time log output

### Volume Mounts:
- `./logs:/app/logs` - Persistent log storage
- `./.env:/app/.env:ro` - Environment file (read-only)

### Resource Limits:
- **Memory**: 512MB limit, 256MB reserved
- **Health checks**: Every 60 seconds
- **Restart policy**: Unless manually stopped

## Production Deployment

For production use, consider:

1. **Use external log management**:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

2. **Add monitoring**:
   ```yaml
   labels:
     - "traefik.enable=true"  # For reverse proxy
   ```

3. **Use secrets**:
   ```yaml
   secrets:
     - telegram_token
   ```

4. **Database persistence** (if adding database):
   ```yaml
   volumes:
     - bot_data:/app/data
   ```

## Updates

To update the bot:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

The bot will automatically restart and begin monitoring Toyota listings with all configured features including crash detection and smart filtering.