import os

def create_inits(root_dir):
    for root, dirs, files in os.walk(root_dir):
        if "__pycache__" in root:
            continue
        if "__init__.py" not in files:
            init_path = os.path.join(root, "__init__.py")
            print(f"Creating {init_path}")
            with open(init_path, 'w', encoding='utf-8') as f:
                f.write(f"# Package {os.path.basename(root)}\n")

if __name__ == "__main__":
    create_inits(r"c:\PassGuardian_v2\src")
