# Kaggle notebook starter: environment/data audit only; no training or large downloads.
import os
import platform
import shutil
import torch

print('Python:', platform.python_version())
print('Platform:', platform.platform())
print('PyTorch:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print('GPU count:', torch.cuda.device_count())
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}:', torch.cuda.get_device_name(i))
        print(f'GPU {i} memory GB:', round(torch.cuda.get_device_properties(i).total_memory / 1e9, 2))
for path in ['/kaggle/input', '/kaggle/working', '/tmp']:
    if os.path.exists(path):
        _, _, free = shutil.disk_usage(path)
        print(path, 'free GB:', round(free / 1e9, 2))
print('Stockfish binary:', shutil.which('stockfish'))
print('Working directory:', os.getcwd())
print('No training has been started.')
