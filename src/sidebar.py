import flet as ft
from src.responsive_menu_layout import ResponsiveMenuLayout, create_page
from .home import Home


class SideBar(ft.UserControl):
    def __init__(self, app_layout, page: ft.Page):
        super().__init__()
        self.app_layout = app_layout
        self.page = page
        
        menu_button = ft.IconButton(ft.icons.MENU)
        
        self.page.appbar = ft.AppBar(
            title=ft.Text("Microsoft Rewards Farmer"),
            leading=menu_button,
            leading_width=40,
            bgcolor=ft.colors.SURFACE_VARIANT,
        )
        
        pages = [
            (
                dict(icon=ft.icons.HOME, selected_icon=ft.icons.HOME, label="Home"),
                Home(self.app_layout, self.page).build()
            ),
            (
                dict(icon=ft.icons.PERSON, selected_icon=ft.icons.PERSON, label="Accounts"),
                create_page("Accounts", "descripton")
            ),
            (
                dict(icon=ft.icons.TELEGRAM, selected_icon=ft.icons.TELEGRAM, label="Telegram"),
                create_page("Telegram", "descripton")
            ),
            (
                dict(icon=ft.icons.DISCORD, selected_icon=ft.icons.DISCORD, label="Discord"),
                create_page("Discord", "descripton")
            ),
            (
                dict(icon=ft.icons.SETTINGS, selected_icon=ft.icons.SETTINGS, label="Settings"),
                create_page("Settings", "descripton")
            )
        ]
        
        menu_layout = ResponsiveMenuLayout(self.page, pages, landscape_minimize_to_icons=True)
        menu_button.on_click = lambda e: menu_layout.toggle_navigation()
        self.page.add(menu_layout)
        
 