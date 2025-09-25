"""
System dependencies checker for KSIEGI-OCR application.
Checks all required dependencies and provides status information.
"""
import sys
import subprocess
import importlib
import platform
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import re


def _compare_versions(current: str, minimum: str) -> int:
    """
    Compare version strings.
    Returns: -1 if current < minimum, 0 if equal, 1 if current > minimum
    """
    def normalize_version(v):
        # Extract numeric parts from version string
        parts = re.findall(r'\d+', v)
        return [int(x) for x in parts]
    
    curr_parts = normalize_version(current)
    min_parts = normalize_version(minimum)
    
    # Pad shorter version with zeros
    max_len = max(len(curr_parts), len(min_parts))
    curr_parts.extend([0] * (max_len - len(curr_parts)))
    min_parts.extend([0] * (max_len - len(min_parts)))
    
    for curr, min_v in zip(curr_parts, min_parts):
        if curr < min_v:
            return -1
        elif curr > min_v:
            return 1
    
    return 0


class DependencyChecker:
    """Checks system dependencies and provides status information."""
    
    def __init__(self):
        self.dependencies = []
        self._setup_dependencies()
    
    def _setup_dependencies(self):
        """Setup the list of dependencies to check."""
        self.dependencies = [
            {
                'name': 'Python',
                'type': 'system',
                'check_func': self._check_python,
                'required': True,
                'description': 'Interpreter Python (wymagane: 3.8+)',
                'update_link': 'https://www.python.org/downloads/',
                'min_version': '3.8.0'
            },
            {
                'name': 'Tkinter',
                'type': 'module',
                'module': 'tkinter',
                'required': True,
                'description': 'Interfejs graficzny (część standardowej biblioteki)',
                'install_links': {
                    'linux': 'https://docs.python.org/3/library/tkinter.html',
                    'windows': 'https://docs.python.org/3/library/tkinter.html',
                    'darwin': 'https://docs.python.org/3/library/tkinter.html',
                    'default': 'https://docs.python.org/3/library/tkinter.html'
                },
                'install_commands': {
                    'linux': 'sudo apt-get install python3-tk  # Ubuntu/Debian\nsudo yum install tkinter  # RHEL/CentOS',
                    'windows': 'Tkinter jest zwykle dołączony do Pythona w systemie Windows.\nJeśli brakuje, przeinstaluj Python z oficjalnej strony.',
                    'darwin': 'brew install python-tk  # jeśli używasz Homebrew',
                    'default': 'apt-get install python3-tk'
                }
            },
            {
                'name': 'Tesseract OCR',
                'type': 'executable_and_module',
                'executable': 'tesseract',
                'module': 'pytesseract',
                'required': True,
                'description': 'Silnik OCR Tesseract + moduł Python',
                'install_links': {
                    'linux': 'https://github.com/tesseract-ocr/tesseract/wiki/Compiling#linux',
                    'windows': 'https://github.com/UB-Mannheim/tesseract/wiki',
                    'darwin': 'https://github.com/tesseract-ocr/tesseract/wiki/Compiling#macos',
                    'default': 'https://github.com/tesseract-ocr/tesseract/wiki'
                },
                'install_commands': {
                    'linux': 'sudo apt-get install tesseract-ocr && pip install pytesseract  # Ubuntu/Debian\nsudo yum install tesseract && pip install pytesseract  # RHEL/CentOS',
                    'windows': '1. Pobierz installer z: https://github.com/UB-Mannheim/tesseract/wiki\n2. pip install pytesseract',
                    'darwin': 'brew install tesseract && pip install pytesseract',
                    'default': 'apt-get install tesseract-ocr && pip install pytesseract'
                }
            },
            {
                'name': 'Poppler',
                'type': 'custom',
                'check_func': self._check_poppler,
                'required': True,
                'description': 'Narzędzia PDF (pdfinfo, pdfimages, pdftoppm)',
                'install_links': {
                    'linux': 'https://poppler.freedesktop.org/',
                    'windows': 'https://github.com/oschwartz10612/poppler-windows/releases/',
                    'darwin': 'https://formulae.brew.sh/formula/poppler',
                    'default': 'https://poppler.freedesktop.org/'
                },
                'install_commands': {
                    'linux': 'sudo apt-get install poppler-utils  # Ubuntu/Debian\nsudo yum install poppler-utils  # RHEL/CentOS',
                    'windows': '1. Pobierz z: https://github.com/oschwartz10612/poppler-windows/releases/\n2. Wypakuj do katalogu poppler/ w projekcie',
                    'darwin': 'brew install poppler',
                    'default': 'apt-get install poppler-utils'
                }
            },
            {
                'name': 'pdfplumber',
                'type': 'module',
                'module': 'pdfplumber',
                'required': True,
                'description': 'Ekstrakcja tekstu z dokumentów PDF',
                'install_link': 'https://pypi.org/project/pdfplumber/',
                'install_cmd': 'pip install pdfplumber'
            },
            {
                'name': 'EasyOCR',
                'type': 'module',
                'module': 'easyocr',
                'required': False,
                'description': 'Silnik OCR AI (obsługuje GPU)',
                'install_link': 'https://pypi.org/project/easyocr/',
                'install_cmd': 'pip install easyocr'
            },
            {
                'name': 'PaddleOCR',
                'type': 'module',
                'module': 'paddleocr',
                'required': False,
                'description': 'Silnik OCR AI (obsługuje GPU)',
                'install_link': 'https://pypi.org/project/paddleocr/',
                'install_cmd': 'pip install paddlepaddle paddleocr'
            },
            {
                'name': 'PIL/Pillow',
                'type': 'module',
                'module': 'PIL',
                'required': True,
                'description': 'Biblioteka przetwarzania obrazów',
                'install_link': 'https://pypi.org/project/Pillow/',
                'install_cmd': 'pip install Pillow'
            },
            {
                'name': 'OpenCV',
                'type': 'module',
                'module': 'cv2',
                'required': True,
                'description': 'Zaawansowane przetwarzanie obrazów',
                'install_link': 'https://pypi.org/project/opencv-python/',
                'install_cmd': 'pip install opencv-python'
            },
            {
                'name': 'pdf2image',
                'type': 'module',
                'module': 'pdf2image',
                'required': True,
                'description': 'Konwersja stron PDF do obrazów',
                'install_link': 'https://pypi.org/project/pdf2image/',
                'install_cmd': 'pip install pdf2image'
            },
            {
                'name': 'exchangelib',
                'type': 'module',
                'module': 'exchangelib',
                'required': True,
                'description': 'Połączenie z serwerem Microsoft Exchange',
                'install_link': 'https://pypi.org/project/exchangelib/',
                'install_cmd': 'pip install exchangelib'
            },
            {
                'name': 'tkcalendar',
                'type': 'module',
                'module': 'tkcalendar',
                'required': True,
                'description': 'Widget kalendarza dla interfejsu',
                'install_link': 'https://pypi.org/project/tkcalendar/',
                'install_cmd': 'pip install tkcalendar'
            },
            {
                'name': 'pdfminer.six',
                'type': 'module',
                'module': 'pdfminer',
                'required': True,
                'description': 'Analiza i ekstrakcja danych z PDF',
                'install_link': 'https://pypi.org/project/pdfminer-six/',
                'install_cmd': 'pip install pdfminer.six'
            },
            {
                'name': 'numpy',
                'type': 'module',
                'module': 'numpy',
                'required': False,
                'description': 'Biblioteka do obliczeń numerycznych (może poprawić wydajność OCR)',
                'install_links': {
                    'linux': 'https://numpy.org/install/',
                    'windows': 'https://numpy.org/install/',
                    'darwin': 'https://numpy.org/install/',
                    'default': 'https://numpy.org/install/'
                },
                'install_commands': {
                    'linux': 'pip install numpy',
                    'windows': 'pip install numpy',
                    'darwin': 'pip install numpy',
                    'default': 'pip install numpy'
                },
                'update_link': 'https://numpy.org/install/'
            }
        ]
    
    def check_all_dependencies(self) -> List[Dict]:
        """
        Check all dependencies and return their status.
        
        Returns:
            List of dictionaries with dependency status information
        """
        results = []
        
        for dep in self.dependencies:
            status = self._check_dependency(dep)
            result = {
                'name': dep['name'],
                'description': dep['description'],
                'required': dep['required'],
                'status': status['status'],  # 'ok', 'warning', 'error'
                'emoji': status['emoji'],    # '✅', '⚠️', '❌'
                'message': status['message'],
                'version': status.get('version', ''),
                'install_link': self._get_os_specific_install_link(dep),
                'install_cmd': self._get_os_specific_install_cmd(dep),
                'update_link': dep.get('update_link', '')
            }
            
            # Add version/update information for outdated dependencies
            if status['status'] == 'warning' and 'version' in status and dep.get('min_version'):
                result['update_available'] = True
                result['min_version'] = dep['min_version']
            else:
                result['update_available'] = False
                
            results.append(result)
        
        return results
    
    def _get_os_specific_install_link(self, dep: Dict) -> str:
        """Get OS-specific installation link for a dependency."""
        system = platform.system().lower()
        
        # Check if dependency has OS-specific links
        if 'install_links' in dep:
            links = dep['install_links']
            if system in links:
                return links[system]
            elif 'default' in links:
                return links['default']
        
        # Fall back to general install_link
        return dep.get('install_link', '')
    
    def _get_os_specific_install_cmd(self, dep: Dict) -> str:
        """Get OS-specific installation command for a dependency."""
        system = platform.system().lower()
        
        # Check if dependency has OS-specific commands  
        if 'install_commands' in dep:
            commands = dep['install_commands']
            if system in commands:
                return commands[system]
            elif 'default' in commands:
                return commands['default']
        
        # Fall back to general install_cmd
        return dep.get('install_cmd', '')
    
    def _check_dependency(self, dep: Dict) -> Dict:
        """Check a single dependency."""
        if dep['type'] == 'system':
            return dep['check_func']()
        elif dep['type'] == 'module':
            return self._check_module(dep['module'])
        elif dep['type'] == 'executable':
            return self._check_executable(dep['executable'])
        elif dep['type'] == 'executable_and_module':
            # Special handling for Tesseract with auto-detection
            if dep.get('executable') == 'tesseract':
                return self._check_tesseract_with_autodetection(dep)
            
            # Default handling for other executable_and_module dependencies
            exec_result = self._check_executable(dep['executable'])
            module_result = self._check_module(dep['module'])
            
            if exec_result['status'] == 'ok' and module_result['status'] == 'ok':
                return {
                    'status': 'ok',
                    'emoji': '✅',
                    'message': f"Wykonywalny i moduł Python OK",
                    'version': exec_result.get('version', '')
                }
            elif exec_result['status'] == 'ok' or module_result['status'] == 'ok':
                return {
                    'status': 'warning',
                    'emoji': '⚠️',
                    'message': f"Częściowo dostępny: {exec_result['message']} / {module_result['message']}"
                }
            else:
                return {
                    'status': 'error',
                    'emoji': '❌',
                    'message': f"Niedostępny: {exec_result['message']}"
                }
        elif dep['type'] == 'custom':
            return dep['check_func']()
        else:
            return {
                'status': 'error',
                'emoji': '❌',
                'message': 'Nieznany typ zależności'
            }
    
    def _check_python(self) -> Dict:
        """Check Python version."""
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        # Check minimum version requirement (Python 3.8+)
        if sys.version_info >= (3, 8):
            status = 'ok'
            emoji = '✅'
            message = f"Wersja {version}"
        elif sys.version_info >= (3, 6):
            status = 'warning' 
            emoji = '⚠️'
            message = f"Wersja {version} (zalecana 3.8+)"
        else:
            status = 'error'
            emoji = '❌'
            message = f"Wersja {version} (za stara, wymagana 3.8+)"
        
        return {
            'status': status,
            'emoji': emoji,
            'message': message,
            'version': version,
            'needs_update': status == 'warning'
        }
    
    def _check_module(self, module_name: str) -> Dict:
        """Check if a Python module is available."""
        try:
            module = importlib.import_module(module_name)
            
            # Try to get version
            version = ''
            for version_attr in ['__version__', 'version', 'VERSION']:
                if hasattr(module, version_attr):
                    version = str(getattr(module, version_attr))
                    break
            
            return {
                'status': 'ok',
                'emoji': '✅',
                'message': f"Dostępny {f'v{version}' if version else ''}",
                'version': version
            }
        except ImportError:
            return {
                'status': 'error',
                'emoji': '❌',
                'message': 'Moduł niedostępny'
            }
        except Exception as e:
            return {
                'status': 'warning',
                'emoji': '⚠️',
                'message': f'Błąd importu: {str(e)}'
            }
    
    def _check_executable(self, executable_name: str) -> Dict:
        """Check if an executable is available in PATH."""
        try:
            # Try to run the executable with --version flag
            result = subprocess.run(
                [executable_name, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract version from output (first line usually contains version)
                version_line = result.stdout.strip().split('\n')[0] if result.stdout else ''
                return {
                    'status': 'ok',
                    'emoji': '✅',
                    'message': f"Dostępny w PATH",
                    'version': version_line
                }
            else:
                return {
                    'status': 'warning',
                    'emoji': '⚠️',
                    'message': f'Znaleziony ale błąd wersji (kod: {result.returncode})'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'status': 'warning',
                'emoji': '⚠️',
                'message': 'Znaleziony ale timeout podczas sprawdzania wersji'
            }
        except FileNotFoundError:
            return {
                'status': 'error',
                'emoji': '❌',
                'message': 'Nie znaleziono w PATH'
            }
        except Exception as e:
            return {
                'status': 'warning',
                'emoji': '⚠️',
                'message': f'Błąd sprawdzania: {str(e)}'
            }
    
    def _check_tesseract_with_autodetection(self, dep: Dict) -> Dict:
        """Check Tesseract with auto-detection support."""
        # First check if pytesseract module is available
        module_result = self._check_module(dep['module'])
        
        if module_result['status'] != 'ok':
            return {
                'status': 'error',
                'emoji': '❌',
                'message': f"Moduł pytesseract niedostępny: {module_result['message']}"
            }
        
        # Try to use tesseract_utils for auto-detection
        try:
            from tools.tesseract_utils import get_tesseract_manager
            manager = get_tesseract_manager()
            
            if manager.is_detected:
                # Tesseract detected and configured
                success, test_message = manager.test_tesseract()
                if success:
                    return {
                        'status': 'ok',
                        'emoji': '✅',
                        'message': f"Wykryty automatycznie i skonfigurowany",
                        'version': manager._get_version() or ''
                    }
                else:
                    return {
                        'status': 'warning',
                        'emoji': '⚠️',
                        'message': f"Wykryty ale test nie powiódł się: {test_message}"
                    }
            else:
                # Auto-detection failed, fall back to standard executable check
                exec_result = self._check_executable(dep['executable'])
                if exec_result['status'] == 'ok':
                    return {
                        'status': 'ok',
                        'emoji': '✅',
                        'message': f"Wykonywalny i moduł Python OK",
                        'version': exec_result.get('version', '')
                    }
                else:
                    return {
                        'status': 'warning',
                        'emoji': '⚠️',
                        'message': f"Moduł dostępny, ale tesseract nie znaleziony automatycznie ani w PATH"
                    }
                    
        except ImportError:
            # tesseract_utils not available, fall back to standard check
            exec_result = self._check_executable(dep['executable'])
            if exec_result['status'] == 'ok':
                return {
                    'status': 'ok',
                    'emoji': '✅',
                    'message': f"Wykonywalny i moduł Python OK",
                    'version': exec_result.get('version', '')
                }
            else:
                return {
                    'status': 'warning',
                    'emoji': '⚠️',
                    'message': f"Częściowo dostępny: {exec_result['message']} / {module_result['message']}"
                }
        except Exception as e:
            return {
                'status': 'warning',
                'emoji': '⚠️',
                'message': f'Błąd sprawdzania Tesseract: {str(e)}'
            }

    def _check_poppler(self) -> Dict:
        """Check Poppler using existing poppler_utils."""
        try:
            # Import with full path to avoid issues
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            from poppler_utils import get_poppler_manager
            
            manager = get_poppler_manager()
            if manager.is_detected:
                return {
                    'status': 'ok',
                    'emoji': '✅',
                    'message': 'Dostępny i skonfigurowany'
                }
            else:
                error_msg = getattr(manager, 'detection_error', 'Nieznany błąd')
                return {
                    'status': 'error',
                    'emoji': '❌',
                    'message': f'Niedostępny: {error_msg}'
                }
        except ImportError as e:
            return {
                'status': 'error',
                'emoji': '❌',
                'message': f'Moduł poppler_utils niedostępny: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'warning',
                'emoji': '⚠️',
                'message': f'Błąd sprawdzania: {str(e)}'
            }
    
    def get_summary(self) -> Dict:
        """Get summary of dependency check results."""
        results = self.check_all_dependencies()
        
        total = len(results)
        ok_count = sum(1 for r in results if r['status'] == 'ok')
        warning_count = sum(1 for r in results if r['status'] == 'warning')
        error_count = sum(1 for r in results if r['status'] == 'error')
        
        required_missing = sum(1 for r in results if r['required'] and r['status'] == 'error')
        
        if required_missing > 0:
            overall_status = 'error'
            overall_emoji = '❌'
            overall_message = f'Brak {required_missing} wymaganych zależności'
        elif error_count > 0 or warning_count > 0:
            overall_status = 'warning'
            overall_emoji = '⚠️'
            overall_message = f'{ok_count}/{total} zależności OK'
        else:
            overall_status = 'ok'
            overall_emoji = '✅'
            overall_message = f'Wszystkie zależności dostępne ({total}/{total})'
        
        return {
            'status': overall_status,
            'emoji': overall_emoji,
            'message': overall_message,
            'total': total,
            'ok': ok_count,
            'warning': warning_count,
            'error': error_count,
            'required_missing': required_missing
        }


# Global instance
_dependency_checker = None

def get_dependency_checker() -> DependencyChecker:
    """Get the global dependency checker instance."""
    global _dependency_checker
    if _dependency_checker is None:
        _dependency_checker = DependencyChecker()
    return _dependency_checker


def check_dependencies() -> List[Dict]:
    """Quick function to check all dependencies."""
    return get_dependency_checker().check_all_dependencies()


def get_dependencies_summary() -> Dict:
    """Quick function to get dependencies summary."""
    return get_dependency_checker().get_summary()


if __name__ == "__main__":
    # Command line interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Check system dependencies")
    parser.add_argument("--summary", action="store_true", help="Show summary only")
    parser.add_argument("--detailed", action="store_true", help="Show detailed results")
    
    args = parser.parse_args()
    
    checker = get_dependency_checker()
    
    if args.summary or not any([args.detailed]):
        summary = checker.get_summary()
        print(f"\n{summary['emoji']} PODSUMOWANIE ZALEŻNOŚCI")
        print("=" * 40)
        print(f"Status: {summary['message']}")
        print(f"Szczegóły: {summary['ok']} OK, {summary['warning']} ostrzeżenia, {summary['error']} błędy")
        if summary['required_missing'] > 0:
            print(f"⚠️  UWAGA: Brak {summary['required_missing']} wymaganych zależności!")
    
    if args.detailed:
        results = checker.check_all_dependencies()
        print(f"\n📋 SZCZEGÓŁOWE SPRAWDZENIE ZALEŻNOŚCI")
        print("=" * 50)
        
        for result in results:
            required_mark = " (WYMAGANE)" if result['required'] else ""
            version_info = f" - {result['version']}" if result['version'] else ""
            print(f"{result['emoji']} {result['name']}{required_mark}")
            print(f"   {result['description']}")
            print(f"   Status: {result['message']}{version_info}")
            print()