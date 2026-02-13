
import ast
import os
from pathlib import Path

def get_python_files(directory):
    return list(Path(directory).rglob("*.py"))

def analyze_codebase(root_dir):
    defined_functions = {}  # (file, function_name) -> (lineno, is_method)
    references = set()
    
    python_files = get_python_files(root_dir)
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', 'data'}

    # 1. Primera pasada: Recolectar definiciones y referencias
    for file_path in python_files:
        if any(part in exclude_dirs for part in file_path.parts):
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content, filename=str(file_path))
                
            relative_path = os.path.relpath(file_path, root_dir)
            
            for node in ast.walk(tree):
                # Registro de definiciones
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    defined_functions[(relative_path, node.name)] = node.lineno
                
                # Registro de referencias (llamadas, conexiones de señales, etc.)
                if isinstance(node, ast.Name):
                    references.add(node.id)
                elif isinstance(node, ast.Attribute):
                    references.add(node.attr)
                        
        except Exception as e:
            print(f"Error analizando {file_path}: {e}")

    # 2. Segunda pasada: Filtrado inteligente
    # Ignorar métodos especiales de Python y entry points
    ignored_prefixes = {'__', 'test_'}
    ignored_names = {'main', 'run', 'setup', 'app', 'handle', 'event', 'paintEvent', 'closeEvent', 'mousePressEvent', 'mouseMoveEvent'}
    
    orphans = []
    active_count = 0
    
    for (file, func), line in defined_functions.items():
        # Lógica de detección:
        # Una función es huérfana si su nombre no aparece como referencia en NINGÚN lado
        # (exceptuando su propia definición, pero el set de referencias ya incluye todo)
        # Para ser más estrictos, buscamos si el nombre existe en el set de referencias.
        
        is_ignored = any(func.startswith(p) for p in ignored_prefixes) or func in ignored_names
        
        # Como capturamos TODO en 'references', el nombre SIEMPRE estará ahí al menos una vez (la def).
        # Pero en AST, Name/Attribute usualmente se refiere a USOS. 
        # Vamos a ver si el nombre aparece más de lo esperado o simplemente si está en el set
        # (ast.FunctionDef.name no es un ast.Name, así que no se agrega a references automáticamente)
        
        if func not in references and not is_ignored:
            orphans.append((file, func, line))
        else:
            active_count += 1
            
    return defined_functions, orphans, active_count

if __name__ == "__main__":
    root = r"c:\PassGuardian_v2\src" # Enfocarnos en el código fuente
    print(f"Auditando arquitectura en: {root}")
    
    all_funcs, orphans, active_count = analyze_codebase(r"c:\PassGuardian_v2") # Escanear todo para refs
    src_functions = {k: v for k, v in all_funcs.items() if k[0].startswith("src")}
    
    print("\n" + "="*75)
    print(f"{'FUNCION':<30} | {'ARCHIVO':<25} | {'ESTADO'}")
    print("-" * 75)
    
    # Mostrar una mezcla representativa (Activas y Huérfanas)
    sorted_all = sorted(src_functions.items(), key=lambda x: x[0][1])
    
    orphan_map = {(f, n): l for f, n, l in orphans}
    
    for (file, func), line in sorted_all:
        status = "ACTIVA"
        if (file, func) in orphan_map:
            status = "POSIBLE CODIGO MUERTO"
        
        # Limitar salida para no saturar
        print(f"{func[:30]:<30} | {os.path.basename(file):<25} | {status}")

    print("-" * 75)
    print(f"Total funciones en src: {len(src_functions)}")
    print(f"Activas: {active_count}")
    print(f"Sospechosas: {len([o for o in orphans if o[0].startswith('src')])}")
    print("="*75)
