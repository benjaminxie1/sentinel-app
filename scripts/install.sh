#!/bin/bash

# Sentinel Fire Detection System - Production Installer
# Professional deployment script for Linux and macOS systems

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ -f /etc/os-release ]]; then
    OS="linux"
fi

# Installation settings
if [[ "$OS" == "macos" ]]; then
    INSTALL_DIR="$HOME/Applications/Sentinel"
    SERVICE_USER="$USER"
    SERVICE_NAME="com.sentinel.firedetection"
    CONFIG_DIR="$HOME/Library/Application Support/Sentinel"
    LOG_DIR="$HOME/Library/Logs/Sentinel"
    DATA_DIR="$HOME/Library/Application Support/Sentinel/Data"
else
    INSTALL_DIR="/opt/sentinel"
    SERVICE_USER="sentinel"
    SERVICE_NAME="sentinel-fire-detection"
    CONFIG_DIR="/etc/sentinel"
    LOG_DIR="/var/log/sentinel"
    DATA_DIR="/var/lib/sentinel"
fi

# System requirements
MIN_RAM_GB=8
MIN_DISK_GB=100
REQUIRED_PYTHON_VERSION="3.10"

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}    Sentinel Fire Detection System - ${OS^} Installer v2.0    ${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo -e "${YELLOW}⚠️  CRITICAL SAFETY NOTICE:${NC}"
echo -e "${YELLOW}   This is a SUPPLEMENTARY fire detection system only.${NC}"
echo -e "${YELLOW}   Does NOT replace certified fire alarm systems.${NC}"
echo -e "${YELLOW}   Always maintain UL-listed fire detection as primary.${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ "$OS" == "linux" ]] && [[ $EUID -ne 0 ]]; then
        print_error "This installer must be run as root (use sudo)"
        exit 1
    fi
}

# Function to check system requirements
check_system_requirements() {
    print_status "Checking system requirements..."
    
    # Check OS
    if [[ "$OS" == "macos" ]]; then
        print_status "Detected OS: macOS $(sw_vers -productVersion)"
    elif [[ -f /etc/os-release ]]; then
        source /etc/os-release
        print_status "Detected OS: $PRETTY_NAME"
    else
        print_error "Unsupported operating system"
        exit 1
    fi
    
    # Check architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" != "x86_64" ]]; then
        print_warning "Architecture $ARCH may not be fully supported"
    fi
    
    # Check RAM
    if [[ "$OS" == "macos" ]]; then
        TOTAL_RAM=$(sysctl -n hw.memsize)
        TOTAL_RAM_GB=$((TOTAL_RAM / 1073741824))
    else
        TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
    fi
    
    if [[ $TOTAL_RAM_GB -lt $MIN_RAM_GB ]]; then
        print_error "Insufficient RAM: ${TOTAL_RAM_GB}GB (minimum: ${MIN_RAM_GB}GB)"
        exit 1
    fi
    print_status "RAM: ${TOTAL_RAM_GB}GB ✓"
    
    # Check disk space
    if [[ "$OS" == "macos" ]]; then
        AVAILABLE_DISK_GB=$(df -g / | awk 'NR==2 {print $4}')
    else
        AVAILABLE_DISK_GB=$(df / | awk 'NR==2 {print int($4/1024/1024)}')
    fi
    if [[ $AVAILABLE_DISK_GB -lt $MIN_DISK_GB ]]; then
        print_error "Insufficient disk space: ${AVAILABLE_DISK_GB}GB (minimum: ${MIN_DISK_GB}GB)"
        exit 1
    fi
    print_status "Disk space: ${AVAILABLE_DISK_GB}GB available ✓"
    
    # Check GPU (optional but recommended)
    if [[ "$OS" == "macos" ]]; then
        if system_profiler SPDisplaysDataType | grep -q "Metal"; then
            print_status "Metal GPU acceleration available ✓"
        else
            print_warning "No Metal GPU support detected - CPU inference will be slower"
        fi
    else
        if command -v nvidia-smi &> /dev/null; then
            GPU_INFO=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)
            print_status "NVIDIA GPU detected: $GPU_INFO ✓"
        else
            print_warning "No NVIDIA GPU detected - CPU inference will be slower"
        fi
    fi
}

