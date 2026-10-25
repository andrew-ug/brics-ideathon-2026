import subprocess, os, time, json
t0 = time.time()
print(subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv"], capture_output=True, text=True).stdout)
try:
    import torch
    print("torch", torch.__version__, "cuda", torch.cuda.is_available(), "gpus", torch.cuda.device_count())
except Exception as e:
    print("torch error", e)
root = "/kaggle/input"
for dirpath, dirnames, filenames in os.walk(root):
    depth = dirpath[len(root):].count(os.sep)
    if depth <= 3:
        print(dirpath, len(dirnames), "dirs", len(filenames), "files", filenames[:3])
print("elapsed", round(time.time() - t0, 1), "s")
