"""
System dependencies checker for KSIEGI-OCR application.
Checks all required dependencies and provides status information.
"""
import sys
import subprocess
import importlib
from typing import Dict, List, Tuple, Optional
from pathlib import Path


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
                'description': 'Interpreter Python'
            },
            {
                'name': 'Tkinter',
                'type': 'module',
                'module': 'tkinter',
                'required': True,
                'description': 'Interfejs graficzny'
            },
            {
                'name': 'Tesseract OCR',
                'type': 'executable_and_module',
                'executable': 'tesseract',
                'module': 'pytesseract',
                'required': True,
                'description': 'Silnik OCR Tesseract'
            },
            {
                'name': 'Poppler',
                'type': 'custom',
                'check_func': self._check_poppler,
                'required': True,
                'description': 'Narzędzia PDF'
            },
            {
                'name': 'pdfplumber',
                'type': 'module',
                'module': 'pdfplumber',
                'required': True,
                'description': 'Ekstrakcja tekstu z PDF'
            },
            {
                'name': 'EasyOCR',
                'type': 'module',
                'module': 'easyocr',
                'required': False,
                'description': 'Silnik OCR AI'
            },
            {
                'name': 'PaddleOCR',
                'type': 'module',
                'module': 'paddleocr',
                'required': False,
                'description': 'Silnik OCR AI'
            },
            {
                'name': 'PIL/Pillow',
                'type': 'module',
                'module': 'PIL',
                'required': True,
                'description': 'Przetwarzanie obrazów'
            },
            {
                'name': 'OpenCV',
                'type': 'module',
                'module': 'cv2',
                'required': True,
                'description': 'Przetwarzanie obrazów'
            },
            {
                'name': 'pdf2image',
                'type': 'module',
                'module': 'pdf2image',
                'required': True,
                'description': 'Konwersja PDF do obrazów'
            },
            {
                'name': 'exchangelib',
                'type': 'module',
                'module': 'exchangelib',
                'required': True,
                'description': 'Połączenie z Exchange'
            },
            {
                'name': 'tkcalendar',
                'type': 'module',
                'module': 'tkcalendar',
                'required': True,
                'description': 'Widget kalendarza'
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
            results.append({
                'name': dep['name'],
                'description': dep['description'],
                'required': dep['required'],
                'status': status['status'],  # 'ok', 'warning', 'error'
                'emoji': status['emoji'],    # '✅', '⚠️', '❌'
                'message': status['message'],
                'version': status.get('version', '')
            })
        
        return results
    
    def _check_dependency(self, dep: Dict) -> Dict:
        """Check a single dependency."""
        if dep['type'] == 'system':
            return dep['check_func']()
        elif dep['type'] == 'module':
            return self._check_module(dep['module'])
        elif dep['type'] == 'executable':
            return self._check_executable(dep['executable'])
        elif dep['type'] == 'executable_and_module':
            # Check both executable and Python module
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
        return {
            'status': 'ok',
            'emoji': '✅',
            'message': f"Wersja {version}",
            'version': version
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