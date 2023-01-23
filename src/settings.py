import flet as ft
from .core.farmer import PC_USER_AGENT, MOBILE_USER_AGENT


class Settings(ft.UserControl):
    def __init__(self, parent, page: ft.Page):
        super().__init__()
        self.parent = parent
        self.page = page
        self.color_scheme = parent.color_scheme
        self.ui()
        self.page.update()
        self.set_initial_values()
        
    def ui(self):
        self.pc_user_agent_field = ft.TextField(
            label="PC User Agent",
            multiline=False,
            icon=ft.icons.COMPUTER,
            border_color=self.color_scheme,
            height=60,
            expand=6,
            text_size=14,
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                on_click=self.clear_pc_user_agent_field
            )        
        )
        self.mobile_user_agent_field = ft.TextField(
            label="Mobile User Agent",
            multiline=False,
            icon=ft.icons.PHONE_ANDROID,
            border_color=self.color_scheme,
            height=60,
            expand=6,
            text_size=14,
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                on_click=self.clear_mobile_user_agent_field
            )        
        )
        self.delete_user_agents_button = ft.TextButton(
            text="Delete",
            icon=ft.icons.DELETE,
            icon_color=self.color_scheme,
            tooltip="Delete saved user agents",
            on_click=self.delete_user_agents,
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
            active_color=self.color_scheme,
            tooltip="Creates browser instance in background without GUI (NOT RECOMMENDED)",
            on_change=lambda e: self.switches_on_change(e, self.headless_switch)
        )
        self.session_switch = ft.Switch(
            label="Session",
            active_color=self.color_scheme,
            tooltip="Saves browser session and cookies in accounts directory",
            on_change=lambda e: self.switches_on_change(e, self.session_switch)
        )
        self.fast_switch = ft.Switch(
            label="Fast",
            active_color=self.color_scheme,
            tooltip="Reduce delays between actions",
            on_change=lambda e: self.switches_on_change(e, self.fast_switch)
        )
        self.save_errors_switch = ft.Switch(
            label="Save errors",
            active_color=self.color_scheme,
            tooltip="Save errors in a txt file",
            on_change=lambda e: self.switches_on_change(e, self.save_errors_switch)
        )
        self.shutdown_switch = ft.Switch(
            label="Shutdown",
            active_color=self.color_scheme,
            tooltip="Shutdown computer after farming",
            on_change=lambda e: self.switches_on_change(e, self.shutdown_switch)
        )
        self.global_settings = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ListTile(
                            title=ft.Text("Global settings"),
                            leading=ft.Icon(ft.icons.SETTINGS_APPLICATIONS),
                        ),
                        ft.Row([self.headless_switch]),
                        ft.Row([self.session_switch]),
                        ft.Row([self.fast_switch]),
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
            active_color=self.color_scheme,
            on_change=lambda e: self.switches_on_change(e, self.mobile_search_switch)
        )
        self.farmer_settings = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ListTile(
                            title=ft.Text("Farmer settings"),
                            leading=ft.Icon(ft.icons.SETTINGS_APPLICATIONS),
                        ),
                        ft.Row([self.daily_quests_switch]),
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
                    )
                ]
            )
        )
    
    def set_initial_values(self):
        # user-agents
        if not self.page.client_storage.contains_key("MRFarmer.pc_user_agent"):
            self.pc_user_agent_field.value = PC_USER_AGENT
        else:
            self.pc_user_agent_field.value = self.page.client_storage.get("MRFarmer.pc_user_agent")
        if not self.page.client_storage.contains_key("MRFarmer.mobile_user_agent"):
            self.mobile_user_agent_field.value = MOBILE_USER_AGENT
        else:
            self.mobile_user_agent_field.value = self.page.client_storage.get("MRFarmer.mobile_user_agent")
        # global settings
        self.headless_switch.value = self.page.client_storage.get("MRFarmer.headless")
        self.fast_switch.value = self.page.client_storage.get("MRFarmer.fast")
        self.session_switch.value = self.page.client_storage.get("MRFarmer.session")
        self.save_errors_switch.value = self.page.client_storage.get("MRFarmer.save_errors")
        self.shutdown_switch.value = self.page.client_storage.get("MRFarmer.shutdown")
        # farmer settings
        self.daily_quests_switch.value = (
            self.page.client_storage.get("MRFarmer.daily_quests") 
            if self.page.client_storage.contains_key("MRFarmer.daily_quests") 
            else True
        )
        self.punch_cards_switch.value = (
            self.page.client_storage.get("MRFarmer.punch_cards") 
            if self.page.client_storage.contains_key("MRFarmer.punch_cards") 
            else True
        )
        self.more_activities_switch.value = (
            self.page.client_storage.get("MRFarmer.more_activities") 
            if self.page.client_storage.contains_key("MRFarmer.more_activities") 
            else True
        )
        self.pc_search_switch.value = (
            self.page.client_storage.get("MRFarmer.pc_search") 
            if self.page.client_storage.contains_key("MRFarmer.pc_search") 
            else True
        )
        self.mobile_search_switch.value = (
            self.page.client_storage.get("MRFarmer.mobile_search") 
            if self.page.client_storage.contains_key("MRFarmer.mobile_search") 
            else True
        )
        self.page.update()
    
    def clear_pc_user_agent_field(self, e):
        self.pc_user_agent_field.value = None
        self.page.update()
    
    def clear_mobile_user_agent_field(self, e):
        self.mobile_user_agent_field.value = None
        self.page.update()

    def save_user_agents(self, e):
        if self.pc_user_agent_field.value != "":
            self.page.client_storage.set("MRFarmer.pc_user_agent", self.pc_user_agent_field.value)
        if self.mobile_user_agent_field.value != "":    
            self.page.client_storage.set("MRFarmer.mobile_user_agent", self.mobile_user_agent_field.value)
            
    def delete_user_agents(self, e):
        self.page.client_storage.remove("MRFarmer.pc_user_agent")
        self.pc_user_agent_field.value = None
        self.page.client_storage.remove("MRFarmer.mobile_user_agent")
        self.mobile_user_agent_field.value = None
        self.page.update()
    
    def switches_on_change(self, e, control: ft.Switch):
        name = control.label.lower().replace(" ", "_")
        self.page.client_storage.set(f"MRFarmer.{name}", control.value)
        
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
        # farmer settings
        self.daily_quests_switch.active_color = color_scheme
        self.punch_cards_switch.active_color = color_scheme
        self.more_activities_switch.active_color = color_scheme
        self.pc_search_switch.active_color = color_scheme
        self.mobile_search_switch.active_color = color_scheme
    