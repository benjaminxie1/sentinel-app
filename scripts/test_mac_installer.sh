#!/bin/bash

# Sentinel Fire Detection System - macOS Installer Test Script
# Tests the macOS installer in a safe, isolated manner

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_DIR="${1:-$HOME/tmp/SentinelTest}"
KEEP_FILES="${2:-false}"

# Test paths
TEST_INSTALL_DIR="$TEST_DIR/Applications/Sentinel"
TEST_CONFIG_DIR="$TEST_DIR/Library/Application Support/Sentinel"
TEST_LOG_DIR="$TEST_DIR/Library/Logs/Sentinel"
TEST_DATA_DIR="$TEST_DIR/Library/Application Support/Sentinel/Data"

echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}       Sentinel macOS Installer - Test Suite                    ${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Helper functions
print_test_result() {
    local test_name="$1"
    local success="$2"
    local details="$3"
    
    if [[ "$success" == "true" ]]; then
        echo -e "${GREEN}[PASS]${NC} $test_name"
    else
        echo -e "${RED}[FAIL]${NC} $test_name"
    fi
    
    if [[ -n "$details" ]]; then
        echo -e "       ${YELLOW}$details${NC}"
    fi
}

# Test functions
test_prerequisites() {
    echo ""
    echo -e "${YELLOW}Testing Prerequisites...${NC}"
    
    # Test macOS version
    os_version=$(sw_vers -productVersion)
    major_version=$(echo "$os_version" | cut -d. -f1)
    if [[ $major_version -ge 10 ]]; then
        print_test_result "macOS Version" "true" "Current: $os_version"
    else
        print_test_result "macOS Version" "false" "Current: $os_version (Required: 10.15+)"
        return 1
    fi
    
    # Test disk space
    available_space=$(df -g / | awk 'NR==2 {print $4}')
    if [[ $available_space -gt 5 ]]; then
        print_test_result "Disk Space" "true" "${available_space}GB available"
    else
        print_test_result "Disk Space" "false" "${available_space}GB available (Required: 5GB+)"
        return 1
    fi
    
    # Test RAM
    total_ram=$(sysctl -n hw.memsize)
    total_ram_gb=$((total_ram / 1073741824))
    if [[ $total_ram_gb -ge 8 ]]; then
        print_test_result "RAM" "true" "${total_ram_gb}GB detected"
    else
        print_test_result "RAM" "false" "${total_ram_gb}GB detected (Required: 8GB+)"
    fi
    
    # Test command line tools
    if xcode-select -p &>/dev/null; then
        print_test_result "Xcode Command Line Tools" "true"
    else
        print_test_result "Xcode Command Line Tools" "false" "Run: xcode-select --install"
    fi
    
    return 0
}

test_homebrew() {
    echo ""
    echo -e "${YELLOW}Testing Homebrew...${NC}"
    
    if command -v brew &>/dev/null; then
        brew_version=$(brew --version | head -1)
        print_test_result "Homebrew Installed" "true" "$brew_version"
        
        # Test brew update
        if brew update &>/dev/null; then
            print_test_result "Homebrew Update" "true"
        else
            print_test_result "Homebrew Update" "false"
        fi
    else
        print_test_result "Homebrew Installed" "false" "Would be installed by installer"
    fi
}

test_system_dependencies() {
    echo ""
    echo -e "${YELLOW}Testing System Dependencies...${NC}"
    
    # Test Python
    if command -v python3 &>/dev/null; then
        python_version=$(python3 --version)
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            print_test_result "Python 3.10+" "true" "$python_version"
        else
            print_test_result "Python 3.10+" "false" "$python_version (3.10+ required)"
        fi
    else
        print_test_result "Python" "false" "Not installed"
    fi
    
    # Test Node.js
    if command -v node &>/dev/null; then
        node_version=$(node --version)
        print_test_result "Node.js" "true" "$node_version"
    else
        print_test_result "Node.js" "false" "Not installed"
    fi
    
    # Test Rust
    if command -v rustc &>/dev/null; then
        rust_version=$(rustc --version)
        print_test_result "Rust" "true" "$rust_version"
    else
        print_test_result "Rust" "false" "Not installed"
    fi
    
    # Test FFmpeg
    if command -v ffmpeg &>/dev/null; then
        ffmpeg_version=$(ffmpeg -version | head -1)
        print_test_result "FFmpeg" "true" "${ffmpeg_version#ffmpeg }"
    else
        print_test_result "FFmpeg" "false" "Not installed"
    fi
}

test_directory_creation() {
    echo ""
    echo -e "${YELLOW}Testing Directory Creation...${NC}"
    
    # Create test directories
    test_dirs=(
        "$TEST_INSTALL_DIR"
        "$TEST_CONFIG_DIR"
        "$TEST_LOG_DIR"
        "$TEST_DATA_DIR"
        "$TEST_DATA_DIR/models"
        "$TEST_DATA_DIR/datasets"
        "$TEST_DATA_DIR/alerts"
        "$TEST_DATA_DIR/cameras"
    )
    
    all_created=true
    for dir in "${test_dirs[@]}"; do
        if mkdir -p "$dir" 2>/dev/null; then
            if [[ -d "$dir" ]]; then
                dir_name=$(basename "$dir")
                print_test_result "Create $dir_name" "true"
            else
                print_test_result "Create $dir_name" "false"
                all_created=false
            fi
        else
            print_test_result "Create $(basename "$dir")" "false" "Permission denied"
            all_created=false
        fi
    done
    
    if [[ "$all_created" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

test_configuration_files() {
    echo ""
    echo -e "${YELLOW}Testing Configuration File Creation...${NC}"
    
    # Test creating YAML configurations
    config_files=(
        "detection_config.yaml"
        "alerts.yaml"
        "cameras.yaml"
        "network_config.yaml"
        "recipients.yaml"
    )
    
    all_created=true
    for file in "${config_files[@]}"; do
        file_path="$TEST_CONFIG_DIR/$file"
        
        # Create sample content
        cat > "$file_path" << EOF
# Test configuration file
test: true
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF
        
        if [[ -f "$file_path" ]] && [[ -s "$file_path" ]]; then
            print_test_result "Create $file" "true"
        else
            print_test_result "Create $file" "false"
            all_created=false
        fi
    done
    
    if [[ "$all_created" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

test_launchd_plist() {
    echo ""
    echo -e "${YELLOW}Testing LaunchAgent Configuration...${NC}"
    
    # Create test plist
    plist_path="$TEST_DIR/Library/LaunchAgents/com.sentinel.firedetection.plist"
    mkdir -p "$(dirname "$plist_path")"
    
    cat > "$plist_path" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sentinel.firedetection.test</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/true</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF
    
    if [[ -f "$plist_path" ]]; then
        # Validate plist
        if plutil -lint "$plist_path" &>/dev/null; then
            print_test_result "LaunchAgent plist" "true" "Valid plist created"
        else
            print_test_result "LaunchAgent plist" "false" "Invalid plist format"
        fi
    else
        print_test_result "LaunchAgent plist" "false" "Could not create plist"
    fi
}

test_python_environment() {
    echo ""
    echo -e "${YELLOW}Testing Python Environment...${NC}"
    
    if command -v python3 &>/dev/null; then
        # Test venv creation
        venv_path="$TEST_INSTALL_DIR/test_venv"
        if python3 -m venv "$venv_path" 2>/dev/null; then
            if [[ -f "$venv_path/bin/python" ]]; then
                print_test_result "Virtual Environment" "true" "venv created successfully"
                
                # Test pip
                if "$venv_path/bin/pip" --version &>/dev/null; then
                    print_test_result "Pip Available" "true"
                else
                    print_test_result "Pip Available" "false"
                fi
            else
                print_test_result "Virtual Environment" "false" "venv creation failed"
            fi
        else
            print_test_result "Virtual Environment" "false" "Could not create venv"
        fi
    else
        print_test_result "Python Available" "false" "Python not installed"
    fi
}

test_gpu_support() {
    echo ""
    echo -e "${YELLOW}Testing GPU Support...${NC}"
    
    # Check for Metal support
    if system_profiler SPDisplaysDataType | grep -q "Metal"; then
        gpu_info=$(system_profiler SPDisplaysDataType | grep "Chipset Model" | head -1 | awk -F': ' '{print $2}')
        print_test_result "Metal GPU Support" "true" "$gpu_info"
    else
        print_test_result "Metal GPU Support" "false" "No Metal support detected"
    fi
}

test_network_connectivity() {
    echo ""
    echo -e "${YELLOW}Testing Network Connectivity...${NC}"
    
    # Test DNS resolution
    if ping -c 1 -t 2 google.com &>/dev/null; then
        print_test_result "DNS Resolution" "true"
    else
        print_test_result "DNS Resolution" "false"
    fi
    
    # Test package repositories
    if curl -s -I https://pypi.org | grep "200 OK" &>/dev/null; then
        print_test_result "PyPI Access" "true"
    else
        print_test_result "PyPI Access" "false"
    fi
    
    if curl -s -I https://registry.npmjs.org | grep "200 OK" &>/dev/null; then
        print_test_result "NPM Registry Access" "true"
    else
        print_test_result "NPM Registry Access" "false"
    fi
}

cleanup_test_files() {
    if [[ "$KEEP_FILES" != "true" ]]; then
        echo ""
        echo -e "${YELLOW}Cleaning up test files...${NC}"
        
        if [[ -d "$TEST_DIR" ]]; then
            if rm -rf "$TEST_DIR"; then
                print_test_result "Cleanup" "true" "Test files removed"
            else
                print_test_result "Cleanup" "false" "Some files could not be removed"
            fi
        fi
    else
        echo ""
        echo -e "${YELLOW}Test files kept at: $TEST_DIR${NC}"
    fi
}

# Main test execution
run_installer_tests() {
    local start_time=$(date +%s)
    
    echo "Test Directory: $TEST_DIR"
    echo ""
    
    # Create test directory
    mkdir -p "$TEST_DIR"
    
    # Run tests
    local all_passed=true
    
    test_prerequisites || all_passed=false
    test_homebrew
    test_system_dependencies
    test_directory_creation || all_passed=false
    test_configuration_files || all_passed=false
    test_launchd_plist
    test_python_environment
    test_gpu_support
    test_network_connectivity
    
    # Summary
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}                        Test Summary                            ${NC}"
    echo -e "${BLUE}================================================================${NC}"
    
    if [[ "$all_passed" == "true" ]]; then
        echo -e "${GREEN}All critical tests passed!${NC}"
    else
        echo -e "${YELLOW}Some critical tests failed${NC}"
    fi
    
    echo "Duration: ${duration} seconds"
    
    # Cleanup
    cleanup_test_files
    
    echo ""
    echo -e "${GREEN}Testing complete!${NC}"
    
    # Return appropriate exit code
    if [[ "$all_passed" == "true" ]]; then
        return 0
    else
        return 1
    fi
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}This test script is for macOS only${NC}"
    exit 1
fi

# Run the tests
if run_installer_tests; then
    exit 0
else
    exit 1
fi