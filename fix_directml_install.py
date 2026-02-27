"""
Fix DirectML installation with correct dependencies
DirectML requires specific torch version (2.4.1) to work properly
"""

import subprocess
import sys

def check_current_install():
    """Check what's currently installed"""
    print("=== Checking current PyTorch installation ===")
    
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=freeze"],
        capture_output=True,
        text=True
    )
    
    # Look for torch packages
    lines = result.stdout.split('\n')
    torch_packages = [line for line in lines if 'torch' in line.lower()]
    
    for pkg in torch_packages:
        print(f"  {pkg}")
    
    return torch_packages

def clean_install_directml():
    """Clean install of DirectML with correct dependencies"""
    print("\n=== Clean installing DirectML ===")
    
    # Uninstall all torch packages
    uninstall_commands = [
        "pip uninstall torch torchvision torchaudio torch-directml -y",
    ]
    
    for cmd in uninstall_commands:
        print(f"Running: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"  Note: {e}")
    
    # Install DirectML with correct version constraints
    print("\n=== Installing DirectML with correct dependencies ===")
    
    # Method 1: Install torch-directml which should handle dependencies
    print("Method 1: Installing torch-directml package")
    try:
        subprocess.run(
            "pip install torch-directml==0.2.5.dev240914",
            shell=True,
            check=True
        )
        print("✓ Successfully installed torch-directml")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install torch-directml: {e}")
        
        # Method 2: Manual installation with exact versions
        print("\nMethod 2: Manual installation with exact versions")
        manual_commands = [
            "pip install torch==2.4.1",
            "pip install torchvision==0.19.1",
            "pip install torchaudio==2.4.1",
            "pip install torch-directml==0.2.5.dev240914",
        ]
        
        for cmd in manual_commands:
            print(f"  Running: {cmd}")
            try:
                subprocess.run(cmd, shell=True, check=True)
                print(f"    ✓ Success")
            except subprocess.CalledProcessError as e:
                print(f"    ✗ Failed: {e}")

def verify_installation():
    """Verify DirectML installation works"""
    print("\n=== Verifying DirectML Installation ===")
    
    test_code = """
import torch
print(f"PyTorch version: {torch.__version__}")

try:
    import torch_directml
    print(f"DirectML available: True")
    device = torch_directml.device()
    print(f"DirectML device: {device}")
    
    # Test tensor operations
    x = torch.randn(3, 3, device=device)
    y = torch.randn(3, 3, device=device)
    z = torch.mm(x, y)
    print(f"DirectML test successful: {z.shape}")
    
except ImportError as e:
    print(f"DirectML import error: {e}")
except Exception as e:
    print(f"DirectML test error: {e}")
"""
    
    # Write test file
    with open("test_directml.py", "w") as f:
        f.write(test_code)
    
    # Run test
    result = subprocess.run(
        [sys.executable, "test_directml.py"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(f"Errors: {result.stderr}")
    
    # Clean up
    import os
    if os.path.exists("test_directml.py"):
        os.remove("test_directml.py")

def create_gpu_requirements():
    """Create a requirements-gpu.txt for GPU acceleration"""
    print("\n=== Creating GPU requirements file ===")
    
    gpu_requirements = """# GPU Acceleration Requirements for AMD RX 6700 XT on Windows
# PyTorch with DirectML support
torch==2.4.1
torchvision==0.19.1
torchaudio==2.4.1
torch-directml==0.2.5.dev240914

# Optional: For monitoring GPU usage
# pynvml  # NVIDIA only
# gpustat  # NVIDIA only

# Existing requirements
adam-atan2
einops
tqdm
coolname
pydantic
argdantic
wandb
omegaconf
hydra-core
huggingface_hub
packaging
ninja
wheel
setuptools
setuptools-scm
pydantic-core
huggingface_hub
numba
triton
"""
    
    with open("requirements-gpu.txt", "w") as f:
        f.write(gpu_requirements)
    
    print("✓ Created requirements-gpu.txt")
    print("  Install with: pip install -r requirements-gpu.txt")

def main():
    """Main fix function"""
    print("=" * 70)
    print("Fixing DirectML Installation for AMD GPU")
    print("=" * 70)
    
    # Step 1: Check current install
    torch_packages = check_current_install()
    
    # Step 2: Clean install
    clean_install_directml()
    
    # Step 3: Verify
    verify_installation()
    
    # Step 4: Create requirements file
    create_gpu_requirements()
    
    print("\n" + "=" * 70)
    print("FIX COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Restart your Python environment")
    print("2. Test with: python gpu_usage_example.py")
    print("3. For Ollama: Run with OLLAMA_VULKAN=1")
    print("4. Use the provided requirements-gpu.txt for future setups")
    
    print("\nTroubleshooting:")
    print("- If DirectML still fails, update AMD drivers")
    print("- Make sure Windows is up to date")
    print("- Consider using WSL2 with ROCm for better AMD support")

if __name__ == "__main__":
    main()