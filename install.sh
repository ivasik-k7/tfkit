#!/usr/bin/env bash
set -e

# tfkit installer script
# Usage: curl -fsSL https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash

REPO="ivasik-k7/tfkit"
BINARY_NAME="tfkit"
BACKUP_SUFFIX=".backup"

# Will be set after platform detection
INSTALL_DIR=""
PLATFORM=""
BINARY_FILE=""

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
GRAY='\033[0;90m'
BOLD='\033[1m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${GRAY}[$(date +'%H:%M:%S')]${NC} ${CYAN}▸${NC} $1" >&2
}

success() {
    echo -e "${GRAY}[$(date +'%H:%M:%S')]${NC} ${GREEN}✓${NC} $1" >&2
}

warn() {
    echo -e "${GRAY}[$(date +'%H:%M:%S')]${NC} ${YELLOW}⚠${NC} $1" >&2
}

error() {
    echo -e "${GRAY}[$(date +'%H:%M:%S')]${NC} ${RED}✗${NC} $1" >&2
    exit 1
}

progress() {
    echo -e "${GRAY}[$(date +'%H:%M:%S')]${NC} ${CYAN}⟳${NC} $1" >&2
}

info() {
    echo -e "${GRAY}[$(date +'%H:%M:%S')]${NC} ${BLUE}ℹ${NC} $1" >&2
}

show_banner() {
    echo "" >&2
    echo "" >&2
    echo -e "${CYAN}████████╗███████╗██╗  ██╗██╗████████╗${NC}" >&2
    echo -e "${CYAN}╚══██╔══╝██╔════╝██║ ██╔╝██║╚══██╔══╝${NC}" >&2
    echo -e "${CYAN}   ██║   █████╗  █████╔╝ ██║   ██║   ${NC}" >&2
    echo -e "${CYAN}   ██║   ██╔══╝  ██╔═██╗ ██║   ██║   ${NC}" >&2
    echo -e "${CYAN}   ██║   ██║     ██║  ██╗██║   ██║   ${NC}" >&2
    echo -e "${CYAN}   ╚═╝   ╚═╝     ╚═╝  ╚═╝╚═╝   ╚═╝   ${NC}" >&2
    echo "" >&2
    echo "" >&2
}

detect_platform() {
    local os arch

    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    arch=$(uname -m)

    log "Scanning system architecture..."
    
    case "$os" in
        linux*)
            PLATFORM="linux"
            BINARY_FILE="tfkit-linux"
            BINARY_NAME="tfkit"
            INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
            ;;
        darwin*)
            PLATFORM="macos"
            BINARY_FILE="tfkit-macos"
            BINARY_NAME="tfkit"
            INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
            ;;
        mingw* | msys* | cygwin*)
            PLATFORM="windows"
            BINARY_FILE="tfkit-windows.exe"
            BINARY_NAME="tfkit.exe"
            if [ -n "$LOCALAPPDATA" ]; then
                INSTALL_DIR="${INSTALL_DIR:-$(cygpath -u "$LOCALAPPDATA/Programs/tfkit" 2>/dev/null || echo "$LOCALAPPDATA/Programs/tfkit")}"
            else
                INSTALL_DIR="${INSTALL_DIR:-$HOME/bin}"
            fi
            ;;
        *)
            error "Platform not supported: $os"
            ;;
    esac

    success "Platform identified: ${BOLD}$PLATFORM${NC} ${GRAY}($arch)${NC}"
    info "Installation target: ${BOLD}$INSTALL_DIR${NC}"
}

check_existing_installation() {
    local install_path="$INSTALL_DIR/$BINARY_NAME"
    
    if [ -f "$install_path" ]; then
        log "Existing installation detected"
        
        local current_version=""
        if current_version=$("$install_path" --version 2>/dev/null | head -n1); then
            CURRENT_VERSION="$current_version"
            info "Current version: ${BOLD}$CURRENT_VERSION${NC}"
        else
            CURRENT_VERSION="unknown"
            info "Current version: ${GRAY}unable to determine${NC}"
        fi
        
        EXISTING_INSTALL=true
        return 0
    else
        log "No existing installation found"
        EXISTING_INSTALL=false
        return 1
    fi
}

