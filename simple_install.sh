#!/bin/bash

# Simple Subdomain Scanner Installation Script
# Works on both macOS and Linux
# Focused only on Python dependencies and SQLite setup

# Make script exit on any error
set -e

echo "=== Subdomain Scanner Simple Installation ==="
echo "This script will install Python dependencies and setup SQLite database."
echo ""

# Create and activate virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
echo "Virtual environment activated."

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install flask flask-sqlalchemy psycopg2-binary gunicorn email-validator python-dotenv
echo "Python dependencies installed."

# Create .env file for SQLite configuration
echo "Setting up SQLite database configuration..."
cat > .env << EOF
DATABASE_URL=sqlite:///subdomain_scanner.db
FLASK_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
EOF
echo ".env file created with SQLite configuration."

# Create a simple script to run the application
cat > run.sh << EOF
#!/bin/bash
source venv/bin/activate
gunicorn --bind 0.0.0.0:5003 main:app
EOF
chmod +x run.sh

echo ""
echo "===== Installation Completed Successfully! ====="
echo ""
echo "To run the application: ./run.sh"
echo "SQLite database will be created automatically on first run."
echo "Application will be available at: http://localhost:5003"
echo ""
echo "Happy scanning!"