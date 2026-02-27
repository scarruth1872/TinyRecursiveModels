import torch
import sys

print("=== PyTorch GPU Check ===")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA device count: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.current_device()}")
    for i in range(torch.cuda.device_count()):
        print(f"Device {i}: {torch.cuda.get_device_name(i)}")
        print(f"  Memory allocated: {torch.cuda.memory_allocated(i) / 1024**3:.2f} GB")
        print(f"  Memory reserved: {torch.cuda.memory_reserved(i) / 1024**3:.2f} GB")
        print(f"  CUDA capability: {torch.cuda.get_device_capability(i)}")
else:
    print("CUDA not available. Checking if ROCm is available...")
    # Check for ROCm (AMD GPU support)
    try:
        if hasattr(torch, 'version') and 'rocm' in torch.version.__version__.lower():
            print("ROCm detected.")
        else:
            print("No ROCm detected.")
    except:
        pass

print("\n=== Backend Info ===")
print(f"Backend: {torch.backends.cudnn.enabled}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")

# Test a small tensor to see if GPU is actually used
print("\n=== Tensor Test ===")
x = torch.randn(3, 3)
print(f"Tensor device (default): {x.device}")
if torch.cuda.is_available():
    x_gpu = x.cuda()
    print(f"Tensor device (GPU): {x_gpu.device}")
    # Perform a simple operation
    y = x_gpu @ x_gpu.t()
    print(f"GPU operation successful: {y.shape}")
    print(f"GPU memory allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
else:
    print("No GPU available for tensor operations.")