backup_existing() {
    local install_path="$INSTALL_DIR/$BINARY_NAME"
    local backup_path="$install_path$BACKUP_SUFFIX"
    
    if [ -f "$install_path" ]; then
        log "Creating backup of current installation..."
        progress "Backing up to ${BOLD}${BINARY_NAME}${BACKUP_SUFFIX}${NC}"
        
        cp "$install_path" "$backup_path" || error "Failed to create backup"
        
        local backup_size=$(du -h "$backup_path" | cut -f1)
        success "Backup created ${GRAY}(${backup_size})${NC}"
        BACKUP_CREATED=true
    fi
}

get_latest_version() {
    log "Querying GitHub API for latest release..."
    
    if command -v curl &> /dev/null; then
        VERSION=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    elif command -v wget &> /dev/null; then
        VERSION=$(wget -qO- "https://api.github.com/repos/$REPO/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    else
        error "No download tool found (curl/wget required)"
    fi

    if [ -z "$VERSION" ]; then
        error "Failed to retrieve version metadata"
    fi

    success "Target version locked: ${BOLD}$VERSION${NC}"
}

compare_versions() {
    if [ "$EXISTING_INSTALL" = true ]; then
        if [ "$CURRENT_VERSION" = "$VERSION" ]; then
            info "Already running latest version ${BOLD}$VERSION${NC}"
            echo "" >&2
            read -p "$(echo -e ${YELLOW}Re-install anyway? [y/N]:${NC} )" -n 1 -r >&2
            echo "" >&2
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "" >&2
                success "Installation cancelled - no changes made"
                echo "" >&2
                exit 0
            fi
        else
            info "Upgrade available: ${GRAY}$CURRENT_VERSION${NC} → ${GREEN}${BOLD}$VERSION${NC}"
        fi
    fi
}

download_binary() {
    local url="https://github.com/$REPO/releases/download/$VERSION/$BINARY_FILE"
    local tmp_file="/tmp/$BINARY_FILE"

    log "Initiating binary download..."
    progress "Fetching ${BOLD}$BINARY_FILE${NC} from release artifacts..."

    if command -v curl &> /dev/null; then
        if ! curl -fsSL "$url" -o "$tmp_file"; then
            error "Download failed - binary not found or network error"
        fi
    elif command -v wget &> /dev/null; then
        if ! wget -q "$url" -O "$tmp_file"; then
            error "Download failed - binary not found or network error"
        fi
    fi

    if [ ! -f "$tmp_file" ]; then
        error "Download verification failed - file not created"
    fi

    local size=$(du -h "$tmp_file" | cut -f1)
    local checksum=$(sha256sum "$tmp_file" 2>/dev/null | cut -d' ' -f1 || shasum -a 256 "$tmp_file" 2>/dev/null | cut -d' ' -f1 || echo "unavailable")
    success "Binary acquired ${GRAY}(${size})${NC}"
    info "SHA256: ${GRAY}${checksum:0:16}...${NC}"
    
    echo "$tmp_file"
}

install_binary() {
    local tmp_file="$1"
    local install_path="$INSTALL_DIR/$BINARY_NAME"

    if [ ! -d "$INSTALL_DIR" ]; then
        log "Creating installation directory..."
        mkdir -p "$INSTALL_DIR" || error "Failed to create directory: $INSTALL_DIR"
        success "Directory structure created"
    fi

    if [ "$EXISTING_INSTALL" = true ]; then
        log "Replacing existing installation..."
    else
        log "Deploying binary to system..."
    fi
    
    progress "Installing to ${BOLD}$install_path${NC}"
    
    mv "$tmp_file" "$install_path" || error "Installation failed - check permissions"
    chmod +x "$install_path" || error "Failed to set executable permissions"

    success "Binary deployed successfully"
}

cleanup_backup() {
    local backup_path="$INSTALL_DIR/$BINARY_NAME$BACKUP_SUFFIX"
    
    if [ "$BACKUP_CREATED" = true ] && [ -f "$backup_path" ]; then
        log "Cleaning up backup file..."
        rm -f "$backup_path"
        success "Backup removed"
    fi
}

restore_backup() {
    local install_path="$INSTALL_DIR/$BINARY_NAME"
    local backup_path="$install_path$BACKUP_SUFFIX"
    
    if [ "$BACKUP_CREATED" = true ] && [ -f "$backup_path" ]; then
        warn "Installation failed - restoring from backup..."
        mv "$backup_path" "$install_path"
        success "Previous version restored"
    fi
}

check_path() {
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        warn "Installation directory not in PATH"
        echo "" >&2
        
        if [ "$PLATFORM" = "windows" ]; then
            echo -e "  ${GRAY}To add to PATH on Windows:${NC}" >&2
            echo "" >&2
            echo -e "  ${CYAN}1. Open System Properties > Environment Variables${NC}" >&2
            echo -e "  ${CYAN}2. Add to PATH:${NC} ${BOLD}$INSTALL_DIR${NC}" >&2
            echo "" >&2
            echo -e "  ${GRAY}Or run in PowerShell (as Administrator):${NC}" >&2
            echo -e "  ${CYAN}[Environment]::SetEnvironmentVariable('Path', \$env:Path + ';$INSTALL_DIR', 'User')${NC}" >&2
            echo "" >&2
        else
            echo -e "  ${GRAY}To enable system-wide access, add this to your shell profile:${NC}" >&2
            echo "" >&2
            echo -e "  ${CYAN}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}" >&2
            echo "" >&2
            echo -e "  ${GRAY}Then reload: ${NC}${CYAN}source ~/.bashrc${NC} ${GRAY}or${NC} ${CYAN}source ~/.zshrc${NC}" >&2
            echo "" >&2
        fi
    else
        success "Installation directory verified in PATH"
    fi
}

verify_installation() {
    local install_path="$INSTALL_DIR/$BINARY_NAME"
    
    log "Running installation verification..."
    
    if [ -f "$install_path" ] && [ -x "$install_path" ]; then
        success "Binary integrity confirmed"
        
        local installed_version=""
        if installed_version=$("$install_path" --version 2>/dev/null | head -n1); then
            info "Installed version: ${BOLD}$installed_version${NC}"
        fi
        
        if "$install_path" --version &>/dev/null || "$install_path" --help &>/dev/null; then
            echo "" >&2
            if [ "$EXISTING_INSTALL" = true ]; then
                echo -e "${GREEN}${BOLD}⚡ tfkit upgraded successfully${NC}" >&2
            else
                echo -e "${GREEN}${BOLD}⚡ tfkit installation complete${NC}" >&2
            fi
            echo "" >&2
            echo -e "  ${GRAY}Start analyzing:${NC} ${CYAN}tfkit --help${NC}" >&2
        else
            warn "Binary installed but runtime verification inconclusive"
        fi
    else
        error "Installation verification failed"
    fi
}

main() {
    trap 'restore_backup' ERR
    
    show_banner
    log "Initializing installation sequence..."
    echo "" >&2

    detect_platform
    check_existing_installation
    get_latest_version
    compare_versions
    
    if [ "$EXISTING_INSTALL" = true ]; then
        backup_existing
    fi
    
    local tmp_file
    tmp_file=$(download_binary)
    
    install_binary "$tmp_file"
    
    if [ "$EXISTING_INSTALL" = true ]; then
        cleanup_backup
    fi
    
    check_path
    verify_installation

    echo "" >&2
    echo -e "${GRAY}Installation path:${NC} ${BOLD}$INSTALL_DIR${NC}" >&2
    echo "" >&2
}

EXISTING_INSTALL=false
BACKUP_CREATED=false
CURRENT_VERSION=""

main "$@"