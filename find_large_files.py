import os

def find_large_files(start_dir, limit=500):
    large_files = []
    exclude_dirs = {'.venv', 'node_modules', '__pycache__', '.git', 'archive'}
    
    for root, dirs, files in os.walk(start_dir):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = sum(1 for _ in f)
                        if lines > limit:
                            large_files.append((full_path, lines))
                except Exception as e:
                    print(f"Error reading {full_path}: {e}")
                    
    return sorted(large_files, key=lambda x: x[1], reverse=True)

if __name__ == "__main__":
    project_root = r"c:\PassGuardian_v2"
    large_files = find_large_files(project_root)
    print(f"{'Path':<80} | {'Lines':<10}")
    print("-" * 95)
    for path, lines in large_files:
        print(f"{path:<80} | {lines:<10}")
