"""
GPU Acceleration Setup for AMD Radeon RX 6700 XT on Windows
This script configures both PyTorch and Ollama for GPU acceleration using Vulkan/DirectML.
Since ROCm doesn't work well on Windows, we use alternative backends.
"""

import os
import sys
import subprocess
import torch
import json

def check_current_gpu_status():
    """Check current GPU and backend status"""
    print("=== Current GPU Status ===")
    
    # Check PyTorch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    
    # Check for DirectML
    try:
        import torch_directml
        print(f"DirectML available: True")
        print(f"DirectML devices: {torch_directml.device_count()}")
    except ImportError:
        print(f"DirectML available: False")
    
    # Check system GPU
    try:
        import wmi
        c = wmi.WMI()
        for gpu in c.Win32_VideoController():
            print(f"GPU: {gpu.Name}")
    except:
        pass
    
    return torch.cuda.is_available()

def install_directml():
    """Install PyTorch with DirectML support for AMD GPUs on Windows"""
    print("\n=== Installing DirectML for PyTorch ===")
    
    commands = [
        "pip uninstall torch torchvision torchaudio -y",
        "pip install torch-directml",
        "pip install torchvision",
        "pip install torchaudio"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {cmd}: {e}")
            return False
    
    return True

def configure_ollama_vulkan():
    """Configure Ollama to use Vulkan backend"""
    print("\n=== Configuring Ollama for Vulkan ===")
    
    # Set environment variables for Ollama
    env_vars = {
        "OLLAMA_VULKAN": "1",
        "OLLAMA_NUM_PARALLEL": "2",
        "HSA_OVERRIDE_GFX_VERSION": "10.3.0"  # Navi 22 (RX 6700 XT)
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"Set {key}={value}")
    
    # Also set as system environment variables (requires admin)
    print("\nTo make these permanent, set these environment variables:")
    for key, value in env_vars.items():
        print(f"  {key}={value}")
    
    return True

def test_directml_acceleration():
    """Test if DirectML acceleration is working"""
    print("\n=== Testing DirectML Acceleration ===")
    
    try:
        import torch_directml
        dml = torch_directml.device()
        print(f"DirectML device: {dml}")
        
        # Create a tensor on DML device
        x = torch.randn(3, 3, device=dml)
        y = torch.randn(3, 3, device=dml)
        z = torch.mm(x, y)
        
        print(f"Tensor on DML device: {x.device}")
        print(f"Matrix multiplication successful: {z.shape}")
        print("✓ DirectML acceleration working!")
        
        return True
    except Exception as e:
        print(f"✗ DirectML test failed: {e}")
        return False

def test_vulkan_acceleration():
    """Test Vulkan compute capabilities"""
    print("\n=== Testing Vulkan Compute ===")
    
    # Check if we can run Ollama with Vulkan
    try:
        result = subprocess.run(
            ["ollama", "ps"],
            capture_output=True,
            text=True,
            env={**os.environ, "OLLAMA_VULKAN": "1"}
        )
        
        if "GPU" in result.stdout or "Vulkan" in result.stdout:
            print("✓ Ollama Vulkan acceleration detected")
            return True
        else:
            print("✗ Ollama not using GPU/Vulkan")
            print(f"Output: {result.stdout[:200]}")
            return False
    except Exception as e:
        print(f"✗ Ollama test failed: {e}")
        return False

def create_gpu_config():
    """Create configuration file for GPU acceleration"""
    config = {
        "gpu_backend": "directml_vulkan",
        "gpu_device": "AMD Radeon RX 6700 XT",
        "pytorch_backend": "directml",
        "ollama_backend": "vulkan",
        "environment_variables": {
            "OLLAMA_VULKAN": "1",
            "OLLAMA_NUM_PARALLEL": "2",
            "HSA_OVERRIDE_GFX_VERSION": "10.3.0"
        },
        "recommended_batch_size": 4,
        "vram_available_gb": 12  # RX 6700 XT has 12GB
    }
    
    with open("gpu_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("\n=== GPU Configuration Saved ===")
    print("Configuration saved to gpu_config.json")
    return config

def optimize_performance():
    """Apply performance optimizations"""
    print("\n=== Applying Performance Optimizations ===")
    
    optimizations = {
        "torch.backends.cudnn.benchmark": True,
        "torch.backends.cudnn.enabled": True,
        "batch_size_recommendation": "Start with batch size 4, increase if memory allows",
        "mixed_precision": "Consider using torch.cuda.amp for mixed precision training",
        "gradient_accumulation": "Use for larger effective batch sizes"
    }
    
    # Apply PyTorch optimizations if CUDA is available
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.enabled = True
    
    print("Performance optimizations applied:")
    for key, value in optimizations.items():
        print(f"  {key}: {value}")
    
    return optimizations

def main():
    """Main setup function"""
    print("=" * 60)
    print("GPU Acceleration Setup for AMD Radeon RX 6700 XT")
    print("=" * 60)
    
    # Step 1: Check current status
    has_cuda = check_current_gpu_status()
    
    # Step 2: Configure Ollama for Vulkan
    configure_ollama_vulkan()
    
    # Step 3: Install DirectML if needed
    if not has_cuda:
        print("\nCUDA not available. Setting up DirectML...")
        if install_directml():
            print("✓ DirectML installed successfully")
        else:
            print("✗ DirectML installation failed")
    
    # Step 4: Test acceleration
    print("\n" + "=" * 60)
    print("Testing GPU Acceleration")
    print("=" * 60)
    
    dml_working = False
    vulkan_working = False
    
    try:
        dml_working = test_directml_acceleration()
    except ImportError:
        print("DirectML not available for testing")
    
    vulkan_working = test_vulkan_acceleration()
    
    # Step 5: Create configuration
    config = create_gpu_config()
    
    # Step 6: Apply optimizations
    optimize_performance()
    
    # Summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)
    
    if dml_working or vulkan_working:
        print("✓ GPU acceleration configured successfully!")
        if dml_working:
            print("  - DirectML: Working (PyTorch)")
        if vulkan_working:
            print("  - Vulkan: Working (Ollama)")
        
        print("\nNext steps:")
        print("1. Restart your Python environment")
        print("2. Import torch_directml in your code")
        print("3. Use device = torch_directml.device()")
        print("4. Move tensors: tensor.to(device)")
        print("5. Run ollama with OLLAMA_VULKAN=1")
    else:
        print("✗ GPU acceleration not working")
        print("\nTroubleshooting:")
        print("1. Make sure AMD drivers are up to date")
        print("2. Run enable_vulkan.ps1 as administrator")
        print("3. Check Windows Subsystem for Linux (WSL2) for ROCm")
        print("4. Consider using CPU fallback for now")
    
    print("\nConfiguration saved to gpu_config.json")
    print("=" * 60)

if __name__ == "__main__":
    main()