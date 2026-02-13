
import ast
import os
import sys
from pathlib import Path

# Forzar salida UTF-8 para que los emojis no rompan Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def get_python_files(directory):
    return list(Path(directory).rglob("*.py"))

def analyze_codebase(root_dir):
    defined_functions = {}  # (file, function_name) -> lineno
    references = set()
    
    python_files = get_python_files(root_dir)
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist'}
    scanned_count = 0

    for file_path in python_files:
        if any(part in exclude_dirs for part in file_path.parts):
            continue
            
        scanned_count += 1
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
                
            relative_path = os.path.relpath(file_path, root_dir)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defined_functions[(relative_path, node.name)] = node.lineno
                
                if isinstance(node, ast.Name):
                    references.add(node.id)
                elif isinstance(node, ast.Attribute):
                    references.add(node.attr)
                        
        except Exception as e:
            pass

    ignored_prefixes = {'__', 'test_'}
    ignored_names = {'main', 'run', 'setup', 'app', 'handle', 'event', 'paintEvent', 'closeEvent', 'mousePressEvent', 'mouseMoveEvent'}
    
    results = []
    for (file, func), line in defined_functions.items():
        # Reportar funciones en src/ y también en la raíz que no sean de sistema
        is_ignored = any(func.startswith(p) for p in ignored_prefixes) or func in ignored_names
        
        if func in references or is_ignored:
            status = "✅ ACTIVA"
        else:
            status = "⚠️ HUERFANA"
        
        results.append({
            "func": func,
            "file": file, # Guardamos la ruta completa para verificar
            "status": status
        })
            
    return sorted(results, key=lambda x: x["func"]), scanned_count

if __name__ == "__main__":
    root = r"c:\PassGuardian_v2"
    report, total_files = analyze_codebase(root)
    
    print(f"VERIFICACIÓN DE ESCANEO:")
    print(f"- Total de archivos .py procesados: {total_files}")
    print(f"- Total de funciones detectadas: {len(report)}")
    print("-" * 75)
    print(f"{'FUNCION':<30} | {'ARCHIVO':<40} | {'ESTADO'}")
    print("-" * 85)
    
    for item in report[:50]: # Mostramos las primeras 50 para validar
        print(f"{item['func'][:30]:<30} | {item['file'][:40]:<40} | {item['status']}")
    print("...")