# Function to install system dependencies
install_system_dependencies() {
    print_status "Installing system dependencies..."
    
    if [[ "$OS" == "macos" ]]; then
        # Install Homebrew if not present
        if ! command -v brew &> /dev/null; then
            print_status "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew update
        
        # Install dependencies
        brew install python@3.10 git node rust ffmpeg opencv sqlite nginx
        
        print_status "System dependencies installed ✓"
        return
    fi
    
    # Linux package managers
    if command -v apt-get &> /dev/null; then
        apt-get update
        
        # Install essential packages
        apt-get install -y \
            python3 python3-pip python3-venv \
            git curl wget unzip \
            build-essential \
            pkg-config \
            libopencv-dev \
            ffmpeg \
            sqlite3 \
            nginx \
            ufw \
            logrotate \
            systemd
        
        # Install Python 3.10+ if not available
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ $(echo "$PYTHON_VERSION >= $REQUIRED_PYTHON_VERSION" | bc -l) -eq 0 ]]; then
            add-apt-repository ppa:deadsnakes/ppa -y
            apt-get update
            apt-get install -y python3.10 python3.10-venv python3.10-dev
            update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
        fi
        
    elif command -v yum &> /dev/null; then
        yum update -y
        yum groupinstall -y "Development Tools"
        yum install -y \
            python3 python3-pip \
            git curl wget unzip \
            opencv-devel \
            ffmpeg \
            sqlite \
            nginx \
            firewalld \
            systemd
    else
        print_error "Unsupported package manager"
        exit 1
    fi
    
    print_status "System dependencies installed ✓"
}

# Function to create system user
create_service_user() {
    if [[ "$OS" == "macos" ]]; then
        print_status "Using current user for macOS: $SERVICE_USER"
        return
    fi
    
    print_status "Creating service user..."
    
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd --system --home-dir "$INSTALL_DIR" --shell /bin/bash "$SERVICE_USER"
        print_status "Created user: $SERVICE_USER"
    else
        print_status "User $SERVICE_USER already exists"
    fi
}

# Function to create directories
create_directories() {
    print_status "Creating directories..."
    
    # Create main directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$DATA_DIR/models"
    mkdir -p "$DATA_DIR/datasets"
    mkdir -p "$DATA_DIR/alerts"
    mkdir -p "$DATA_DIR/cameras"
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    
    # Set permissions
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$DATA_DIR"
    
    print_status "Directories created ✓"
}

# Function to install Rust for Tauri
install_rust() {
    print_status "Installing Rust toolchain..."
    
    if ! command -v rustc &> /dev/null; then
        if [[ "$OS" == "macos" ]]; then
            # Install Rust for current user
            curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
            source "$HOME/.cargo/env"
        else
            # Install Rust as service user
            sudo -u "$SERVICE_USER" bash -c 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y'
            echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> "/home/$SERVICE_USER/.bashrc"
        fi
        
        print_status "Rust installed ✓"
    else
        print_status "Rust already installed ✓"
    fi
}

# Function to install Node.js
install_nodejs() {
    print_status "Installing Node.js..."
    
    if [[ "$OS" == "macos" ]]; then
        # Node.js should be installed via brew in system dependencies
        NODE_VERSION=$(node --version 2>/dev/null || echo "not installed")
        if [[ "$NODE_VERSION" != "not installed" ]]; then
            print_status "Node.js already installed: $NODE_VERSION ✓"
        else
            print_error "Node.js installation failed"
            exit 1
        fi
        return
    fi
    
    if ! command -v node &> /dev/null; then
        # Install Node.js 18+ using NodeSource
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
        
        print_status "Node.js installed ✓"
    else
        NODE_VERSION=$(node --version)
        print_status "Node.js already installed: $NODE_VERSION ✓"
    fi
}

