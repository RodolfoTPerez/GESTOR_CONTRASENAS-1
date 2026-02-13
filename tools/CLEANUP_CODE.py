from pathlib import Path
import os
import sys
BASE_DIR = Path(__file__).resolve().parent.parent

import os
import ast

def comment_function(file_path, function_name):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())

    start_line = -1
    end_line = -1

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            start_line = node.lineno - 1
            # Simple heuristic for end line (node.end_lineno is available in Python 3.8+)
            if hasattr(node, 'end_lineno'):
                end_line = node.end_lineno
            else:
                # Fallback: find the next node or use the last line of the body
                end_line = max(n.lineno for n in ast.walk(node)) 

    if start_line != -1:
        print(f"Commenting {function_name} in {file_path} (Lines {start_line+1}-{end_line})")
        
        # Add a header comment
        lines.insert(start_line, f"# [LEGACY] {function_name} - Commented out during cleanup\n")
        
        # Adjust indices because of the insertion
        start_line += 1
        end_line += 1
        
        for i in range(start_line, end_line):
            if i < len(lines):
                lines[i] = "# " + lines[i]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    else:
        print(f"Function {function_name} not found in {file_path}")

# DEAD CODE LIST
DEATH_NOTE = [
    (r"src/infrastructure/guardian_ai.py", "get_smart_suggestion"),
    (r"src/infrastructure/guardian_ai.py", "calculate_crack_time"),
    (r"src/infrastructure/sync_manager.py", "upload_audit_event"),
    (r"src/infrastructure/sync_manager.py", "_get_public_ip"),
    (r"src/infrastructure/db.py", "init_db")
]

if __name__ == "__main__":
    base_path = rstr(BASE_DIR) + ""
    for file_rel, func in DEATH_NOTE:
        full_path = os.path.join(base_path, file_rel)
        comment_function(full_path, func)
    
    print("\n>>> Operación de Limpieza (Comentado) Finalizada.")
