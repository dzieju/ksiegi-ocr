"""
GPU and AI framework utilities for version detection and capability testing.
"""
import warnings
import os
import subprocess
import sys
from tools.logger import log


def suppress_torch_warnings():
    """Suppress common torch warnings that clutter the logs"""
    # Suppress torch warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="torch")
    warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="torch")
    
    # Suppress CUDA warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings too
    
    # Suppress paddle warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="paddle")
    warnings.filterwarnings("ignore", category=FutureWarning, module="paddle")
    
    log("Torch/Paddle warnings suppressed for cleaner logs")


def get_torch_info():
    """Get PyTorch version and CUDA availability information"""
    try:
        suppress_torch_warnings()
        import torch
        
        info = {
            'available': True,
            'version': torch.__version__,
            'cuda_available': torch.cuda.is_available(),
            'cuda_version': None,
            'device_count': 0,
            'device_names': []
        }
        
        if info['cuda_available']:
            info['cuda_version'] = torch.version.cuda
            info['device_count'] = torch.cuda.device_count()
            info['device_names'] = [torch.cuda.get_device_name(i) for i in range(info['device_count'])]
        
        log(f"PyTorch detected: {info['version']}, CUDA: {info['cuda_available']}")
        return info
        
    except ImportError:
        log("PyTorch not available")
        return {
            'available': False,
            'version': None,
            'cuda_available': False,
            'cuda_version': None,
            'device_count': 0,
            'device_names': []
        }
    except Exception as e:
        log(f"Error detecting PyTorch: {e}")
        return {
            'available': False,
            'version': None,
            'cuda_available': False,
            'cuda_version': None,
            'device_count': 0,
            'device_names': [],
            'error': str(e)
        }


def get_paddle_info():
    """Get PaddlePaddle version and GPU availability information"""
    try:
        suppress_torch_warnings()
        import paddle
        
        info = {
            'available': True,
            'version': paddle.__version__,
            'gpu_available': paddle.device.is_compiled_with_cuda(),
            'device_count': 0,
            'device_info': []
        }
        
        if info['gpu_available']:
            try:
                info['device_count'] = paddle.device.cuda.device_count()
                # Get device info if available
                for i in range(info['device_count']):
                    try:
                        # Try to get device properties
                        device_name = f"CUDA Device {i}"
                        info['device_info'].append(device_name)
                    except:
                        info['device_info'].append(f"GPU {i}")
            except:
                info['device_count'] = 1  # Assume at least one if CUDA compiled
                info['device_info'] = ["GPU Device"]
        
        log(f"PaddlePaddle detected: {info['version']}, GPU: {info['gpu_available']}")
        return info
        
    except ImportError:
        log("PaddlePaddle not available")
        return {
            'available': False,
            'version': None,
            'gpu_available': False,
            'device_count': 0,
            'device_info': []
        }
    except Exception as e:
        log(f"Error detecting PaddlePaddle: {e}")
        return {
            'available': False,
            'version': None,
            'gpu_available': False,
            'device_count': 0,
            'device_info': [],
            'error': str(e)
        }


