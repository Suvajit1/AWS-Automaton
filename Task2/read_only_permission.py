import os
import subprocess
import getpass

KEY_DIR = os.path.join(os.getcwd(), "keys")
KEY_FILES = ["public-key.pem", "private-key.pem"]
current_user = getpass.getuser()

def fix_pem_permissions_windows():
    for key_file in KEY_FILES:
        full_path = os.path.join(KEY_DIR, key_file)

        print(f"Fixing permissions for {key_file}...")

        commands = [
            ['icacls', full_path, '/reset'],
            ['icacls', full_path, '/inheritance:r'],
            ['icacls', full_path, f'/grant:r', f'{current_user}:R'],
            ['icacls', full_path, '/remove', 'Users'],
            ['icacls', full_path, '/remove', 'BUILTIN\\Users'],
            ['icacls', full_path, '/remove', 'Everyone']
        ]

        for cmd in commands:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error: {result.stderr.strip()}")
            else:
                print(f"{' '.join(cmd)} → Done")

        print(f"✅ Permissions fixed for {key_file}\n")


if __name__ == "__main__":
    if os.name == "nt":
        fix_pem_permissions_windows()
    else:
        print("This script is intended for Windows only.")
