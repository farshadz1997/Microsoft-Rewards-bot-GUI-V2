import flet as ft
from src.sidebar import SideBar
from src.home import Home
from src.responsive_menu_layout import ResponsiveMenuLayout, create_page

class UserInterface:
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Microsoft Rewards Farmer"
        self.ui()
        self.page.update()
        
    def ui(self):
        SideBar(self, self.page)
        
        
if __name__ == "__main__":
    ft.app(target=UserInterface)