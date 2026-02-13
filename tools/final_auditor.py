
import ast
import os
import sys
from pathlib import Path

# Configuración de salida UTF-8 para Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def analyze_full_project(root_dir):
    defined_functions = {}  # (file, function_name) -> lineno
    references = set()
    all_py_files = []
    
    # Extensiones a ignorar (entornos virtuales, caches, etc)
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'build', 'dist', '.gemini', 'data'}
    
    # 1. Recolectar todos los archivos y mapear el código
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                all_py_files.append(full_path)
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        tree = ast.parse(content, filename=full_path)
                    
                    rel_path = os.path.relpath(full_path, root_dir)
                    
                    for node in ast.walk(tree):
                        # Definiciones
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            defined_functions[(rel_path, node.name)] = node.lineno
                        
                        # Referencias (Nombres, Atributos, Imports)
                        if isinstance(node, ast.Name):
                            references.add(node.id)
                        elif isinstance(node, ast.Attribute):
                            references.add(node.attr)
                        elif isinstance(node, ast.Import):
                            for n in node.names:
                                references.add(n.name.split('.')[-1])
                        elif isinstance(node, ast.ImportFrom):
                            for n in node.names:
                                references.add(n.name)
                                
                except Exception:
                    pass

    # 2. Clasificar Funciones
    ignored_prefixes = {'__', 'test_'}
    # Agregamos métodos de Qt que se disparan por eventos
    ignored_names = {
        'main', 'run', 'setup', 'app', 'handle', 'event', 'paintEvent', 
        'closeEvent', 'mousePressEvent', 'mouseMoveEvent', 'focusInEvent', 
        'focusOutEvent', 'eventFilter', 'resizeEvent', 'wheelEvent'
    }
    
    function_report = []
    for (file, func), line in defined_functions.items():
        is_ignored = any(func.startswith(p) for p in ignored_prefixes) or func in ignored_names
        status = "✅ ACTIVA" if (func in references or is_ignored) else "⚠️ HUERFANA"
        function_report.append(f"{func[:30]:<30} | {os.path.basename(file):<25} | {status}")

    # 3. Detectar Archivos Muertos (Scripts que nadie importa ni usa)
    # Un archivo es sospechoso si no es un entry point (main.py, etc) y nadie lo referencia
    dead_files = []
    core_files = {'main.py', 'bootstrap.py', 'config.py'}
    
    for full_path in all_py_files:
        filename = os.path.basename(full_path)
        rel_path = os.path.relpath(full_path, root_dir)
        
        # Ignorar archivos en src/ (asumimos que la arquitectura src es viva por definición si hay funciones activas)
        if rel_path.startswith("src"):
            continue
            
        # Si el nombre del archivo (sin .py) no aparece en ninguna referencia y no es core
        module_name = filename[:-3]
        if module_name not in references and filename not in core_files and not filename.startswith("test_"):
            # Verificar si tiene funciones activas. Si tiene funciones activas, no está muerto.
            has_active = any(f == rel_path and "✅ ACTIVA" in r for (f, n), r in zip(defined_functions.keys(), function_report) if f == rel_path)
            if not has_active:
                dead_files.append(rel_path)

    # 4. Generar el archivo final
    report_path = os.path.join(root_dir, "REPORTE_AUDITORIA_FINAL.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("="*80 + "\n")
        f.write("              REPORTE DE AUDITORÍA DE ARQUITECTURA - PASSGUARDIAN\n")
        f.write("="*80 + "\n\n")
        
        f.write("1. LISTADO DE FUNCIONES Y ESTADO\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'FUNCION':<30} | {'ARCHIVO':<25} | {'ESTADO'}\n")
        f.write("-" * 80 + "\n")
        for line in sorted(function_report):
            f.write(line + "\n")
            
        f.write("\n\n2. ARCHIVOS SOSPECHOSOS (POSIBLE CÓDIGO MUERTO)\n")
        f.write("Estos archivos no son importados por nadie ni parecen ser parte del flujo principal:\n")
        f.write("-" * 80 + "\n")
        if not dead_files:
            f.write("No se encontraron archivos muertos críticos.\n")
        else:
            for df in sorted(dead_files):
                f.write(f"❌ {df}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write(f"Reporte generado automáticamente. Total archivos analizados: {len(all_py_files)}\n")

    return report_path

if __name__ == "__main__":
    path = analyze_full_project(r"c:\PassGuardian_v2")
    print(f"REPORT_CREATED_AT: {path}")
