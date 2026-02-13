import os

def update_imports(root_dir):
    old_import = "from src.presentation.messages import MESSAGES"
    new_import = "from src.domain.messages import MESSAGES"
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if old_import in content:
                    print(f"Updating {file_path}")
                    new_content = content.replace(old_import, new_import)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

if __name__ == "__main__":
    update_imports(r"c:\PassGuardian_v2\src")
