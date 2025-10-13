# Step-by-Step: Installing Docker Desktop and Containerlab on macOS

This guide will walk you through the complete installation process for Docker Desktop and containerlab on your Mac.

## Prerequisites Check

Before we begin, verify your system meets the requirements:

1. **Check your macOS version:**
   ```bash
   sw_vers
   ```
   You need macOS 10.15 (Catalina) or newer.

2. **Check your Mac architecture:**
   ```bash
   uname -m
   ```
   - `x86_64` = Intel Mac
   - `arm64` = Apple Silicon (M1/M2/M3)

## Step 1: Install Docker Desktop for Mac

### Option A: Download from Docker Website (Recommended)

1. **Go to the Docker Desktop download page:**
   - Visit: https://www.docker.com/products/docker-desktop/

2. **Download the correct version:**
   - **For Intel Macs:** Click "Download for Mac with Intel chip"
   - **For Apple Silicon Macs:** Click "Download for Mac with Apple chip"

3. **Install Docker Desktop:**
   - Open the downloaded `.dmg` file
   - Drag Docker.app to your Applications folder
   - Launch Docker Desktop from Applications
   - Follow the setup wizard
   - Grant necessary permissions when prompted

4. **Verify Docker Desktop is running:**
   ```bash
   docker --version
   docker info
   ```

### Option B: Install via Homebrew

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Docker Desktop via Homebrew Cask
brew install --cask docker

# Launch Docker Desktop
open /Applications/Docker.app
```

## Step 2: Configure Docker Desktop

1. **Open Docker Desktop preferences:**
   - Click the Docker icon in your menu bar
   - Select "Preferences" or "Settings"

2. **Allocate sufficient resources:**
   - Go to "Resources" → "Advanced"
   - Set **Memory** to at least 4GB (8GB recommended for multiple routers)
   - Set **CPUs** to at least 2 cores
   - Click "Apply & Restart"

3. **Configure file sharing:**
   - Go to "Resources" → "File Sharing"
   - Ensure your home directory or working directory is included
   - Add additional paths if needed

## Step 3: Install Containerlab

### Option A: Install via Homebrew (Recommended)

```bash
# Add the containerlab tap
brew tap srl-labs/containerlab

# Install containerlab
brew install containerlab

# Verify installation
containerlab version
```

### Option B: Direct Binary Installation

**For Intel Macs:**
```bash
# Create a temporary directory
mkdir -p ~/tmp && cd ~/tmp

# Download the latest Intel binary
curl -L https://github.com/srl-labs/containerlab/releases/latest/download/containerlab_darwin_amd64.tar.gz -o containerlab.tar.gz

# Extract the binary
tar -xf containerlab.tar.gz

# Move to /usr/local/bin (make sure this directory exists and is in your PATH)
sudo mkdir -p /usr/local/bin
sudo mv containerlab /usr/local/bin/

# Make it executable
sudo chmod +x /usr/local/bin/containerlab

# Clean up
cd ~ && rm -rf ~/tmp
```

**For Apple Silicon Macs (M1/M2/M3):**
```bash
# Create a temporary directory
mkdir -p ~/tmp && cd ~/tmp

# Download the latest ARM64 binary
curl -L https://github.com/srl-labs/containerlab/releases/latest/download/containerlab_darwin_arm64.tar.gz -o containerlab.tar.gz

# Extract the binary
tar -xf containerlab.tar.gz

# Move to /usr/local/bin
sudo mkdir -p /usr/local/bin
sudo mv containerlab /usr/local/bin/

# Make it executable
sudo chmod +x /usr/local/bin/containerlab

# Clean up
cd ~ && rm -rf ~/tmp
```

## Step 4: Verify Installation

1. **Check containerlab version:**
   ```bash
   containerlab version
   ```

2. **Test Docker connectivity:**
   ```bash
   docker run hello-world
   ```

3. **Check if containerlab can access Docker:**
   ```bash
   containerlab help
   ```

## Step 5: Create Your First Lab

1. **Create a working directory:**
   ```bash
   mkdir ~/containerlab-labs
   cd ~/containerlab-labs
   ```

2. **Create a simple test topology file (`test-lab.yml`):**
   ```yaml
   name: test-lab
   
   topology:
     nodes:
       alpine1:
         kind: linux
         image: alpine:latest
       alpine2:
         kind: linux
         image: alpine:latest
     links:
       - endpoints: ["alpine1:eth1", "alpine2:eth1"]
   ```

3. **Deploy the test lab:**
   ```bash
   containerlab deploy -t test-lab.yml
   ```

4. **Verify the lab is running:**
   ```bash
   containerlab inspect -t test-lab.yml
   docker ps
   ```

5. **Clean up the test lab:**
   ```bash
   containerlab destroy -t test-lab.yml
   ```

## Troubleshooting Common Issues

### Issue: "containerlab: command not found"

**Solution:**
```bash
# Check if /usr/local/bin is in your PATH
echo $PATH

# If not, add it to your shell profile
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Issue: Docker Desktop not starting

**Solutions:**
1. Restart Docker Desktop from Applications
2. Check system resources (close other applications)
3. Restart your Mac
4. Reinstall Docker Desktop if necessary

### Issue: Permission denied errors

**Solution:**
```bash
# Ensure your user is in the docker group (this happens automatically on Mac)
# If issues persist, restart Docker Desktop
```

### Issue: "Cannot connect to the Docker daemon"

**Solutions:**
1. Ensure Docker Desktop is running (check menu bar icon)
2. Restart Docker Desktop
3. Check Docker Desktop logs in Preferences → Troubleshoot

## Next Steps

Once you have containerlab installed and working:

1. **Download router images** (if you have access to Cisco images)
2. **Try the FRRouting examples** from the main guide
3. **Create more complex topologies**
4. **Explore containerlab documentation** at https://containerlab.dev/

## Useful Commands Reference

```bash
# Check containerlab version
containerlab version

# List all labs
containerlab inspect --all

# Deploy a lab
containerlab deploy -t lab-file.yml

# Destroy a lab
containerlab destroy -t lab-file.yml

# Show lab details
containerlab inspect -t lab-file.yml

# Check Docker status
docker info
docker ps
```

## Getting Help

- **Containerlab Documentation:** https://containerlab.dev/
- **Docker Desktop Documentation:** https://docs.docker.com/desktop/mac/
- **Containerlab GitHub:** https://github.com/srl-labs/containerlab