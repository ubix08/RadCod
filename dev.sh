#!/bin/bash
# RadCode Local Development Script
# Runs both backend and frontend locally without Docker

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check Python
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required"
        exit 1
    fi
    log_success "Python available"
}

# Check Node
check_node() {
    if ! command -v node &> /dev/null; then
        log_error "Node.js is required"
        exit 1
    fi
    log_success "Node.js available"
}

# Install dependencies
install_backend() {
    log_info "Installing backend dependencies..."
    pip install -e . --quiet 2>/dev/null || pip install openhands-sdk openhands-tools openhands-runtime fastapi uvicorn sse-starlette pydantic psutil --quiet
    log_success "Backend dependencies installed"
}

install_frontend() {
    log_info "Installing frontend dependencies..."
    cd ui && npm install --quiet && cd ..
    log_success "Frontend dependencies installed"
}

# Start backend
start_backend() {
    log_info "Starting backend on port 8000..."
    python3 -m src.server &
    BACKEND_PID=$!
    log_success "Backend started (PID: $BACKEND_PID)"
}

# Start frontend  
start_frontend() {
    log_info "Starting frontend on port 5173..."
    cd ui && npm run dev &
    FRONTEND_PID=$!
    log_success "Frontend started (PID: $FRONTEND_PID)"
}

# Start both
start() {
    check_python
    # Backend
    python3 -m src.server &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/radcod_backend.pid
    
    # Frontend
    cd ui && npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/radcod_frontend.pid
    
    log_success "Both services started"
    log_info "Backend: http://localhost:8000"
    log_info "Frontend: http://localhost:5173"
}

# Stop both
stop() {
    log_info "Stopping services..."
    
    if [ -f /tmp/radcod_backend.pid ]; then
        kill $(cat /tmp/radcod_backend.pid) 2>/dev/null || true
        rm /tmp/radcod_backend.pid
    fi
    
    if [ -f /tmp/radcod_frontend.pid ]; then
        kill $(cat /tmp/radcod_frontend.pid) 2>/dev/null || true
        rm /tmp/radcod_frontend.pid
    fi
    
    # Kill any remaining
    pkill -f "src.server" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    
    log_success "Services stopped"
}

# Help
help() {
    echo "RadCode Local Development"
    echo
    echo "Usage: $0 <command>"
    echo
    echo "Commands:"
    echo "  install - Install all dependencies"
    echo "  start   - Start both services"
    echo "  stop    - Stop all services"
    echo
    echo "Note: Requires Python 3.10+ and Node.js 18+"
}

case "${1:-help}" in
    install)
        check_python
        check_node
        install_backend
        install_frontend
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    help)
        help
        ;;
    *)
        help
        ;;
esac