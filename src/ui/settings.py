import flet as ft
from ..core.farmer import PC_USER_AGENT, MOBILE_USER_AGENT


class ThemeChanger(ft.UserControl):
    def __init__(self, parent, page: ft.Page):
        from .app_layout import UserInterface
        super().__init__()
        self.parent: UserInterface = parent
        self.page = page
        self.color_scheme = parent.color_scheme
        self.ui()
        self.page.update()
        # self.set_initial_values()
    
    def color_option_creator(self, color: str):
        return ft.Container(
            bgcolor=color,
            border_radius=ft.border_radius.all(50),
            height=10,
            width=10,
            padding=ft.padding.all(5),
            alignment=ft.alignment.center,
            data=color
        )
    
    def ui(self):
        option_dict = {
            ft.colors.LIGHT_GREEN: self.color_option_creator(ft.colors.LIGHT_GREEN),
            ft.colors.RED_200: self.color_option_creator(ft.colors.RED_200),
            ft.colors.AMBER_500: self.color_option_creator(ft.colors.AMBER_500),
            ft.colors.PINK_300: self.color_option_creator(ft.colors.PINK_300),
            ft.colors.ORANGE_300: self.color_option_creator(ft.colors.ORANGE_300),
            ft.colors.LIGHT_BLUE: self.color_option_creator(ft.colors.LIGHT_BLUE),
            ft.colors.DEEP_ORANGE_300: self.color_option_creator(ft.colors.DEEP_ORANGE_300),
            ft.colors.PURPLE_100: self.color_option_creator(ft.colors.PURPLE_100),
            ft.colors.RED_700: self.color_option_creator(ft.colors.RED_700),
            ft.colors.TEAL_500: self.color_option_creator(ft.colors.TEAL_500),
            ft.colors.YELLOW_400: self.color_option_creator(ft.colors.YELLOW_400),
            ft.colors.PURPLE_400: self.color_option_creator(ft.colors.PURPLE_400),
            ft.colors.BROWN_300: self.color_option_creator(ft.colors.BROWN_300),
            ft.colors.CYAN_500: self.color_option_creator(ft.colors.CYAN_500),
            ft.colors.BLUE_GREY_500: self.color_option_creator(ft.colors.BLUE_GREY_500),
        }
        
        self.theme_color_grid = ft.GridView(
            expand=5,
            runs_count=6,
        )
        for color in option_dict.values():
            color.on_click = self.set_theme_color
            self.theme_color_grid.controls.append(color)
            
        self.widget_color_grid = ft.GridView(
            expand=5,
            runs_count=6
        )
        for color in option_dict.values():
            color.on_click = self.set_widget_color
            self.widget_color_grid.controls.append(color)
            
        
    def build(self):
        return self.theme_changer
        
    def change_theme(self, theme: str):
        self.parent.toggle_theme_mode(theme)
    
    def set_theme_color(self, e):
        pass
    
    def set_widget_color(self, e):
        pass
        
    def set_initial_values(self):
        if self.parent.theme == "light":
            self.light_theme_button.disabled = True
            self.dark_theme_button.disabled = False
        else:
            self.light_theme_button.disabled = False
            self.dark_theme_button.disabled = True


class Settings(ft.UserControl):
    def __init__(self, parent, page: ft.Page):
        from .app_layout import UserInterface
        super().__init__()
        self.parent: UserInterface = parent
        self.page = page
        self.color_scheme = parent.color_scheme
        self.ui()
        self.page.update()
        self.set_initial_values()
        
    def ui(self):
        self.pc_user_agent_field = ft.TextField(
            label="PC User Agent",
            multiline=False,
            text_size=14,
            icon=ft.icons.COMPUTER,
            border_color=self.color_scheme,
            error_style=ft.TextStyle(color="red"),
            dense=True,
            expand=True,
            on_change=lambda _: self.user_agents_on_change(self.pc_user_agent_field),
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                icon_size=14,
                on_click=lambda _: self.clear_field(self.pc_user_agent_field)
            )        
        )
        self.mobile_user_agent_field = ft.TextField(
            label="Mobile User Agent",
            multiline=False,
            text_size=14,
            icon=ft.icons.PHONE_ANDROID,
            border_color=self.color_scheme,
            error_style=ft.TextStyle(color="red"),
            dense=True,
            expand=True,
            on_change=lambda _: self.user_agents_on_change(self.mobile_user_agent_field),
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                icon_size=14,
                on_click=lambda _: self.clear_field(self.mobile_user_agent_field)
            )        
        )
        self.delete_user_agents_button = ft.TextButton(
            text="Reset to defaults",
            icon=ft.icons.RESTART_ALT,
            icon_color=self.color_scheme,
            tooltip="Delete saved user agents and use defaults",
            on_click=self.reset_to_default_user_agents,
        )
        self.save_user_agents_button = ft.TextButton(
            text="Save",
            icon=ft.icons.SAVE,
            icon_color=self.color_scheme,
            tooltip="Save user agents",
            on_click=self.save_user_agents,
        )
        self.user_agent_settings = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    value="Settings",
                                    text_align="center",
                                    size=24,
                                    weight="bold",
                                    expand=6
                                )
                            ],
                            vertical_alignment="center",
                        ),
                        ft.Divider(),
                        ft.Row([self.pc_user_agent_field]),
                        ft.Row([self.mobile_user_agent_field]),
                        ft.Row(
                            controls=[
                                self.delete_user_agents_button,
                                self.save_user_agents_button
                            ],
                            alignment="end"
                        )
                    ]
                ),
                margin=ft.margin.all(15)
            ),
            expand=6
        )
        
        # global settings
        self.headless_switch = ft.Switch(
            label="Headless",
            value=False,
            active_color=self.color_scheme,
            tooltip="Creates browser instance in background without GUI (NOT RECOMMENDED)",
            on_change=lambda e: self.switches_on_change(e, self.headless_switch)
        )
        self.session_switch = ft.Switch(
            label="Session",
            value=False,
            active_color=self.color_scheme,
            tooltip="Saves browser session and cookies in accounts directory",
            on_change=lambda e: self.switches_on_change(e, self.session_switch)
        )
        self.fast_switch = ft.Switch(
            label="Fast",
            value=False,
            active_color=self.color_scheme,
            tooltip="Reduce delays between actions",
            on_change=lambda e: self.switches_on_change(e, self.fast_switch)
        )
        self.save_errors_switch = ft.Switch(
            label="Save errors",
            value=False,
            active_color=self.color_scheme,
            tooltip="Save errors in a txt file",
            on_change=lambda e: self.switches_on_change(e, self.save_errors_switch)
        )
        self.shutdown_switch = ft.Switch(
            label="Shutdown",
            value=False,
            active_color=self.color_scheme,
            tooltip="Shutdown computer after farming",
            on_change=lambda e: self.switches_on_change(e, self.shutdown_switch)
        )
        self.edge_switch = ft.Switch(
            label="Edge webdriver",
            value=False,
            active_color=self.color_scheme,
            tooltip="Use Microsoft Edge webdriver instead of Chrome webdriver",
            on_change=lambda e: self.switches_on_change(e, self.edge_switch)
        )
        self.use_proxy = ft.Switch(
            label="Use proxy",
            value=False,
            active_color=self.color_scheme,
            tooltip="Use proxy in browser instance if you have set it in your account",
            on_change=lambda e: self.switches_on_change(e, self.use_proxy)
        )
        self.auto_start_switch = ft.Switch(
            label="Auto start",
            value=False,
            active_color=self.color_scheme,
            tooltip="Start farming automatically when you start the program",
            on_change=lambda e: self.switches_on_change(e, self.auto_start_switch)
        )
        self.global_settings = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ListTile(
                            title=ft.Text("Global settings"),
                            leading=ft.Icon(ft.icons.SETTINGS_APPLICATIONS),
                        ),
                        ft.Row(
                            controls=[
                                self.headless_switch,
                                self.edge_switch
                            ],
                            spacing=130
                        ),
                        ft.Row(
                            [self.session_switch, self.use_proxy],
                            spacing=140,
                        ),
                        ft.Row(
                            controls=[
                                self.fast_switch,
                                self.auto_start_switch
                            ],
                            spacing=162,
                        ),
                        ft.Row([self.save_errors_switch]),
                        ft.Row([self.shutdown_switch]),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                margin=ft.margin.all(15)
            ),
            expand=3,
        )
        
        # farmer settings
        self.daily_quests_switch = ft.Switch(
            label="Daily quests",
            value=True,
            active_color=self.color_scheme,
            on_change=lambda e: self.switches_on_change(e, self.daily_quests_switch)
        )
        self.punch_cards_switch = ft.Switch(
            label="Punch cards",
            value=True,
            active_color=self.color_scheme,
            on_change=lambda e: self.switches_on_change(e, self.punch_cards_switch)
        )
        self.more_activities_switch = ft.Switch(
            label="More activities",
            value=True,
            active_color=self.color_scheme,
            on_change=lambda e: self.switches_on_change(e, self.more_activities_switch)
        )
        self.pc_search_switch = ft.Switch(
            label="PC search",
            value=True,
            active_color=self.color_scheme,
            on_change=lambda e: self.switches_on_change(e, self.pc_search_switch)
        )
        self.mobile_search_switch = ft.Switch(
            label="Mobile search",
            value=True,
            active_color=self.color_scheme,
            on_change=lambda e: self.switches_on_change(e, self.mobile_search_switch)
        )
        self.msn_shopping_game_switch = ft.Switch(
            label="MSN shopping game",
            value=False,
            active_color=self.color_scheme,
            on_change=lambda e: self.switches_on_change(e, self.msn_shopping_game_switch)
        )
        self.farmer_settings = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ListTile(
                            title=ft.Text("Farmer settings"),
                            leading=ft.Icon(ft.icons.SETTINGS_APPLICATIONS),
                        ),
                        ft.Row([self.daily_quests_switch, self.msn_shopping_game_switch], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([self.punch_cards_switch]),
                        ft.Row([self.more_activities_switch]),
                        ft.Row([self.pc_search_switch]),
                        ft.Row([self.mobile_search_switch]),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                margin=ft.margin.all(15)
            ),
            expand=3,
        )
        
        self.theme_changer = ThemeChanger(self.parent, self.page)
        
    def build(self):
        return ft.Container(
            margin=ft.margin.all(25),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment="stretch",
                controls=[
                    ft.Row([self.user_agent_settings]),
                    ft.Row(
                        controls=[
                            self.global_settings,
                            self.farmer_settings
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row(
                        controls=[
                            ft.Card(
                                expand=True,
                                content=ft.Container(
                                    margin=ft.margin.all(15),
                                    content=ft.Column(
                                        controls=[
                                            ft.Row(
                                                controls=[
                                                    ft.Text("Theme color", text_align="center", expand=5, size=24, weight="bold"),
                                                    ft.VerticalDivider(),
                                                    ft.Text("Widgets color", text_align="center", expand=5, size=24, weight="bold"),
                                                ]
                                            ),
                                            ft.Divider(),
                                            ft.Row(
                                                controls=[
                                                    self.theme_changer.theme_color_grid,
                                                    ft.VerticalDivider(),
                                                    self.theme_changer.widget_color_grid
                                                ]
                                            )
                                        ],
                                    )
                                )
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                ]
            )
        )
    
    def set_initial_values(self):
        # user-agents
        self.pc_user_agent_field.value = self.page.client_storage.get("MRFarmer.pc_user_agent")
        self.mobile_user_agent_field.value = self.page.client_storage.get("MRFarmer.mobile_user_agent")
        # global settings
        self.headless_switch.value = self.page.client_storage.get("MRFarmer.headless")
        self.fast_switch.value = self.page.client_storage.get("MRFarmer.fast")
        self.session_switch.value = self.page.client_storage.get("MRFarmer.session")
        self.save_errors_switch.value = self.page.client_storage.get("MRFarmer.save_errors")
        self.shutdown_switch.value = self.page.client_storage.get("MRFarmer.shutdown")
        self.edge_switch.value = self.page.client_storage.get("MRFarmer.edge_webdriver")
        self.edge_switch.value = self.page.client_storage.get("MRFarmer.use_proxy")
        self.auto_start_switch.value = self.page.client_storage.get("MRFarmer.auto_start")
        # farmer settings
        self.daily_quests_switch.value = self.page.client_storage.get("MRFarmer.daily_quests")
        self.punch_cards_switch.value = self.page.client_storage.get("MRFarmer.punch_cards")
        self.more_activities_switch.value = self.page.client_storage.get("MRFarmer.more_activities")
        self.pc_search_switch.value = self.page.client_storage.get("MRFarmer.pc_search")
        self.mobile_search_switch.value = self.page.client_storage.get("MRFarmer.mobile_search")
        self.msn_shopping_game_switch.value = self.page.client_storage.get("MRFarmer.msn_shopping_game")
        self.page.update()
    
    def clear_field(self, control: ft.TextField):
        control.value = None
        control.error_text = "This field is required"
        self.page.update()

    def save_user_agents(self, e):
        user_agents_fields = [self.pc_user_agent_field, self.mobile_user_agent_field]
        error = False
        for field in user_agents_fields:
            if field.value == "":
                field.error_text = "This field is required"
                error = True
        if error:
            self.parent.open_snack_bar("Please fill in all fields.")
            self.page.update()
            return
        self.page.client_storage.set("MRFarmer.pc_user_agent", self.pc_user_agent_field.value)
        self.page.client_storage.set("MRFarmer.mobile_user_agent", self.mobile_user_agent_field.value)
        self.parent.open_snack_bar("User agents have been saved.")
    
    def user_agents_on_change(self, control: ft.TextField):
        if control.value == "":
            control.error_text = "This field is required"
        else:
            control.error_text = None
        self.page.update()
            
    def reset_to_default_user_agents(self, e):
        user_agents_fields = [self.pc_user_agent_field, self.mobile_user_agent_field]
        for field in user_agents_fields:
            if field.error_text:
                field.error_text = None
        self.page.client_storage.set("MRFarmer.pc_user_agent", PC_USER_AGENT)
        self.pc_user_agent_field.value = PC_USER_AGENT
        self.page.client_storage.set("MRFarmer.mobile_user_agent", MOBILE_USER_AGENT)
        self.mobile_user_agent_field.value = MOBILE_USER_AGENT
        self.parent.open_snack_bar("User agents have been reset to default.")
        self.page.update()
    
    def switches_on_change(self, e, control: ft.Switch):
        farmer_options = [
            self.daily_quests_switch,
            self.punch_cards_switch,
            self.more_activities_switch,
            self.pc_search_switch,
            self.mobile_search_switch,
            self.msn_shopping_game_switch
        ]
        if control in farmer_options and not control.value:
            count_of_true_controls = 0
            for ctrl in farmer_options:
                if ctrl.value:
                    count_of_true_controls += 1
                if count_of_true_controls > 1:
                    break
            if count_of_true_controls == 0:
                control.value = True
                self.page.update()
                self.parent.display_error("Farmer settings error", "You must select at least one farmer option")
                return
        name = control.label.lower().replace(" ", "_")
        self.page.client_storage.set(f"MRFarmer.{name}", control.value)
        if control == self.auto_start_switch and control.value:
            self.parent.display_error("Auto start", "Auto start will be enabled after the next start of the app.")
        
    def toggle_theme_mode(self, color_scheme):
        self.color_scheme = color_scheme
        # user-agents
        self.pc_user_agent_field.border_color = color_scheme
        self.mobile_user_agent_field.border_color = color_scheme
        self.delete_user_agents_button.icon_color = color_scheme
        self.save_user_agents_button.icon_color = color_scheme
        # global settings
        self.headless_switch.active_color = color_scheme
        self.fast_switch.active_color = color_scheme
        self.session_switch.active_color = color_scheme
        self.save_errors_switch.active_color = color_scheme
        self.shutdown_switch.active_color = color_scheme
        self.edge_switch.active_color = color_scheme
        self.use_proxy.active_color = color_scheme
        self.auto_start_switch.active_color = color_scheme
        # farmer settings
        self.daily_quests_switch.active_color = color_scheme
        self.punch_cards_switch.active_color = color_scheme
        self.more_activities_switch.active_color = color_scheme
        self.pc_search_switch.active_color = color_scheme
        self.mobile_search_switch.active_color = color_scheme
        self.msn_shopping_game_switch.active_color = color_scheme
    