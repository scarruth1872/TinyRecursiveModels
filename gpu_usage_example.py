"""
Example of using GPU acceleration with AMD Radeon RX 6700 XT on Windows
Using DirectML for PyTorch and Vulkan for Ollama
"""

import torch
import torch.nn as nn
import torch.optim as optim
import time

def check_gpu_backend():
    """Check which GPU backend is available"""
    print("=== Available GPU Backends ===")
    
    # Check DirectML
    try:
        import torch_directml
        dml = torch_directml.device()
        print(f"✓ DirectML available: {dml}")
        print(f"  Device count: {torch_directml.device_count()}")
        
        # List all DirectML devices
        for i in range(torch_directml.device_count()):
            print(f"  Device {i}: {torch_directml.device(i)}")
    except ImportError:
        print("✗ DirectML not installed")
        dml = None
    
    # Check CUDA
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  Device count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  Device {i}: {torch.cuda.get_device_name(i)}")
    
    return dml

def simple_tensor_operations(device):
    """Perform simple tensor operations on the specified device"""
    print(f"\n=== Tensor Operations on {device} ===")
    
    # Create tensors
    start = time.time()
    x = torch.randn(1000, 1000, device=device)
    y = torch.randn(1000, 1000, device=device)
    
    # Matrix multiplication
    z = torch.mm(x, y)
    
    # Sum operation
    result = z.sum()
    
    elapsed = time.time() - start
    print(f"  Matrix size: 1000x1000")
    print(f"  Operation: (1000,1000) x (1000,1000)")
    print(f"  Result shape: {z.shape}")
    print(f"  Sum: {result.item():.4f}")
    print(f"  Time: {elapsed:.4f} seconds")
    
    return elapsed

def neural_network_example(device):
    """Simple neural network training example"""
    print(f"\n=== Neural Network Example on {device} ===")
    
    # Define a simple network
    class SimpleNet(nn.Module):
        def __init__(self):
            super(SimpleNet, self).__init__()
            self.fc1 = nn.Linear(784, 128)
            self.fc2 = nn.Linear(128, 64)
            self.fc3 = nn.Linear(64, 10)
            self.relu = nn.ReLU()
        
        def forward(self, x):
            x = self.relu(self.fc1(x))
            x = self.relu(self.fc2(x))
            x = self.fc3(x)
            return x
    
    # Create model and move to device
    model = SimpleNet().to(device)
    
    # Create dummy data
    batch_size = 32
    inputs = torch.randn(batch_size, 784, device=device)
    targets = torch.randint(0, 10, (batch_size,), device=device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.01)
    
    # Training step
    start = time.time()
    
    optimizer.zero_grad()
    outputs = model(inputs)
    loss = criterion(outputs, targets)
    loss.backward()
    optimizer.step()
    
    elapsed = time.time() - start
    
    print(f"  Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    print(f"  Batch size: {batch_size}")
    print(f"  Loss: {loss.item():.4f}")
    print(f"  Training step time: {elapsed:.4f} seconds")
    
    return elapsed

def compare_with_cpu(device):
    """Compare GPU performance with CPU"""
    print("\n=== Performance Comparison ===")
    
    # Warm up
    x = torch.randn(100, 100, device=device)
    _ = torch.mm(x, x)
    
    # Test on GPU/DirectML
    gpu_time = simple_tensor_operations(device)
    
    # Test on CPU
    print(f"\n=== Tensor Operations on CPU ===")
    cpu_time = simple_tensor_operations(torch.device('cpu'))
    
    # Comparison
    if gpu_time > 0:
        speedup = cpu_time / gpu_time
        print(f"\n=== Speedup Analysis ===")
        print(f"  CPU time: {cpu_time:.4f}s")
        print(f"  GPU time: {gpu_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}x")
        
        if speedup > 1:
            print(f"  ✓ GPU is {speedup:.2f}x faster than CPU")
        else:
            print(f"  ✗ GPU is {1/speedup:.2f}x slower than CPU")
            print(f"  This may indicate issues with GPU acceleration")
    
    return gpu_time, cpu_time

def get_usage_instructions():
    """Get instructions for using GPU in your code"""
    print("\n=== How to Use GPU in Your Code ===")
    print("\n1. Import DirectML (if available):")
    print("   ```python")
    print("   try:")
    print("       import torch_directml")
    print("       device = torch_directml.device()")
    print("   except ImportError:")
    print("       device = torch.device('cpu')")
    print("   ```")
    
    print("\n2. Move your model to GPU:")
    print("   ```python")
    print("   model = YourModel().to(device)")
    print("   ```")
    
    print("\n3. Move your data to GPU:")
    print("   ```python")
    print("   inputs = inputs.to(device)")
    print("   targets = targets.to(device)")
    print("   ```")
    
    print("\n4. For data loaders, use automatic device placement:")
    print("   ```python")
    print("   for batch in dataloader:")
    print("       inputs, targets = batch")
    print("       inputs, targets = inputs.to(device), targets.to(device)")
    print("       # ... rest of training loop")
    print("   ```")
    
    print("\n5. For Ollama with Vulkan:")
    print("   Set environment variables before running:")
    print("   ```bash")
    print("   set OLLAMA_VULKAN=1")
    print("   set HSA_OVERRIDE_GFX_VERSION=10.3.0")
    print("   ollama run deepseek-r1:1.5b \"Your prompt\"")
    print("   ```")

def main():
    """Main demonstration function"""
    print("=" * 70)
    print("GPU ACCELERATION DEMONSTRATION")
    print("AMD Radeon RX 6700 XT on Windows")
    print("=" * 70)
    
    # Check available backends
    device = check_gpu_backend()
    
    if device is None:
        print("\n✗ No GPU backend available. Using CPU.")
        device = torch.device('cpu')
    
    # Run demonstrations
    if str(device) != 'cpu':
        print(f"\nUsing device: {device}")
        
        # Simple tensor operations
        simple_tensor_operations(device)
        
        # Neural network example
        neural_network_example(device)
        
        # Performance comparison
        gpu_time, cpu_time = compare_with_cpu(device)
    else:
        print("\n⚠️  Running in CPU mode only")
        print("Consider installing DirectML for GPU acceleration:")
        print("  pip install torch-directml")
        
        # Still run CPU benchmark
        simple_tensor_operations(device)
    
    # Usage instructions
    get_usage_instructions()
    
    # Final recommendations
    print("\n=== Recommendations ===")
    print("1. For PyTorch: Use DirectML (torch-directml)")
    print("2. For Ollama: Use Vulkan backend (OLLAMA_VULKAN=1)")
    print("3. Monitor GPU usage with:")
    print("   - Windows Task Manager (Performance tab)")
    print("   - GPU-Z for detailed GPU metrics")
    print("   - AMD Software: Adrenalin Edition")
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()