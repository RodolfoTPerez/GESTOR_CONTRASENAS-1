
import os
import ast
from pathlib import Path

def get_python_files(directory):
    files = []
    # Exclude directories
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', '.gemini', 'tmp', 'dist', 'build'}
    for root, dirs, filenames in os.walk(directory):
        # In-place modification of dirs to skip excluded ones
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in filenames:
            if f.endswith(".py"):
                files.append(Path(os.path.join(root, f)))
    return files

def analyze_codebase(root_dir):
    all_files = get_python_files(root_dir)
    defined_functions = {}  # (file, function_name) -> lineno
    function_calls = set()
    imports = set()
    
    # 1. Collect all definitions and all calls/imports
    for file_path in all_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            
            rel_path = os.path.relpath(file_path, root_dir)
            
            for node in ast.walk(tree):
                # Function definitions
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith("__"):
                        defined_functions[(rel_path, node.name)] = node.lineno
                
                # Class method definitions
                elif isinstance(node, ast.ClassDef):
                    for subnode in node.body:
                        if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if not subnode.name.startswith("__"):
                                defined_functions[(rel_path, subnode.name)] = subnode.lineno

                # Function calls
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        function_calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        function_calls.add(node.func.attr)

                # Imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)

        except Exception as e:
            # Silently skip errors for now or log them properly
            pass

    # 2. Identify orphaned functions
    orphans = []
    # common entry points or special methods to exclude
    exclude_names = {
        'main', 'run', 'setup', 'paintEvent', 'resizeEvent', 'closeEvent', 
        'mouseMoveEvent', 'mousePressEvent', 'mouseReleaseEvent', 'wheelEvent',
        'keyPressEvent', 'focusInEvent', 'focusOutEvent', 'changeEvent',
        'eventFilter', 'test_shared_privacy' # Add common test entry points
    }
    
    for (file, func), line in defined_functions.items():
        # Heuristic: if it's in a test file, it's likely used by pytest
        if "test_" in file.lower() or file.startswith("tests"):
            if func.startswith("test_") or func in exclude_names:
                continue
                
        if func not in function_calls and func not in exclude_names:
            orphans.append((file, func, line))

    # 3. Identify potentially unused files
    # Only check files in src/
    src_files = [os.path.relpath(f, root_dir) for f in all_files if "src" in str(f)]
    unused_files = []
    
    import_paths = set()
    for imp in imports:
        import_paths.add(imp.replace(".", os.sep))

    for sf in src_files:
        if sf.endswith("__init__.py") or sf.endswith("main.py") or sf.endswith("bootstrap.py"):
            continue
            
        base_sf = os.path.splitext(sf)[0]
        found = False
        for imp in import_paths:
            # Match for src/infrastructure/secrets_manager
            if base_sf.replace(os.sep, "/") == imp.replace(os.sep, "/"):
                found = True
                break
            # Also match if imported as 'infrastructure.secrets_manager' from inside src
            if base_sf.endswith(imp) and (len(base_sf) == len(imp) or base_sf[-(len(imp)+1)] == os.sep):
                found = True
                break
        
        if not found:
            unused_files.append(sf)

    return orphans, unused_files

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

    root = os.getcwd()
    orphans, unused_files = analyze_codebase(root)

    print("--- REPORTE DE AUDITORÍA DE PASSGUARDIAN ---")
    print("\n[+] ARCHIVOS EN 'src/' POSIBLEMENTE NO IMPORTADOS:")
    if not unused_files:
        print("  (Ninguno detectado)")
    else:
        for f in sorted(unused_files):
            print(f"  - {f}")

    print("\n[+] FUNCIONES POSIBLEMENTE HUÉRFANAS (DEFINIDAS PERO NO LLAMADAS):")
    current_file = ""
    found_orphans = False
    for file, func, line in sorted(orphans):
        # Ignore files in root that are scripts (they are orphaned by nature)
        if os.sep not in file and file != "main.py":
            continue
            
        found_orphans = True
        if file != current_file:
            print(f"\nARCHIVO: {file}")
            current_file = file
        print(f"  - L{line}: {func}")
    
    if not found_orphans:
        print("  (Ninguna detectada)")
