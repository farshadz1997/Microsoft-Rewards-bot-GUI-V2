import flet as ft
from pathlib import Path
from src.ui.app_layout import UserInterface
import json


def main():
    directory_path = Path(__file__).parent
    if Path(directory_path / "accounts.json").exists():
        pass
    else:
        with open(directory_path / "accounts.json", "w") as f:
            f.write(json.dumps([{"username": "Your Email", "password": "Your Password"}], indent=4))
    ft.app(target=UserInterface)
    

if __name__ == "__main__":
    main()