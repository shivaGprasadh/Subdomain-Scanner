#!/bin/bash

# Subdomain Scanner Installation Script
# Works on both macOS and Linux
# Handles all dependency installation and SQLite setup

# Make script exit on any error
set -e

# ANSI color codes for better output readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "  _____       _         _                       _         _____                                 "
echo " / ____|     | |       | |                     (_)       / ____|                                "
echo "| (___  _   _| |__   __| | ___  _ __ ___   __ _ _ _ __  | (___   ___ __ _ _ __  _ __   ___ _ __"
echo " \___ \| | | | '_ \ / _\` |/ _ \| '_ \` _ \ / _\` | | '_ \  \___ \ / __/ _\` | '_ \| '_ \ / _ \ '__|"
echo " ____) | |_| | |_) | (_| | (_) | | | | | | (_| | | | | | ____) | (_| (_| | | | | | | |  __/ |   "
echo "|_____/ \__,_|_.__/ \__,_|\___/|_| |_| |_|\__,_|_|_| |_||_____/ \___\__,_|_| |_|_| |_|\___|_|   "
echo -e "${NC}"
echo -e "${GREEN}Subdomain Scanner Installation Script${NC}"
echo -e "${YELLOW}This script will install all required dependencies and setup the SQLite database.${NC}"
echo ""

# Check if script is being run as root on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ "$EUID" -eq 0 ]; then
        echo -e "${RED}Please do not run this script as root or with sudo.${NC}"
        exit 1
    fi
fi

# Detect operating system
echo -e "${BLUE}=== Detecting operating system ===${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
    echo -e "${GREEN}Detected: macOS${NC}"
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Homebrew not found. Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo -e "${GREEN}Homebrew already installed.${NC}"
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}Python 3 not found. Installing...${NC}"
        brew install python3
    else
        echo -e "${GREEN}Python 3 already installed.${NC}"
    fi
    
    # Install pip if not available
    if ! command -v pip3 &> /dev/null; then
        echo -e "${YELLOW}Pip not found. Installing...${NC}"
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python3 get-pip.py
        rm get-pip.py
    else
        echo -e "${GREEN}Pip already installed.${NC}"
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
    echo -e "${GREEN}Detected: Linux${NC}"
    
    # Try to detect distribution
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        echo -e "${GREEN}Detected distribution: $DISTRO${NC}"
    else
        DISTRO="unknown"
        echo -e "${YELLOW}Unknown Linux distribution. Will attempt generic installation.${NC}"
    fi
    
    # Install python and pip based on distribution
    echo -e "${BLUE}=== Installing Python and pip ===${NC}"
    if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$DISTRO" == "linuxmint" ]]; then
        echo -e "${YELLOW}Updating package lists...${NC}"
        sudo apt-get update
        
        echo -e "${YELLOW}Installing Python 3 and pip...${NC}"
        sudo apt-get install -y python3 python3-pip python3-venv
    elif [[ "$DISTRO" == "fedora" ]]; then
        echo -e "${YELLOW}Installing Python 3 and pip...${NC}"
        sudo dnf install -y python3 python3-pip
    elif [[ "$DISTRO" == "centos" || "$DISTRO" == "rhel" ]]; then
        echo -e "${YELLOW}Installing Python 3 and pip...${NC}"
        sudo yum install -y python3 python3-pip
    elif [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" ]]; then
        echo -e "${YELLOW}Installing Python 3 and pip...${NC}"
        sudo pacman -S --noconfirm python python-pip
    else
        echo -e "${RED}Unsupported Linux distribution. Please install Python 3 and pip manually.${NC}"
        echo -e "${YELLOW}Then run this script again.${NC}"
        exit 1
    fi
else
    echo -e "${RED}Unsupported operating system: $OSTYPE${NC}"
    exit 1
fi

# Create and activate virtual environment
echo -e "${BLUE}=== Setting up Python virtual environment ===${NC}"
python3 -m venv venv
echo -e "${GREEN}Virtual environment created.${NC}"

# Activate virtual environment
if [[ "$OS" == "macOS" ]]; then
    source venv/bin/activate
else
    source venv/bin/activate
fi
echo -e "${GREEN}Virtual environment activated.${NC}"

# Install Python dependencies
echo -e "${BLUE}=== Installing Python dependencies ===${NC}"
pip install --upgrade pip
pip install flask flask-sqlalchemy psycopg2-binary gunicorn email-validator python-dotenv
echo -e "${GREEN}Python dependencies installed.${NC}"

# Create .env file for SQLite configuration
echo -e "${BLUE}=== Setting up SQLite database configuration ===${NC}"
if [ -f .env ]; then
    echo -e "${YELLOW}.env file already exists. Creating backup at .env.bak${NC}"
    cp .env .env.bak
fi

cat > .env << EOF
DATABASE_URL=sqlite:///subdomain_scanner.db
FLASK_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(16))')
EOF

echo -e "${GREEN}.env file created with SQLite configuration and a secure random secret key.${NC}"