def get_cuda_info():
    """Get CUDA installation information from system"""
    try:
        # Try to run nvidia-smi
        result = subprocess.run(['nvidia-smi', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # Parse nvidia-smi output
            output = result.stdout
            cuda_version = None
            driver_version = None
            
            for line in output.split('\n'):
                if 'CUDA Version:' in line:
                    cuda_version = line.split('CUDA Version: ')[1].strip()
                elif 'NVIDIA-SMI' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        driver_version = parts[1]
            
            log("CUDA drivers detected via nvidia-smi")
            return {
                'available': True,
                'cuda_version': cuda_version,
                'driver_version': driver_version,
                'method': 'nvidia-smi'
            }
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Try to check CUDA installation path
    cuda_paths = [
        '/usr/local/cuda/version.txt',
        '/usr/local/cuda/version.json',
        'C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA'
    ]
    
    for path in cuda_paths:
        if os.path.exists(path):
            log(f"CUDA installation found at: {path}")
            return {
                'available': True,
                'cuda_version': 'unknown',
                'driver_version': 'unknown',
                'method': 'filesystem'
            }
    
    log("No CUDA installation detected")
    return {
        'available': False,
        'cuda_version': None,
        'driver_version': None,
        'method': 'none'
    }


def test_gpu_availability():
    """Comprehensive GPU availability test"""
    log("Starting comprehensive GPU test...")
    
    results = {
        'cuda_system': get_cuda_info(),
        'torch': get_torch_info(),
        'paddle': get_paddle_info(),
        'overall_status': 'unknown',
        'recommendations': []
    }
    
    # Determine overall GPU status
    has_cuda_system = results['cuda_system']['available']
    has_torch_gpu = results['torch']['cuda_available']
    has_paddle_gpu = results['paddle']['gpu_available']
    
    if has_cuda_system and (has_torch_gpu or has_paddle_gpu):
        results['overall_status'] = 'available'
        results['recommendations'].append("✅ GPU jest dostępne i gotowe do użycia")
    elif has_cuda_system and not (has_torch_gpu or has_paddle_gpu):
        results['overall_status'] = 'cuda_only'
        results['recommendations'].append("⚠️ CUDA jest zainstalowana, ale PyTorch/Paddle nie wykrywa GPU")
        results['recommendations'].append("Możliwe problemy: niekompatybilne wersje, brak CUDA-enabled PyTorch/Paddle")
    elif not has_cuda_system and (has_torch_gpu or has_paddle_gpu):
        results['overall_status'] = 'framework_only'
        results['recommendations'].append("⚠️ Framework wykrywa GPU, ale brak systemowych sterowników CUDA")
    else:
        results['overall_status'] = 'unavailable'
        results['recommendations'].append("❌ GPU/CUDA niedostępne")
        results['recommendations'].append("Potrzebne: sterowniki NVIDIA, CUDA toolkit, GPU-enabled PyTorch/Paddle")
    
    log(f"GPU test completed: {results['overall_status']}")
    return results


def get_cuda_installation_links():
    """Get CUDA installation links and instructions"""
    return {
        'cuda_toolkit': 'https://developer.nvidia.com/cuda-downloads',
        'nvidia_drivers': 'https://www.nvidia.com/drivers/',
        'pytorch_cuda': 'https://pytorch.org/get-started/locally/',
        'paddle_gpu': 'https://www.paddlepaddle.org.cn/install/quick',
        'instructions': [
            "1. Zainstaluj najnowsze sterowniki NVIDIA",
            "2. Pobierz i zainstaluj CUDA Toolkit",
            "3. Zainstaluj GPU-enabled wersję PyTorch lub PaddlePaddle",
            "4. Zrestartuj aplikację aby wykryć zmiany"
        ]
    }


def format_gpu_status_text():
    """Format GPU status for display in UI"""
    torch_info = get_torch_info()
    paddle_info = get_paddle_info()
    cuda_info = get_cuda_info()
    
    lines = []
    
    # System CUDA
    if cuda_info['available']:
        lines.append(f"🔧 CUDA System: ✅ Dostępna")
        if cuda_info['driver_version']:
            lines.append(f"   Sterownik: {cuda_info['driver_version']}")
        if cuda_info['cuda_version']:
            lines.append(f"   CUDA: {cuda_info['cuda_version']}")
    else:
        lines.append("🔧 CUDA System: ❌ Niedostępna")
    
    # PyTorch
    if torch_info['available']:
        gpu_status = "✅" if torch_info['cuda_available'] else "❌"
        lines.append(f"🔥 PyTorch: {torch_info['version']} (GPU: {gpu_status})")
        if torch_info['cuda_available'] and torch_info['device_names']:
            for device in torch_info['device_names']:
                lines.append(f"   📱 {device}")
    else:
        lines.append("🔥 PyTorch: ❌ Niedostępny")
    
    # PaddlePaddle
    if paddle_info['available']:
        gpu_status = "✅" if paddle_info['gpu_available'] else "❌"
        lines.append(f"🚀 PaddlePaddle: {paddle_info['version']} (GPU: {gpu_status})")
        if paddle_info['gpu_available'] and paddle_info['device_info']:
            for device in paddle_info['device_info']:
                lines.append(f"   📱 {device}")
    else:
        lines.append("🚀 PaddlePaddle: ❌ Niedostępny")
    
    return "\n".join(lines)