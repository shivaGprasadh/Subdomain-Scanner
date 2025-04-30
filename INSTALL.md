# Subdomain Scanner - Installation Guide

This document provides detailed installation and setup instructions for the Subdomain Scanner tool on both macOS and Linux environments.

## Required Packages

The following Python packages are required for this application:

```
flask
flask-sqlalchemy
psycopg2-binary
gunicorn
email-validator
python-dotenv
```

## Database Setup

### PostgreSQL Installation

**macOS:**

Using Homebrew:
```bash
# Install PostgreSQL
brew install postgresql

# Start PostgreSQL service
brew services start postgresql
```

Or using Postgres.app (easier):
1. Download [Postgres.app](https://postgresapp.com/)
2. Move to Applications folder and open it
3. Click "Initialize" to create a new server

**Linux (Ubuntu/Debian):**
```bash
# Update package list
sudo apt update

# Install PostgreSQL and development libraries
sudo apt install postgresql postgresql-contrib libpq-dev

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database and User

```bash
# Access PostgreSQL command line
sudo -u postgres psql

# Inside PostgreSQL shell, create a database and user
CREATE DATABASE subdomain_scanner;
CREATE USER scanner_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE subdomain_scanner TO scanner_user;
\q
```

### Configure Environment Variables

Create a `.env` file in the project root:
```
DATABASE_URL=postgresql://scanner_user:your_password@localhost/subdomain_scanner
FLASK_SECRET_KEY=your_secret_key
```

### SQLite Setup (Recommended for Both macOS and Linux)

SQLite is the recommended database option for both macOS and Linux users due to its simplicity and zero-configuration setup:

1. **Create a `.env` file in your project root:**

   ```bash
   touch .env
   ```

2. **Add these lines to the .env file:**

   ```
   DATABASE_URL=sqlite:///subdomain_scanner.db
   FLASK_SECRET_KEY=your_secret_key
   ```

3. **Install python-dotenv:**

   ```bash
   pip install python-dotenv
   ```

The SQLite database is automatically created by the application - no manual database setup required:

- When you run the application for the first time, SQLAlchemy will:
  1. Create the SQLite database file (subdomain_scanner.db) in your project directory
  2. Create all the necessary tables based on your model definitions
  3. Set up the appropriate indexes and constraints

This is one of the biggest advantages of SQLite - zero configuration database setup!

#### Advantages of SQLite for All Users

- No database server to install or configure
- Database is contained in a single file
- Works identically on macOS and Linux
- Works immediately without any system-level configuration
- Perfect for development and smaller deployments
- Easily portable between environments

#### Note for Linux Users
The SQLite setup process is exactly the same on Linux as it is on macOS. No adjustments needed!

## Optional: Install Subdomain Discovery Tools

For enhanced subdomain discovery features, you can install Subfinder and dnsx:

**macOS:**
```bash
# Install Go (required for Subfinder and dnsx)
brew install go

# Install Subfinder
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Install dnsx
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest

# Make sure $GOPATH/bin is in your PATH
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.zshrc  # or ~/.bash_profile
source ~/.zshrc  # or ~/.bash_profile
```

**Linux:**
```bash
# Install Go (required for Subfinder and dnsx)
sudo apt install golang-go

# Install Subfinder
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Install dnsx
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest

# Make sure $GOPATH/bin is in your PATH
echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bashrc
source ~/.bashrc
```

**Note:** If these tools are not installed, the application will still function using a built-in fallback mode.

## Running the Application

```bash
# Load environment variables
source .env  # On Linux/macOS

# Run with Gunicorn (production)
gunicorn --bind 0.0.0.0:5003 main:app

# Or run with Flask for development
python main.py
```

The application should now be running at http://localhost:5003

## Troubleshooting

### Database Connection Issues

#### SQLite Issues:
If you encounter issues with SQLite:
- Check that your application has write permissions in the directory where the database file should be created
- Verify that your DATABASE_URL is correctly set to `sqlite:///subdomain_scanner.db` in the .env file
- Check that python-dotenv is installed and working by printing an environment variable
- If the database file exists but has errors, you can safely delete it and it will be recreated
- For debugging, you can check the SQLite database directly with: `sqlite3 subdomain_scanner.db .tables`

#### PostgreSQL Issues:
If you encounter issues with PostgreSQL:
- Verify PostgreSQL is running: `systemctl status postgresql` (Linux) or `brew services list` (macOS)
- Check your DATABASE_URL environment variable is correctly set
- Ensure database user has proper permissions
- For PostgreSQL connection issues: `sudo -u postgres psql -c "ALTER USER scanner_user WITH PASSWORD 'your_password';"`

### Subfinder/dnsx Not Found

If tools are installed but not detected:
- Check they're properly installed: `which subfinder` and `which dnsx`
- Verify they're in your PATH: `echo $PATH`
- If not in PATH: `export PATH=$PATH:$(go env GOPATH)/bin`
- The application will still work without these tools using its built-in fallback mode

### Missing Python Dependencies

If you encounter module import errors:
```bash
pip install flask flask-sqlalchemy psycopg2-binary gunicorn email-validator python-dotenv
```