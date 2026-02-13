import os
import ast
from collections import defaultdict

def mapear_proyecto(directorio_raiz):
    funciones_definidas = defaultdict(list) # {nombre_funcion: [archivos]}
    llamadas_detectadas = set()
    
    print(f"🔍 Auditando arquitectura en: {directorio_raiz}\n")

    for root, _, files in os.walk(directorio_raiz):
        for file in files:
            if file.endswith(".py"):
                ruta_completa = os.path.join(root, file)
                with open(ruta_completa, "r", encoding="utf-8") as f:
                    try:
                        tree = ast.parse(f.read())
                        
                        for node in ast.walk(tree):
                            # 1. Detectar definiciones de funciones
                            if isinstance(node, ast.FunctionDef):
                                funciones_definidas[node.name].append(file)
                            
                            # 2. Detectar llamadas a funciones
                            if isinstance(node, ast.Call):
                                if isinstance(node.func, ast.Name):
                                    llamadas_detectadas.add(node.func.id)
                                elif isinstance(node.func, ast.Attribute):
                                    llamadas_detectadas.add(node.func.attr)
                    except Exception as e:
                        print(f"❌ Error leyendo {file}: {e}")

    # --- REPORTE DE QA ---
    print(f"{'FUNCION':<30} | {'ARCHIVO':<25} | {'ESTADO'}")
    print("-" * 75)
    
    for func, archivos in funciones_definidas.items():
        # Ignorar métodos mágicos de Python como __init__
        if func.startswith("__"): continue
        
        estado = "✅ ACTIVA" if func in llamadas_detectadas else "⚠️ POSIBLE CÓDIGO MUERTO"
        archivos_str = ", ".join(archivos)
        print(f"{func:<30} | {archivos_str:<25} | {estado}")

if __name__ == "__main__":
    # Apuntamos a tu carpeta de código fuente
    ruta_src = os.path.join(os.getcwd(), "src")
    mapear_proyecto(ruta_src)