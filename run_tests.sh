#!/bin/bash

# E-commerce Testing Framework - Quick Start Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if config exists
check_config() {
    if [ ! -f "config/config.json" ]; then
        print_warning "Configuration file not found!"
        print_status "Copying example configuration..."
        cp config/config.example.json config/config.json
        print_warning "Please edit config/config.json with your site details before running tests"
        exit 1
    fi
}

# Install dependencies
install_deps() {
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_status "Installing Playwright browsers..."
    playwright install chromium firefox webkit
    playwright install-deps
}

# Run tests
run_tests() {
    local site=$1
    local flow=${2:-full}
    local extra_args="${@:3}"
    
    print_status "Starting E-commerce Testing Framework"
    print_status "Target Site: $site"
    print_status "Test Flow: $flow"
    
    python main.py --site "$site" --flow "$flow" $extra_args
}

# Show usage
show_usage() {
    echo "E-commerce Testing Framework - Quick Start"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  setup                    - Install dependencies and setup environment"
    echo "  test <site> [flow]       - Run tests for specified site"
    echo "  docker-build             - Build Docker image"
    echo "  docker-run <site> [flow] - Run tests in Docker container"
    echo "  clean                    - Clean up reports and logs"
    echo ""
    echo "Test Flows:"
    echo "  full                     - Complete test suite (default)"
    echo "  checkout                 - Checkout flow tests only"
    echo "  validation               - Form validation tests only"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 test your-test-site full"
    echo "  $0 test your-test-site checkout --headless"
    echo "  $0 docker-run your-test-site validation"
    echo ""
}

# Setup environment
setup_environment() {
    print_status "Setting up E-commerce Testing Framework..."
    
    # Create directories
    mkdir -p reports/screenshots
    mkdir -p config
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [ "$(printf '%s\n' "3.8" "$python_version" | sort -V | head -n1)" != "3.8" ]; then
        print_error "Python 3.8+ required. Current version: $python_version"
        exit 1
    fi
    
    # Install dependencies
    install_deps
    
    # Copy config if needed
    check_config
    
    print_success "Setup completed successfully!"
    print_status "Next steps:"
    print_status "1. Edit config/config.json with your site details"
    print_status "2. Run: $0 test your-site-name"
}

# Build Docker image
docker_build() {
    print_status "Building Docker image..."
    docker build -t ecommerce-testing .
    print_success "Docker image built successfully!"
}

# Run tests in Docker
docker_run() {
    local site=$1
    local flow=${2:-full}
    local extra_args="${@:3}"
    
    if [ -z "$site" ]; then
        print_error "Site name required for Docker run"
        show_usage
        exit 1
    fi
    
    print_status "Running tests in Docker container..."
    docker run --rm \
        -v "$(pwd)/config:/app/config" \
        -v "$(pwd)/reports:/app/reports" \
        ecommerce-testing \
        python main.py --site "$site" --flow "$flow" $extra_args
}

# Clean up
clean_reports() {
    print_status "Cleaning up reports and logs..."
    rm -rf reports/*.html reports/*.json reports/screenshots/* reports/*.log
    print_success "Cleanup completed!"
}

# Main script logic
case "$1" in
    "setup")
        setup_environment
        ;;
    "test")
        if [ -z "$2" ]; then
            print_error "Site name required"
            show_usage
            exit 1
        fi
        check_config
        run_tests "${@:2}"
        ;;
    "docker-build")
        docker_build
        ;;
    "docker-run")
        if [ -z "$2" ]; then
            print_error "Site name required"
            show_usage
            exit 1
        fi
        docker_run "${@:2}"
        ;;
    "clean")
        clean_reports
        ;;
    "help"|"--help"|"-h"|"")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac