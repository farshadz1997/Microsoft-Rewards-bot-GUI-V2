import flet as ft
from flet import theme
from src.home import Home
from src.settings import Settings
from src.responsive_menu_layout import ResponsiveMenuLayout, create_page


LIGHT_SEED_COLOR = ft.colors.BLUE
DARK_SEED_COLOR = ft.colors.INDIGO

class UserInterface:
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Microsoft Rewards Farmer"
        self.page.window_prevent_close = True
        self.page.on_window_event = self.window_event
        self.page.theme_mode = self.page.client_storage.get("MRFarmer.theme_mode") if self.page.client_storage.contains_key("MRFarmer.theme_mode") else "dark"
        self.color_scheme = ft.colors.BLUE_300 if self.page.theme_mode == "light" else ft.colors.INDIGO_300
        self.page.theme =  theme.Theme(color_scheme_seed=LIGHT_SEED_COLOR)
        self.page.dark_theme = theme.Theme(color_scheme_seed=DARK_SEED_COLOR)
        self.ui()
        self.page.update()
        
        
    def ui(self):
        menu_button = ft.IconButton(ft.icons.MENU)
        
        self.toggle_theme_button = ft.IconButton(
            ft.icons.MODE_NIGHT if self.page.theme_mode == "light" else ft.icons.WB_SUNNY_ROUNDED,
            on_click=self.toggle_theme_mode,
        )
        
        self.page.appbar = ft.AppBar(
            title=ft.Text("Microsoft Rewards Farmer"),
            leading=menu_button,
            leading_width=40,
            bgcolor=ft.colors.SURFACE_VARIANT,
            actions=[
                self.toggle_theme_button
            ]
        )
        # Exit dialog confirmation
        self.confirm_dialog = ft.AlertDialog(
            modal=False,
            title=ft.Text("Exit confirmation"),
            content=ft.Text("Do you really want to exit?"),
            actions=[
                ft.ElevatedButton("Yes", on_click=lambda _: self.page.window_destroy()),
                ft.OutlinedButton("No", on_click=self.no_click),
            ],
            actions_alignment="end",
        )
        
        self.home_page = Home(self, self.page)
        self.settings_page = Settings(self, self.page)
        pages = [
            (
                dict(icon=ft.icons.HOME, selected_icon=ft.icons.HOME, label="Home"),
                self.home_page.build()
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
                self.settings_page.build()
            )
        ]
        
        menu_layout = ResponsiveMenuLayout(self.page, pages, landscape_minimize_to_icons=True)
        menu_button.on_click = lambda e: menu_layout.toggle_navigation()
        self.page.add(menu_layout)
        
        
    def window_event(self, e):
        if e.data == "close":
            self.page.dialog = self.confirm_dialog
            self.confirm_dialog.open = True
            self.page.update()
            
    def no_click(self, e):
        self.confirm_dialog.open = False
        self.page.update()
    
    def toggle_theme_mode(self, e):
        self.page.theme_mode = "dark" if self.page.theme_mode == "light" else "light"
        self.page.client_storage.set("MRFarmer.theme_mode", self.page.theme_mode)
        self.color_scheme = ft.colors.BLUE_300 if self.page.theme_mode == "light" else ft.colors.INDIGO_300
        self.toggle_theme_button.icon = (
            ft.icons.MODE_NIGHT if self.page.theme_mode == "light" else ft.icons.WB_SUNNY_ROUNDED
        )
        self.home_page.toggle_theme_mode(self.color_scheme)
        self.settings_page.toggle_theme_mode(self.color_scheme)
        self.page.update()
        
        
if __name__ == "__main__":
    ft.app(target=UserInterface)