import subprocess
import sys
import os

if __name__ == "__main__":
    # Change to the directory where main.py is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--reload"], check=True)
