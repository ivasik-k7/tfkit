# TFKIT Installation Guide

## Table of Contents

- [Quick Install (Recommended)](#quick-install-recommended)
- [Platform-Specific Guides](#platform-specific-guides)
  - [Linux](#linux)
  - [macOS](#macos)
  - [Windows](#windows)
- [Alternative Installation Methods](#alternative-installation-methods)
- [Upgrading](#upgrading)
- [Verifying Installation](#verifying-installation)
- [Uninstalling](#uninstalling)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

---

## Quick Install (Recommended)

The automated installer script detects your platform and installs the latest version automatically.

### One-Line Install

**Linux & macOS:**

```bash
curl -fsSL https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
```

**Alternative with wget:**

```bash
wget -qO- https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
```

### What the Installer Does

1. ✅ Detects your operating system and architecture
2. ✅ Fetches the latest release from GitHub
3. ✅ Downloads the appropriate binary
4. ✅ Verifies the download with SHA256 checksum
5. ✅ Creates backup if upgrading existing installation
6. ✅ Installs to platform-appropriate directory
7. ✅ Sets executable permissions
8. ✅ Verifies the installation
9. ✅ Provides PATH configuration instructions if needed

### Custom Installation Directory

```bash
# Install to custom directory
export INSTALL_DIR="$HOME/bin"
curl -fsSL https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
```

---

## Platform-Specific Guides

### Linux

#### Automated Installation

```bash
curl -fsSL https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
```

**Default installation path:** `~/.local/bin/tfkit`

#### Manual Installation

1. **Download the binary:**

   ```bash
   curl -fsSL https://github.com/ivasik-k7/tfkit/releases/latest/download/tfkit-linux -o tfkit
   ```

2. **Make it executable:**

   ```bash
   chmod +x tfkit
   ```

3. **Move to PATH:**

   ```bash
   # Option 1: User-local installation (recommended)
   mkdir -p ~/.local/bin
   mv tfkit ~/.local/bin/

   # Option 2: System-wide installation (requires sudo)
   sudo mv tfkit /usr/local/bin/
   ```

4. **Add to PATH (if using ~/.local/bin):**

   For **bash** (`~/.bashrc`):

   ```bash
   echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
   source ~/.bashrc
   ```

   For **zsh** (`~/.zshrc`):

   ```bash
   echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.zshrc
   source ~/.zshrc
   ```

   For **fish** (`~/.config/fish/config.fish`):

   ```bash
   echo 'set -gx PATH $PATH $HOME/.local/bin' >> ~/.config/fish/config.fish
   source ~/.config/fish/config.fish
   ```

#### Distribution-Specific Notes

**Ubuntu/Debian:**

```bash
# Install dependencies if needed
sudo apt-get update
sudo apt-get install curl
```

**Fedora/RHEL/CentOS:**

```bash
# Install dependencies if needed
sudo dnf install curl
```

**Arch Linux:**

```bash
# Install dependencies if needed
sudo pacman -S curl
```

---

### macOS

#### Automated Installation

```bash
curl -fsSL https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
```

**Default installation path:** `~/.local/bin/tfkit`

#### Manual Installation

1. **Download the binary:**

   ```bash
   curl -fsSL https://github.com/ivasik-k7/tfkit/releases/latest/download/tfkit-macos -o tfkit
   ```

2. **Make it executable:**

   ```bash
   chmod +x tfkit
   ```

3. **Remove quarantine attribute (macOS security):**

   ```bash
   xattr -d com.apple.quarantine tfkit
   ```

4. **Move to PATH:**

   ```bash
   # Option 1: User-local installation (recommended)
   mkdir -p ~/.local/bin
   mv tfkit ~/.local/bin/

   # Option 2: System-wide installation (requires sudo)
   sudo mv tfkit /usr/local/bin/
   ```

5. **Add to PATH (if using ~/.local/bin):**

   For **zsh** (default on macOS Catalina+):

   ```bash
   echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.zshrc
   source ~/.zshrc
   ```

   For **bash**:

   ```bash
   echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bash_profile
   source ~/.bash_profile
   ```

#### macOS Security Notes

If you encounter a security warning when running tfkit:

1. **First attempt - Remove quarantine:**

   ```bash
   xattr -d com.apple.quarantine ~/.local/bin/tfkit
   ```

2. **If that doesn't work - Allow in System Preferences:**
   - Open System Preferences → Security & Privacy
   - Click "Open Anyway" when prompted about tfkit
   - Or run: `sudo spctl --master-disable` (not recommended for security)

---

### Windows

#### Automated Installation (Git Bash/WSL)

If using Git Bash or WSL:

```bash
curl -fsSL https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
```

**Default installation path:** `%LOCALAPPDATA%\Programs\tfkit\tfkit.exe`

#### Manual Installation (PowerShell)

1. **Download the binary:**

   ```powershell
   Invoke-WebRequest -Uri "https://github.com/ivasik-k7/tfkit/releases/latest/download/tfkit-windows.exe" -OutFile "tfkit.exe"
   ```

2. **Create installation directory:**

   ```powershell
   $installDir = "$env:LOCALAPPDATA\Programs\tfkit"
   New-Item -ItemType Directory -Force -Path $installDir
   ```

3. **Move binary:**

   ```powershell
   Move-Item -Force tfkit.exe "$installDir\tfkit.exe"
   ```

4. **Add to PATH (User):**

   ```powershell
   $currentPath = [Environment]::GetEnvironmentVariable('Path', 'User')
   [Environment]::SetEnvironmentVariable('Path', "$currentPath;$installDir", 'User')
   ```

5. **Restart your terminal** for PATH changes to take effect.

#### Manual Installation (Command Prompt)

1. **Download from browser:**

   - Visit: https://github.com/ivasik-k7/tfkit/releases/latest
   - Download `tfkit-windows.exe`

2. **Create installation directory:**

   ```cmd
   mkdir "%LOCALAPPDATA%\Programs\tfkit"
   ```

3. **Move the file:**

   - Move `tfkit-windows.exe` to `%LOCALAPPDATA%\Programs\tfkit\`
   - Rename to `tfkit.exe`

4. **Add to PATH manually:**

   - Right-click "This PC" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "User variables", select "Path" → Edit
   - Click "New" and add: `%LOCALAPPDATA%\Programs\tfkit`
   - Click OK on all dialogs

5. **Restart your terminal**

#### Windows Subsystem for Linux (WSL)

If using WSL, follow the [Linux installation guide](#linux).

---

## Alternative Installation Methods

### Install via pip (Python Package)

If you have Python installed:

```bash
# Install
pip install tfkit

# Or with pipx (recommended for CLI tools)
pipx install tfkit

# Upgrade
pip install --upgrade tfkit
```

**Requirements:**

- Python 3.8 or higher
- pip or pipx

### Install from Source

```bash
# Clone the repository
git clone https://github.com/ivasik-k7/tfkit.git
cd tfkit

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### Install Specific Version

**Using installer script:**

```bash
# Not currently supported - always installs latest
# For specific version, use manual installation
```

**Manual installation:**

```bash
VERSION=v0.1.2

# Linux
curl -fsSL "https://github.com/ivasik-k7/tfkit/releases/download/$VERSION/tfkit-linux" -o tfkit

# macOS
curl -fsSL "https://github.com/ivasik-k7/tfkit/releases/download/$VERSION/tfkit-macos" -o tfkit

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://github.com/ivasik-k7/tfkit/releases/download/$VERSION/tfkit-windows.exe" -OutFile "tfkit.exe"
```

Then follow the manual installation steps for your platform.

---

## Upgrading

### Automated Upgrade

Simply run the installer again - it will automatically:

- Detect your current version
- Show upgrade path (e.g., `v0.1.0 → v0.1.2`)
- Create a backup of your current installation
- Install the new version
- Clean up the backup on success
- Restore backup if upgrade fails

```bash
curl -fsSL https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
```

**Example output:**

```
[14:23:01] ▸ Existing installation detected
[14:23:01] ℹ Current version: v0.1.0
[14:23:02] ✓ Target version locked: v0.1.2
[14:23:02] ℹ Upgrade available: v0.1.0 → v0.1.2
[14:23:02] ▸ Creating backup of current installation...
[14:23:02] ✓ Backup created (23M)
...
⚡ tfkit upgraded successfully
```

### Upgrade via pip

```bash
pip install --upgrade tfkit
```

### Manual Upgrade

Follow the manual installation steps for your platform, which will overwrite the existing binary.

---

## Verifying Installation

### Check Version

```bash
tfkit --version
```

### Check Help

```bash
tfkit --help
```

### Verify Binary Location

**Linux/macOS:**

```bash
which tfkit
# Should output: /home/username/.local/bin/tfkit (or your custom path)
```

**Windows (PowerShell):**

```powershell
Get-Command tfkit | Select-Object Source
# Should output: C:\Users\Username\AppData\Local\Programs\tfkit\tfkit.exe
```

### Run a Test Command

```bash
# Navigate to a Terraform project
cd /path/to/terraform/project

# Analyze the project
tfkit analyze
```

---

## Uninstalling

### Remove Binary

**Linux/macOS:**

```bash
# If installed to ~/.local/bin
rm ~/.local/bin/tfkit

# If installed to /usr/local/bin
sudo rm /usr/local/bin/tfkit
```

**Windows (PowerShell):**

```powershell
# Remove binary
Remove-Item "$env:LOCALAPPDATA\Programs\tfkit\tfkit.exe"

# Remove directory
Remove-Item -Recurse "$env:LOCALAPPDATA\Programs\tfkit"

# Remove from PATH (optional)
$currentPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$newPath = ($currentPath -split ';' | Where-Object { $_ -notlike "*tfkit*" }) -join ';'
[Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
```

### Uninstall pip Installation

```bash
pip uninstall tfkit
# or
pipx uninstall tfkit
```

### Clean Up PATH (Optional)

**Linux/macOS:**

Edit your shell profile and remove the PATH line:

```bash
# ~/.bashrc or ~/.zshrc
# Remove or comment out:
# export PATH="$PATH:$HOME/.local/bin"
```

**Windows:**

Follow the manual PATH removal steps above or use GUI method.

---

## Troubleshooting

### Command Not Found

**Symptom:** `tfkit: command not found` or `'tfkit' is not recognized`

**Solutions:**

1. **Check if binary exists:**

   ```bash
   # Linux/macOS
   ls -la ~/.local/bin/tfkit

   # Windows
   dir "%LOCALAPPDATA%\Programs\tfkit\tfkit.exe"
   ```

2. **Verify PATH includes install directory:**

   ```bash
   # Linux/macOS
   echo $PATH | grep -o "$HOME/.local/bin"

   # Windows (PowerShell)
   $env:Path -split ';' | Select-String "tfkit"
   ```

3. **Add to PATH manually** (see platform-specific guides above)

4. **Restart terminal** after PATH modifications

5. **Run with full path as workaround:**

   ```bash
   # Linux/macOS
   ~/.local/bin/tfkit --version

   # Windows
   %LOCALAPPDATA%\Programs\tfkit\tfkit.exe --version
   ```

### Permission Denied

**Symptom:** `Permission denied` when running tfkit

**Solutions:**

**Linux/macOS:**

```bash
# Make executable
chmod +x ~/.local/bin/tfkit

# Verify permissions
ls -la ~/.local/bin/tfkit
# Should show: -rwxr-xr-x (executable flags)
```

**Windows:**

- Run PowerShell as Administrator
- Check antivirus isn't blocking the file
- Verify file isn't marked as blocked: Right-click → Properties → Unblock

### Download Failed

**Symptom:** Installation script fails to download binary

**Solutions:**

1. **Check internet connection**

2. **Verify GitHub is accessible:**

   ```bash
   curl -I https://github.com
   ```

3. **Try alternative download tool:**

   ```bash
   # If curl fails, try wget
   wget -qO- https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
   ```

4. **Check if behind proxy:**

   ```bash
   # Set proxy for curl
   export http_proxy=http://proxy.example.com:8080
   export https_proxy=http://proxy.example.com:8080

   # Then retry installation
   ```

5. **Download manually** and follow manual installation steps

### macOS Security Warning

**Symptom:** "tfkit cannot be opened because it is from an unidentified developer"

**Solutions:**

1. **Remove quarantine attribute:**

   ```bash
   xattr -d com.apple.quarantine ~/.local/bin/tfkit
   ```

2. **Allow in System Preferences:**

   - System Preferences → Security & Privacy
   - Click "Open Anyway"

3. **Check quarantine status:**
   ```bash
   xattr -l ~/.local/bin/tfkit
   ```

### Already Installed - Reinstall

**Symptom:** Want to reinstall same version

**Solution:**

The installer will prompt you:

```
Already running latest version v0.1.2
Re-install anyway? [y/N]:
```

Type `y` and press Enter to proceed with reinstallation.

### Installation Fails - Rollback

**Symptom:** Installation fails during upgrade

**Automatic Recovery:**

The installer automatically creates a backup before upgrading. If installation fails, it will:

```
[14:23:03] ⚠ Installation failed - restoring from backup...
[14:23:03] ✓ Previous version restored
```

Your previous working version is automatically restored.

### Binary Not Working After Install

**Symptom:** Binary installed but doesn't run or shows errors

**Solutions:**

1. **Verify you have the correct platform binary:**

   ```bash
   # Check your platform
   uname -sm

   # Linux: should be using tfkit-linux
   # Darwin: should be using tfkit-macos
   ```

2. **Check binary integrity:**

   ```bash
   # Linux/macOS - verify it's a valid executable
   file ~/.local/bin/tfkit
   # Should show: ELF (Linux) or Mach-O (macOS) executable
   ```

3. **Re-download if corrupted:**

   ```bash
   # Remove and reinstall
   rm ~/.local/bin/tfkit
   curl -fsSL https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
   ```

4. **Check for missing dependencies:**
   ```bash
   # Linux - check for missing libraries
   ldd ~/.local/bin/tfkit
   ```

### Windows Defender Blocking

**Symptom:** Windows Defender or antivirus blocks tfkit.exe

**Solutions:**

1. **Add exception in Windows Defender:**

   - Windows Security → Virus & threat protection
   - Manage settings → Add or remove exclusions
   - Add folder: `%LOCALAPPDATA%\Programs\tfkit`

2. **Verify file is safe:**
   - Check SHA256 hash against release page
   - Download from official GitHub releases only

### PATH Not Persisting

**Symptom:** PATH works in current session but not after restart

**Solutions:**

**Linux/macOS:**

Ensure you're editing the correct shell profile:

```bash
# Check your shell
echo $SHELL

# bash: edit ~/.bashrc (Linux) or ~/.bash_profile (macOS)
# zsh: edit ~/.zshrc
# fish: edit ~/.config/fish/config.fish
```

**Windows:**

Ensure you set it in User or System environment variables, not just current session:

```powershell
# Use this method for persistent PATH
[Environment]::SetEnvironmentVariable('Path',
    [Environment]::GetEnvironmentVariable('Path', 'User') + ";$env:LOCALAPPDATA\Programs\tfkit",
    'User')
```

---

## Advanced Configuration

### Custom Installation Directory

**Linux/macOS:**

```bash
export INSTALL_DIR="$HOME/custom/path"
curl -fsSL https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh | bash
```

**Windows:**

```powershell
$env:INSTALL_DIR = "C:\custom\path"
# Then run installer via Git Bash/WSL
```

### System-Wide Installation (Requires Admin)

**Linux:**

```bash
# Download
curl -fsSL https://github.com/ivasik-k7/tfkit/releases/latest/download/tfkit-linux -o tfkit
chmod +x tfkit

# Install system-wide
sudo mv tfkit /usr/local/bin/
```

**macOS:**

```bash
# Download and prepare
curl -fsSL https://github.com/ivasik-k7/tfkit/releases/latest/download/tfkit-macos -o tfkit
chmod +x tfkit
xattr -d com.apple.quarantine tfkit

# Install system-wide
sudo mv tfkit /usr/local/bin/
```

**Windows (PowerShell as Administrator):**

```powershell
# Download
Invoke-WebRequest -Uri "https://github.com/ivasik-k7/tfkit/releases/latest/download/tfkit-windows.exe" -OutFile "tfkit.exe"

# Install to system location
Move-Item tfkit.exe "C:\Windows\System32\tfkit.exe"
```

### Offline Installation

1. **Download binary on connected machine:**

   - Visit: https://github.com/ivasik-k7/tfkit/releases/latest
   - Download appropriate binary for target platform

2. **Transfer to offline machine:**

   - USB drive, SCP, or other transfer method

3. **Follow manual installation steps** for your platform

### Multiple Versions

To keep multiple versions:

```bash
# Linux/macOS
mv ~/.local/bin/tfkit ~/.local/bin/tfkit-v0.1.0
# Install new version normally
# Use specific version: tfkit-v0.1.0
```

### Build from Source

For development or custom builds:

```bash
# Prerequisites: Python 3.8+, uv or pip

# Clone repository
git clone https://github.com/ivasik-k7/tfkit.git
cd tfkit

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .

# Build binary with PyInstaller
uv pip install pyinstaller
pyinstaller --onefile --name tfkit src/tfkit/cli.py

# Binary location: dist/tfkit
```

---

## Support

- **Issues:** https://github.com/ivasik-k7/tfkit/issues
- **Discussions:** https://github.com/ivasik-k7/tfkit/discussions
- **Documentation:** https://github.com/ivasik-k7/tfkit

---

## Security

### Verifying Downloads

Always download from official sources:

- GitHub Releases: https://github.com/ivasik-k7/tfkit/releases
- Installer Script: https://raw.githubusercontent.com/ivasik-k7/tfkit/main/install.sh

### SHA256 Verification

The installer displays SHA256 hash during installation. Verify against release page if concerned.

**Manual verification:**

```bash
# Linux/macOS
sha256sum tfkit

# macOS alternative
shasum -a 256 tfkit

# Windows (PowerShell)
Get-FileHash -Algorithm SHA256 tfkit.exe
```

Compare output with checksums on GitHub release page.

---

**Last Updated:** October 2025  
**Version:** Covers tfkit v0.1.0+
