import flet as ft
from datetime import date, time
from itertools import zip_longest


class AccountsCardCreator(ft.UserControl):
    def __init__(self, accounts: dict, page: ft.Page):
        super().__init__()
        self.accounts = accounts
        self.page = page
        self.divided_accounts_lists = list(zip_longest(*[iter(self.accounts)]*2, fillvalue=None))
        self.number_of_rows = len(self.divided_accounts_lists)
        
    def build(self):
        list_of_cards = []
        column = ft.Column(expand=12)
        for accounts in self.divided_accounts_lists:
            cards = [SingleAccountCardCreator(account, self.page).card for account in accounts if account is not None]
            list_of_cards.append(cards)
            
        for _list in list_of_cards:
            row = ft.Row(controls=_list)
            column.controls.append(row)
        self.container = ft.Container(
            expand=True,
            content=column
        )
        return self.container


class SingleAccountCardCreator:
    def __init__(self, account: dict, page: ft.Page):
        self.account = account
        self.page = page
        self.card_creator()
        
    def card_creator(self):
        self.card = ft.Card(
            expand=4,
            content=ft.Container(
                margin=ft.margin.all(15),
                content=ft.Column(
                    expand=3,
                    controls=[
                        ft.ListTile(
                            title=ft.Text(self.account["username"]),
                            leading=ft.Icon(ft.icons.ACCOUNT_CIRCLE),
                            subtitle=ft.Text(self.account["log"]["Last check"]),
                            trailing=ft.PopupMenuButton(
                                icon=ft.icons.MORE_VERT,
                                items=[
                                    ft.PopupMenuItem(
                                        text="Copy Email",
                                        icon=ft.icons.COPY,
                                        on_click=lambda _: self.page.set_clipboard(self.account["username"])
                                    ),
                                    ft.PopupMenuItem(
                                        text="Copy password",
                                        icon=ft.icons.COPY,
                                        on_click=lambda _: self.page.set_clipboard(self.account["password"])
                                    ),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(text="Edit account", icon=ft.icons.EDIT_ATTRIBUTES),
                                    ft.PopupMenuItem(text="Delete account", icon=ft.icons.DELETE),
                                ]
                            )
                        ),
                        ft.Row([ft.Text(f'Earned points: {0}'.format(self.account.get("log").get("Today's points")))]),
                        ft.Row([ft.Text(f"Total points: {self.account.get('log').get('Points')}")]),
                    ]
                )
            )
        )
        
    def is_farmed(self):
        if (
            self.account["log"]["Last check"] == str(date.today()) and
            list(self.account["log"].keys()) == ["Last check", "Today's points", "Points"]
        ):
            return True
        return False
    

