#!/bin/bash
# RadCode Startup Script
# Starts both backend and frontend services

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
COMPOSE_FILE="${COMPOSE_FILE:-deploy/docker-compose.yml}"
PROJECT_NAME="radcod"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check for docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    
    log_success "Docker and Docker Compose available"
}

# Check for .env file
check_env() {
    if [ -f .env ]; then
        log_success ".env file found"
    else
        if [ -f deploy/env.example ]; then
            log_warn ".env file not found, using deploy/env.example as template"
            cp deploy/env.example .env
            log_info "Created .env from template - please edit with your API keys"
        fi
    fi
}

# Build images
build() {
    log_info "Building Docker images..."
    docker compose -f "$COMPOSE_FILE" build --no-cache
    log_success "Images built successfully"
}

# Start services
start() {
    log_info "Starting RadCode services..."
    
    # Pull latest images first
    docker compose -f "$COMPOSE_FILE" pull || true
    
    # Start containers
    docker compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 5
    
    # Check status
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_success "Services started successfully"
    else
        log_error "Some services failed to start"
        docker compose -f "$COMPOSE_FILE" logs
        exit 1
    fi
}

# Stop services
stop() {
    log_info "Stopping RadCode services..."
    docker compose -f "$COMPOSE_FILE" down
    log_success "Services stopped"
}

# Show status
status() {
    docker compose -f "$COMPOSE_FILE" ps
}

# Show logs
logs() {
    docker compose -f "$COMPOSE_FILE" logs -f "${@:-}"
}

# Restart services
restart() {
    stop
    start
}

# Full reset (stop, remove, rebuild, start)
reset() {
    log_warn "This will remove all containers and volumes!"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker compose -f "$COMPOSE_FILE" down -v
        build
        start
    fi
}

# Setup initial deployment
setup() {
    check_docker
    check_env
    build
    start
    log_success "RadCode is ready!"
    echo
    echo "========================================"
    echo "  RadCode Deployment"
    echo "========================================"
    echo "Backend API:  http://localhost:8000"
    echo "Frontend UI:  http://localhost"
    echo "Health:      http://localhost:8000/health"
    echo "========================================"
}

# Print help
help() {
    echo "RadCode Deployment Script"
    echo
    echo "Usage: $0 <command>"
    echo
    echo "Commands:"
    echo "  setup    - Initial setup (check docker, create .env, build, start)"
    echo "  start    - Start services"
    echo "  stop     - Stop services"
    echo "  restart  - Restart services"
    echo "  status   - Show service status"
    echo "  logs     - Show logs (follows by default)"
    echo "  build    - Build Docker images"
    echo "  reset    - Full reset (stop, remove, rebuild, start)"
    echo "  help     - Show this help"
    echo
    echo "Environment Variables:"
    echo "  COMPOSE_FILE - Custom docker-compose file path"
    echo
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 start"
    echo "  $0 logs --tail 100"
}

# Main
case "${1:-help}" in
    setup)
        check_docker
        check_env
        build
        start
        log_success "RadCode is ready!"
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "${@:-}"
        ;;
    build)
        build
        ;;
    reset)
        reset
        ;;
    help|--help|-h)
        help
        ;;
    *)
        log_error "Unknown command: $1"
        help
        exit 1
        ;;
esac