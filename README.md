# Subdomain Scanner Tool

A Flask-based web application for scanning and analyzing subdomains of specified domains. This tool efficiently identifies active and inactive domains with a clean web interface and database storage capabilities.

## Features

- **Subdomain Scanning**: Discover subdomains using subfinder and dnsx tools (with fallback capability if tools are not available)
- **Domain Liveness Detection**: Check if discovered subdomains are active and capture HTTP response information
- **CSV Export**: Export all scan results to CSV format for further analysis
- **PostgreSQL Database**: Store scan history and results for later reference
- **Responsive Web Interface**: Clean, user-friendly interface with Bootstrap styling
- **Real-time Recheck**: Ability to recheck domain status directly from the interface

## Screenshots

(Add screenshots here)

## Installation

For detailed installation instructions, see:
- [INSTALL.md](INSTALL.md) - Detailed instructions for installation
- [Setup Guide](http://localhost:5000/setup) - Web-based setup documentation (when application is running)

### Automated Installation (Recommended)

We provide convenient installation scripts for both macOS and Linux that set up everything for you:

```bash
# Clone repository
git clone https://github.com/yourusername/subdomain-scanner.git
cd subdomain-scanner

# Full installation (with optional tools)
chmod +x install.sh
./install.sh

# OR

# Simple installation (Python dependencies and SQLite only)
chmod +x simple_install.sh
./simple_install.sh
```

These scripts will:
- Create a Python virtual environment
- Install all required dependencies
- Set up the SQLite database (automatically created on first run)
- Generate a secure random secret key
- Create convenient run scripts

### Manual Installation

If you prefer to install everything manually:

```bash
# Clone repository
git clone https://github.com/yourusername/subdomain-scanner.git
cd subdomain-scanner

# Install dependencies
pip install flask flask-sqlalchemy psycopg2-binary gunicorn email-validator python-dotenv

# Create .env file for SQLite (recommended)
echo "DATABASE_URL=sqlite:///subdomain_scanner.db" > .env
echo "FLASK_SECRET_KEY=your_secret_key" >> .env

# Run application
gunicorn --bind 0.0.0.0:5003 main:app
```

## Usage

1. Navigate to the web interface at `http://localhost:5000`
2. Enter a domain name (e.g., example.com)
3. Click "Scan" to start scanning for subdomains
4. View the results, which will be categorized as active or inactive
5. Use the "Export to CSV" button to download results
6. Access scan history through the "Scan History" navigation link

## Requirements

- Python 3.6+
- PostgreSQL or SQLite database
- Subfinder and dnsx (optional, enhances scanning capabilities)

## Development

The application is built with:
- Flask web framework
- SQLAlchemy for database ORM
- Bootstrap for frontend styling
- DataTables for interactive tables
- jQuery for frontend interactions

## License

(Specify your license information here)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- [Subfinder](https://github.com/projectdiscovery/subfinder) - For subdomain discovery
- [dnsx](https://github.com/projectdiscovery/dnsx) - For DNS resolution
- [Bootstrap](https://getbootstrap.com/) - For UI components
- [DataTables](https://datatables.net/) - For enhanced table functionality