# Install Go Tools (Optional)
echo -e "${BLUE}=== Optional: Install subdomain scanning tools ===${NC}"
echo -e "${YELLOW}Would you like to install Go and the subdomain scanning tools (subfinder, dnsx)?${NC}"
echo -e "${YELLOW}This is optional but provides enhanced scanning capabilities. (y/n)${NC}"
read -r install_go

if [[ "$install_go" == "y" || "$install_go" == "Y" ]]; then
    echo -e "${BLUE}=== Installing Go and scanning tools ===${NC}"
    
    if [[ "$OS" == "macOS" ]]; then
        if ! command -v go &> /dev/null; then
            echo -e "${YELLOW}Installing Go...${NC}"
            brew install go
        else
            echo -e "${GREEN}Go already installed.${NC}"
        fi
    else
        if ! command -v go &> /dev/null; then
            echo -e "${YELLOW}Installing Go...${NC}"
            if [[ "$DISTRO" == "ubuntu" || "$DISTRO" == "debian" || "$DISTRO" == "linuxmint" ]]; then
                sudo apt-get install -y golang-go
            elif [[ "$DISTRO" == "fedora" ]]; then
                sudo dnf install -y golang
            elif [[ "$DISTRO" == "centos" || "$DISTRO" == "rhel" ]]; then
                sudo yum install -y golang
            elif [[ "$DISTRO" == "arch" || "$DISTRO" == "manjaro" ]]; then
                sudo pacman -S --noconfirm go
            else
                echo -e "${RED}Unsupported Linux distribution. Please install Go manually.${NC}"
            fi
        else
            echo -e "${GREEN}Go already installed.${NC}"
        fi
    fi
    
    # Install subfinder and dnsx
    echo -e "${YELLOW}Installing subfinder and dnsx...${NC}"
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
    go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
    
    # Add GOPATH to PATH in relevant shell configuration file
    if [[ "$OS" == "macOS" ]]; then
        if [[ "$SHELL" == */zsh ]]; then
            if ! grep -q 'export PATH=$PATH:$(go env GOPATH)/bin' ~/.zshrc; then
                echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.zshrc
                echo -e "${GREEN}Added GOPATH to ~/.zshrc${NC}"
            fi
        else
            if ! grep -q 'export PATH=$PATH:$(go env GOPATH)/bin' ~/.bash_profile; then
                echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bash_profile
                echo -e "${GREEN}Added GOPATH to ~/.bash_profile${NC}"
            fi
        fi
    else
        if ! grep -q 'export PATH=$PATH:$(go env GOPATH)/bin' ~/.bashrc; then
            echo 'export PATH=$PATH:$(go env GOPATH)/bin' >> ~/.bashrc
            echo -e "${GREEN}Added GOPATH to ~/.bashrc${NC}"
        fi
    fi
    
    echo -e "${GREEN}Go and scanning tools installed.${NC}"
    echo -e "${YELLOW}Note: You may need to restart your terminal for the PATH changes to take effect.${NC}"
else
    echo -e "${YELLOW}Skipping Go and scanning tools installation.${NC}"
    echo -e "${YELLOW}The application will still work with built-in fallback mechanisms.${NC}"
fi

# Create a simple script to run the application
cat > run.sh << EOF
#!/bin/bash
source venv/bin/activate
gunicorn --bind 0.0.0.0:5003 main:app
EOF
chmod +x run.sh

# Create a simple script for development mode
cat > run_dev.sh << EOF
#!/bin/bash
source venv/bin/activate
python main.py
EOF
chmod +x run_dev.sh

echo ""
echo -e "${GREEN}=======================================================${NC}"
echo -e "${GREEN}Installation Completed Successfully!${NC}"
echo -e "${GREEN}=======================================================${NC}"
echo ""
echo -e "${BLUE}To run the application:${NC}"
echo -e "  ${YELLOW}Production mode: ${NC}./run.sh"
echo -e "  ${YELLOW}Development mode: ${NC}./run_dev.sh"
echo ""
echo -e "${BLUE}Notes:${NC}"
echo -e "  ${YELLOW}1. SQLite database will be created automatically on first run${NC}"
echo -e "  ${YELLOW}2. Configuration is stored in the .env file${NC}"
echo -e "  ${YELLOW}3. Application will be available at: http://localhost:5003${NC}"
echo ""

if [[ "$install_go" == "y" || "$install_go" == "Y" ]]; then
    echo -e "${YELLOW}IMPORTANT: You need to restart your terminal or run the following command for the Go tools to work:${NC}"
    if [[ "$OS" == "macOS" ]]; then
        if [[ "$SHELL" == */zsh ]]; then
            echo -e "  ${GREEN}source ~/.zshrc${NC}"
        else
            echo -e "  ${GREEN}source ~/.bash_profile${NC}"
        fi
    else
        echo -e "  ${GREEN}source ~/.bashrc${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Happy scanning!${NC}"