import numpy as np
import torch
import time

SEED = 42
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

def benchmark_numpy(np_array, repeats=5, warmup=1):
    print("NumPy benchmark")
    # Warmup
    for _ in range(warmup):
        _ = np_array * 2.5 + 3.0
        _ = np.matmul(_, _.transpose(0, 2, 1))
    times = []
    for _ in range(repeats):
        start = time.perf_counter()
        np_result = np_array * 2.5 + 3.0
        np_matmul = np.matmul(np_result, np_result.transpose(0, 2, 1))
        np_sum = np.sum(np_matmul)
        end = time.perf_counter()
        times.append(end - start)
    print(f"NumPy (CPU) mean: {np.mean(times):.6f}s min: {min(times):.6f}s")
    return float(np_sum)

def benchmark_torch_cpu(np_array, repeats=5, warmup=1):
    print("PyTorch CPU benchmark")
    torch_tensor = torch.from_numpy(np_array)
    with torch.inference_mode():
        for _ in range(warmup):
            r = torch_tensor * 2.5 + 3.0
            m = torch.matmul(r, r.transpose(1, 2))
            _ = torch.sum(m)
        times = []
        for _ in range(repeats):
            start = time.perf_counter()
            r = torch_tensor * 2.5 + 3.0
            m = torch.matmul(r, r.transpose(1, 2))
            s = torch.sum(m)
            end = time.perf_counter()
            times.append(end - start)
    print(f"PyTorch (CPU) mean: {np.mean(times):.6f}s min: {min(times):.6f}s")
    return float(s.item())

def benchmark_torch_gpu(np_array, repeats=5, warmup=1):
    if not torch.cuda.is_available():
        print("GPU not available")
        return None
    print("PyTorch GPU benchmark")
    device = torch.device("cuda")
    torch_tensor = torch.from_numpy(np_array).to(device, non_blocking=True)
    times = []
    with torch.inference_mode():
        # Warmup
        for _ in range(warmup):
            r = torch_tensor * 2.5 + 3.0
            m = torch.matmul(r, r.transpose(1, 2))
            _ = torch.sum(m)
        torch.cuda.synchronize()
        for _ in range(repeats):
            start = time.perf_counter()
            r = torch_tensor * 2.5 + 3.0
            m = torch.matmul(r, r.transpose(1, 2))
            s = torch.sum(m)
            torch.cuda.synchronize()  # ensure all ops complete
            end = time.perf_counter()
            times.append(end - start)
    print(f"PyTorch (GPU) mean: {np.mean(times):.6f}s min: {min(times):.6f}s")
    return float(s.item())

if __name__ == "__main__":
    # Adjust shape for clearer timing; keep memory reasonable
    shape = (32, 256, 256)  # ~8.4M floats (~32 MB)
    np_array = np.random.rand(*shape).astype(np.float32)

    np_sum = benchmark_numpy(np_array)
    torch_cpu_sum = benchmark_torch_cpu(np_array)
    torch_gpu_sum = benchmark_torch_gpu(np_array)

    print("\nResult samples (scalar sums):")
    print(f"NumPy sum: {np_sum}")
    print(f"Torch CPU sum: {torch_cpu_sum}")
    if torch_gpu_sum is not None:
        print(f"Torch GPU sum: {torch_gpu_sum}")
