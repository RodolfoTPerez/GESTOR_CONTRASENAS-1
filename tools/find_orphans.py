
import ast
import os
from pathlib import Path

def get_python_files(directory):
    return list(Path(directory).rglob("*.py"))

def analyze_codebase(root_dir):
    defined_functions = {} # (file, function_name) -> lineno
    function_calls = set()
    
    python_files = get_python_files(root_dir)
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist'}

    for file_path in python_files:
        if any(part in exclude_dirs for part in file_path.parts):
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
                
            relative_path = os.path.relpath(file_path, root_dir)
            
            for node in ast.walk(tree):
                # Detectar definiciones de funciones y métodos
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Guardamos el nombre de la función
                    defined_functions[(relative_path, node.name)] = node.lineno
                
                # Detectar llamadas a funciones
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        function_calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        function_calls.add(node.func.attr)
                        
        except Exception as e:
            print(f"Error analizando {file_path}: {e}")

    # Clasificar
    orphans = []
    # Excluimos métodos mágicos y funciones comunes de entry point
    ignored_names = {'__init__', 'main', '<lambda>', 'setup', 'run'}
    
    for (file, func), line in defined_functions.items():
        if func not in function_calls and func not in ignored_names:
            orphans.append((file, func, line))
            
    return defined_functions, orphans

if __name__ == "__main__":
    root = r"c:\PassGuardian_v2"
    all_funcs, orphans = analyze_codebase(root)
    
    print(f"--- ANALISIS DE FUNCIONES ---")
    print(f"Total de funciones definidas: {len(all_funcs)}")
    print(f"Posibles funciones huérfanas encontradas: {len(orphans)}")
    print("-" * 50)
    
    # Agrupar por archivo
    from collections import defaultdict
    grouped = defaultdict(list)
    for file, func, line in orphans:
        grouped[file].append((func, line))
        
    for file in sorted(grouped.keys()):
        print(f"\nARCHIVO: {file}")
        for func, line in sorted(grouped[file], key=lambda x: x[1]):
            print(f"  - L{line}: {func}")