class Accounts(ft.UserControl):
    def __init__(self, parent, page: ft.Page):
        super().__init__()
        self.page = page
        self.parent = parent
        self.color_scheme = parent.color_scheme
        self.ui()
        self.set_initial_values()
        self.page.update()
        
    def ui(self):
        self.title = ft.Row(
            controls=[
                ft.Text(
                    value="Accounts",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    text_align="center",
                    expand=6,
                ),
            ]
        )
        self.accounts_card = ft.Card(expand=12)
        
        # add button
        self.page.floating_action_button = ft.FloatingActionButton(
            text="Add account",
            icon=ft.icons.ADD,
            on_click=self.open_add_account_dialog,
            visible=True if self.page.route == "/accounts" else False
        )
        
        # add account page fields
        self.email_field = ft.TextField(
            label="Email",
            border_color=self.color_scheme,
            text_size=12,
            multiline=False,
            dense=True,
            error_style=ft.TextStyle(color="red"),
            on_change=lambda _: self.check_field(self.email_field)
        )
        self.password_field = ft.TextField(
            label="Password",
            password=True,
            can_reveal_password=True,
            border_color=self.color_scheme,
            text_size=12,
            multiline=False,
            dense=True,
            error_style=ft.TextStyle(color="red"),
            on_change=lambda _: self.check_field(self.password_field)
        )
        self.proxy_field = ft.TextField(
            label="Proxy address (Optional)",
            tooltip="The proxy you entered here will be used when farming the account.",
            border_color=self.color_scheme,
            text_size=12,
            disabled=True,
            multiline=False,
            dense=True,
            error_style=ft.TextStyle(color="red"),
            on_change=lambda _: self.check_field(self.proxy_field)
        )
        self.proxy_check_box = ft.Checkbox(
            label="Use proxy",
            scale=0.95,
            fill_color=self.color_scheme,
            on_change=lambda _: self.field_status_update(
                self.proxy_check_box.value,
                self.proxy_field
            )
        )
        self.mobile_user_agent_field = ft.TextField(
            label="Mobile user agent (Optional)",
            tooltip="This user agent will be used when farming the account for mobile device.",
            border_color=self.color_scheme,
            text_size=12,
            disabled=True,
            dense=True,
            multiline=False,
            error_style=ft.TextStyle(color="red"),
            on_change=lambda _: self.check_field(self.mobile_user_agent_field)
        )
        self.mobile_user_agent_check_box = ft.Checkbox(
            label="Use mobile user agent",
            scale=0.95,
            fill_color=self.color_scheme,
            on_change=lambda _: self.field_status_update(
                self.mobile_user_agent_check_box.value,
                self.mobile_user_agent_field
            )
        )
        
        # add account dialog
        self.add_account_dialog = ft.AlertDialog(
            title=ft.Text("Add account", text_align="center"),
            modal=True,
            content_padding=15,
            content=ft.Container(
                width=400,
                content=ft.Column(
                    height=350,
                    controls=[
                        ft.Row(
                            wrap=True,
                            controls=[
                                self.email_field,
                                self.password_field,
                                ft.Divider(),
                                self.proxy_field,
                                self.proxy_check_box,
                                self.mobile_user_agent_field,
                                self.mobile_user_agent_check_box
                            ]
                        )
                    ]
                ),
            ),
            actions=[
                ft.ElevatedButton("Add", on_click=self.add_account),
                ft.ElevatedButton("Cancel", on_click=self.close_dialog),
            ],
            actions_alignment="end",
            on_dismiss=self.clean_fields
        )
    
    def build(self):
        return ft.Container(
            margin=ft.margin.all(25),
            alignment=ft.alignment.top_center,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment="stretch",
                controls=[
                    ft.Row([self.accounts_card]),
                ],
            ),
        )
        
    def set_initial_values(self):
        self.sync_accounts()
    
    def sync_accounts(self):
        if self.page.session.contains_key("MRFarmer.accounts"):
            ctrls = AccountsCardCreator(self.page.session.get("MRFarmer.accounts"), self.page)
            self.accounts_card.content = ft.Container(
                alignment=ft.alignment.top_center,
                margin=ft.margin.all(15),
                content=ft.Column(
                    controls=[
                        self.title,
                        ft.Divider(),
                        ctrls
                    ]
                )
            )
            if ctrls.number_of_rows < 3:
                self.accounts_card.content.height = 600
            else:
                pass
        else:
            self.accounts_card.content = ft.Container(
                height=600,
                alignment=ft.alignment.top_center,
                margin=ft.margin.all(15),
                content=ft.Column(
                    controls=[
                        self.title,
                        ft.Divider(),
                        ft.Row(
                            expand=6,
                            alignment="center",
                            controls=[ft.Text("No accounts file added yet", text_align="center")]
                        )
                    ]
                )
            )
        self.page.update()
        
    def remove_accounts(self):
        self.accounts_card.content = ft.Container(
            alignment=ft.alignment.top_center,
            margin=ft.margin.all(15),
            height=600,
            content=ft.Column(
                controls=[
                    self.title,
                    ft.Divider(),
                    ft.Row(
                        expand=6,
                        alignment="center",
                        controls=[ft.Text("No accounts file added yet", text_align="center")]
                    )
                ]
            )
        )
    
    def open_add_account_dialog(self, e):
        if not self.page.session.contains_key("MRFarmer.accounts"):
            self.parent.display_error("Accounts file not exist", "Open accounts first then try to add account")
            return
        self.page.dialog = self.add_account_dialog
        self.add_account_dialog.open = True
        self.page.update()
        
    def close_dialog(self, e):
        self.add_account_dialog.open = False
        self.clean_fields(e)
        self.page.update()
        
    def field_status_update(self, value: bool, control: ft.TextField):
        """Used to change disable attribute of proxy and mobile user agent TextField"""
        control.disabled = not value
        if not value and control.error_text:
            control.error_text = None
        self.page.update()
        
    def are_fields_valid(self):
        is_valid = True
        error_count = 0
        if not self.email_field.value:
            self.email_field.error_text = "Email is required"
            error_count += 1
            is_valid = False
        if not self.password_field.value:
            self.password_field.error_text = "Password is required"
            error_count += 1
            is_valid = False
        if self.proxy_check_box.value and not self.proxy_field.value:
            self.proxy_field.error_text = "Proxy is required"
            error_count += 1
            is_valid = False
        if self.mobile_user_agent_check_box.value and not self.mobile_user_agent_field.value:
            self.mobile_user_agent_field.error_text = "Mobile user agent is required"
            error_count += 1
            is_valid = False
        dialog_height = 350 + (error_count * 25)
        self.add_account_dialog.content.content.height = dialog_height
        if not is_valid:
            self.page.update()
        return is_valid
    
    def check_field(self, control: ft.TextField):
        if control.value and control.error_text:
            control.error_text = None
            self.add_account_dialog.content.content.height -= 25
            self.page.update()
    
    def add_account(self, e):
        if self.are_fields_valid():
            accounts: list = self.page.session.get("MRFarmer.accounts")
            account = {
                "username": self.email_field.value,
                "password": self.password_field.value,
                "log": {
                    "Last check": "Not farmed yet",
                    "Today's points": 0,
                    "Points": 0,
                    "Daily": False,
                    "Punch cards": False,
                    "More promotions": False,
                    "PC searches": False,
                    "Mobile searches": False
                }
            }
            if self.proxy_check_box.value:
                account["proxy"] = self.proxy_field.value
            if self.mobile_user_agent_check_box.value:
                account["mobile_user_agent"] = self.mobile_user_agent_field.value
            accounts.append(account)
            self.page.session.set("MRFarmer.accounts", accounts)
            self.sync_accounts()
            self.parent.update_accounts_file()
            self.close_dialog(e)
    
    def clean_fields(self, e):
        fields = [
            self.email_field,
            self.password_field,
            self.proxy_field,
            self.mobile_user_agent_field
        ]
        checkboxes = [self.proxy_check_box, self.mobile_user_agent_check_box]
        self.proxy_field.disabled = True
        self.mobile_user_agent_field.disabled = True
        for field in fields:
            field.value = None
            field.error_text = None
        for checkbox in checkboxes:
            checkbox.value = False
        self.add_account_dialog.content.content.height = 350
        self.page.update()
        