# Function to deploy application
deploy_application() {
    print_status "Deploying Sentinel application..."
    
    # Copy application files
    if [[ -d "$(pwd)/backend" ]]; then
        cp -r "$(pwd)"/* "$INSTALL_DIR/"
    else
        print_error "Application files not found. Run installer from project root."
        exit 1
    fi
    
    # Create Python virtual environment
    if [[ "$OS" == "macos" ]]; then
        python3 -m venv "$INSTALL_DIR/venv"
        "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
        "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
        
        cd "$INSTALL_DIR"
        npm install
        source "$HOME/.cargo/env" && npm run tauri build
    else
        sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
        sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
        
        cd "$INSTALL_DIR"
        sudo -u "$SERVICE_USER" npm install
        sudo -u "$SERVICE_USER" bash -c 'source ~/.cargo/env && npm run tauri build'
    fi
    
    # Set ownership
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    
    print_status "Application deployed ✓"
}

# Function to configure firewall
configure_firewall() {
    print_status "Configuring firewall..."
    
    if [[ "$OS" == "macos" ]]; then
        print_status "macOS firewall configuration skipped (not required for local services)"
        return
    fi
    
    if command -v ufw &> /dev/null; then
        # Configure UFW
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        
        # Allow SSH
        ufw allow ssh
        
        # Allow web interface (if needed)
        ufw allow 8080/tcp
        
        # Allow RTSP cameras (common ports)
        ufw allow 554/tcp
        ufw allow 8554/tcp
        
        ufw --force enable
        
    elif command -v firewall-cmd &> /dev/null; then
        # Configure firewalld
        systemctl enable firewalld
        systemctl start firewalld
        
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-port=8080/tcp
        firewall-cmd --permanent --add-port=554/tcp
        firewall-cmd --permanent --add-port=8554/tcp
        firewall-cmd --reload
    fi
    
    print_status "Firewall configured ✓"
}

# Function to create service
create_service() {
    if [[ "$OS" == "macos" ]]; then
        print_status "Creating launchd service..."
        
        # Create LaunchAgents directory if it doesn't exist
        mkdir -p "$HOME/Library/LaunchAgents"
        
        cat > "$HOME/Library/LaunchAgents/${SERVICE_NAME}.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${SERVICE_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/venv/bin/python</string>
        <string>$INSTALL_DIR/run_sentinel.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/sentinel.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/sentinel-error.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>
    <key>ThrottleInterval</key>
    <integer>60</integer>
</dict>
</plist>
EOF
        
        print_status "Launchd service created ✓"
        return
    fi
    
    print_status "Creating systemd service..."
    
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Sentinel Fire Detection System
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/run_sentinel.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=sentinel

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$DATA_DIR $LOG_DIR $CONFIG_DIR

# Resource limits
LimitNOFILE=65536
MemoryLimit=4G

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable and start service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    print_status "Systemd service created ✓"
}

# Function to configure log rotation
configure_logging() {
    print_status "Configuring log rotation..."
    
    if [[ "$OS" == "macos" ]]; then
        # macOS uses newsyslog
        if ! grep -q "$LOG_DIR/sentinel.log" /etc/newsyslog.conf 2>/dev/null; then
            echo "$LOG_DIR/sentinel.log    644  30    100    @T00  J" | sudo tee -a /etc/newsyslog.conf > /dev/null
            echo "$LOG_DIR/sentinel-error.log    644  30    100    @T00  J" | sudo tee -a /etc/newsyslog.conf > /dev/null
        fi
        print_status "Log rotation configured ✓"
        return
    fi
    
    cat > "/etc/logrotate.d/sentinel" << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF
    
    print_status "Log rotation configured ✓"
}

# Function to create default configuration
create_default_config() {
    print_status "Creating default configuration..."
    
    # Detection configuration
    cat > "$CONFIG_DIR/detection_config.yaml" << EOF
detection:
  thresholds:
    immediate_alert: 0.95
    review_queue: 0.85
    log_only: 0.70
  environmental:
    fog_adjustment: -0.05
    sunset_hours: [17, 19]
  adaptive:
    enabled: false
    learning_window_days: 7
    max_auto_adjustment: 0.05

system:
  detection_latency_target: 2.0
  max_concurrent_cameras: 10
  gpu_enabled: true
  
logging:
  level: INFO
  max_file_size: 100MB
  backup_count: 10
EOF
    
    # Network configuration
    cat > "$CONFIG_DIR/network_config.yaml" << EOF
monitor_interval: 30
test_timeout: 5
failover_threshold: 3
test_targets: ['8.8.8.8', '1.1.1.1', '208.67.222.222']

interface_priorities:
  ethernet: 1
  wifi: 2
  cellular: 3
EOF
    
    # Alert configuration template
    cat > "$CONFIG_DIR/alerts.yaml" << EOF
alert_config:
  # In-app alert settings
  max_alerts_stored: 1000
  alert_retention_days: 30
  
  # Rate limiting (prevents alert spam)
  max_alerts_per_hour: 50
  max_alerts_per_day: 200
  
  # UI behavior
  auto_popup_p1: true
  auto_popup_p2: true
  sound_enabled: true
  
  # Storage paths
  database_path: "data/alerts.db"
  alert_frames_dir: "data/alert_frames"
EOF
    
    # User roles template
    cat > "$CONFIG_DIR/recipients.yaml" << EOF
user_roles:
  - name: "operator"
    alert_types: ["P1", "P2", "P4"]
    enabled: true
    can_acknowledge: true
    can_manage_cameras: true
    can_adjust_thresholds: true
EOF
    
    # Camera configuration template
    cat > "$CONFIG_DIR/cameras.yaml" << EOF
cameras: []
last_updated: $(date -Iseconds)
EOF
    
    # Set permissions
    chown -R root:$SERVICE_USER "$CONFIG_DIR"
    chmod -R 640 "$CONFIG_DIR"/*.yaml
    
    print_status "Default configuration created ✓"
}

# Function to run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Check Python installation
    if [[ "$OS" == "macos" ]]; then
        if "$INSTALL_DIR/venv/bin/python" -c "import torch, cv2, ultralytics" &>/dev/null; then
            print_status "Python dependencies ✓"
        else
            print_error "Python dependencies check failed"
            return 1
        fi
    else
        if sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/python" -c "import torch, cv2, ultralytics" &>/dev/null; then
            print_status "Python dependencies ✓"
        else
            print_error "Python dependencies check failed"
            return 1
        fi
    fi
    
    # Check file permissions
    if [[ -r "$CONFIG_DIR/detection_config.yaml" ]] && [[ -w "$LOG_DIR" ]] && [[ -w "$DATA_DIR" ]]; then
        print_status "File permissions ✓"
    else
        print_error "File permissions check failed"
        return 1
    fi
    
    # Check service configuration
    if [[ "$OS" == "macos" ]]; then
        if [[ -f "$HOME/Library/LaunchAgents/${SERVICE_NAME}.plist" ]]; then
            print_status "Service configuration ✓"
        else
            print_error "Service configuration check failed"
            return 1
        fi
    else
        if systemctl is-enabled "$SERVICE_NAME" &>/dev/null; then
            print_status "Service configuration ✓"
        else
            print_error "Service configuration check failed"
            return 1
        fi
    fi
    
    print_status "Health checks passed ✓"
}

# Function to display post-installation instructions
show_post_install_instructions() {
    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}                Installation Completed Successfully!             ${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo ""
    echo "1. Configure alert recipients:"
    echo "   nano $CONFIG_DIR/recipients.yaml"
    echo ""
    echo "2. Add RTSP cameras:"
    echo "   nano $CONFIG_DIR/cameras.yaml"
    echo ""
    
    if [[ "$OS" == "macos" ]]; then
        echo "3. Load the service:"
        echo "   launchctl load ~/Library/LaunchAgents/${SERVICE_NAME}.plist"
        echo ""
        echo "4. Check service status:"
        echo "   launchctl list | grep sentinel"
        echo ""
        echo "5. View logs:"
        echo "   tail -f \"$LOG_DIR/sentinel.log\""
        echo ""
        echo -e "${BLUE}Management Commands:${NC}"
        echo "   Start:    launchctl start ${SERVICE_NAME}"
        echo "   Stop:     launchctl stop ${SERVICE_NAME}"
        echo "   Restart:  launchctl stop ${SERVICE_NAME} && launchctl start ${SERVICE_NAME}"
        echo "   Unload:   launchctl unload ~/Library/LaunchAgents/${SERVICE_NAME}.plist"
    else
        echo "3. Start the service:"
        echo "   sudo systemctl start $SERVICE_NAME"
        echo ""
        echo "4. Check service status:"
        echo "   sudo systemctl status $SERVICE_NAME"
        echo ""
        echo "5. View logs:"
        echo "   sudo journalctl -u $SERVICE_NAME -f"
        echo ""
        echo -e "${BLUE}Management Commands:${NC}"
        echo "   Start:    sudo systemctl start $SERVICE_NAME"
        echo "   Stop:     sudo systemctl stop $SERVICE_NAME"
        echo "   Restart:  sudo systemctl restart $SERVICE_NAME"
        echo "   Status:   sudo systemctl status $SERVICE_NAME"
    fi
    echo ""
    echo -e "${BLUE}Configuration Files:${NC}"
    echo "   Detection:  $CONFIG_DIR/detection_config.yaml"
    echo "   Cameras:    $CONFIG_DIR/cameras.yaml"
    echo "   Alerts:     $CONFIG_DIR/alerts.yaml"
    echo "   User Roles: $CONFIG_DIR/recipients.yaml"
    echo "   Network:    $CONFIG_DIR/network_config.yaml"
    echo ""
    echo -e "${BLUE}Log Files:${NC}"
    echo "   System:    $LOG_DIR/sentinel.log"
    echo "   Service:   sudo journalctl -u $SERVICE_NAME"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANT SAFETY REMINDER:${NC}"
    echo -e "${YELLOW}   This system is SUPPLEMENTARY ONLY${NC}"
    echo -e "${YELLOW}   Always maintain certified fire alarm systems${NC}"
    echo -e "${YELLOW}   Test and verify all fire safety systems regularly${NC}"
    echo ""
}

# Main installation function
main() {
    print_status "Starting Sentinel Fire Detection System installation..."
    
    # Check if running as root
    check_root
    
    # Check system requirements
    check_system_requirements
    
    # Install system dependencies
    install_system_dependencies
    
    # Create service user
    create_service_user
    
    # Create directories
    create_directories
    
    # Install Rust
    install_rust
    
    # Install Node.js
    install_nodejs
    
    # Deploy application
    deploy_application
    
    # Configure firewall
    configure_firewall
    
    # Create service (systemd or launchd)
    create_service
    
    # Configure logging
    configure_logging
    
    # Create default configuration
    create_default_config
    
    # Run health checks
    run_health_checks
    
    # Show post-installation instructions
    show_post_install_instructions
    
    print_status "Installation completed successfully!"
}

# Run main function
main "$@"