# Installation Script for Apple M4 Mac - Docker Desktop & Containerlab

## Step-by-Step Installation Commands for Apple M4 Mac

Copy and paste these commands into your Terminal one section at a time.

### Step 1: Check Your System (Optional)
```bash
# Verify you have an Apple Silicon Mac
uname -m
# Should show: arm64

# Check macOS version
sw_vers
```

### Step 2: Install Homebrew (if not already installed)
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to your PATH (follow the instructions shown after installation)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Verify Homebrew installation
brew --version
```

### Step 3: Install Docker Desktop
```bash
# Install Docker Desktop for Apple Silicon
brew install --cask docker

# Launch Docker Desktop
open /Applications/Docker.app
```

**Important:** After running the above command, Docker Desktop will open. You need to:
1. Complete the Docker Desktop setup wizard
2. Grant necessary permissions when prompted
3. Wait for Docker to start (you'll see "Docker Desktop is running" in the menu bar)

### Step 4: Verify Docker Installation
```bash
# Wait for Docker to fully start, then run:
docker --version
docker info
```

### Step 5: Install Containerlab
```bash
# Add the containerlab tap
brew tap srl-labs/containerlab

# Install containerlab
brew install containerlab

# Verify containerlab installation
containerlab version
```

### Step 6: Create a Test Lab
```bash
# Create a working directory
mkdir ~/containerlab-labs
cd ~/containerlab-labs

# Create a simple test topology
cat > test-lab.yml << 'EOF'
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
EOF

# Deploy the test lab
containerlab deploy -t test-lab.yml

# Check if it's running
containerlab inspect -t test-lab.yml

# Clean up the test lab
containerlab destroy -t test-lab.yml
```

## What to Expect

1. **Homebrew installation** may take 5-10 minutes
2. **Docker Desktop installation** will download ~500MB
3. **First Docker startup** may take 2-3 minutes
4. **Containerlab installation** should be quick (< 1 minute)
5. **Test lab deployment** will download Alpine images (~5MB each)

## Troubleshooting

If you encounter any issues:

```bash
# Check if Docker is running
docker ps

# Restart Docker Desktop if needed
killall Docker && open /Applications/Docker.app

# Check containerlab help
containerlab help
```

## Next Steps After Installation

Once everything is installed, you can:

1. **Try the Cisco router topology** from the main guide
2. **Use FRRouting examples** for free router simulation
3. **Create custom network topologies**

## Quick Reference Commands

```bash
# Deploy a lab
containerlab deploy -t lab-file.yml

# Inspect running labs
containerlab inspect --all

# Destroy a lab
containerlab destroy -t lab-file.yml

# Check Docker containers
docker ps
```

---

**Note:** Make sure to run these commands in order and wait for each step to complete before proceeding to the next one. The Docker Desktop GUI setup is particularly important - don't skip it!