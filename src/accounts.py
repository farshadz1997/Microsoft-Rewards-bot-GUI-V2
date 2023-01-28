import flet as ft
from datetime import date, time
from itertools import zip_longest


class AccountsCardCreator(ft.UserControl):
    def __init__(self, accounts: dict):
        self.accounts = accounts
        self.divided_accounts_lists = list(zip_longest(*[iter(self.accounts)]*2, fillvalue=None))
        self.number_of_rows = len(self.divided_accounts_lists)
        super().__init__()
        
    def build(self):
        list_of_cards = []
        column = ft.Column(expand=12)
        for accounts in self.divided_accounts_lists:
            cards = [SingleAccountCardCreator(account).card for account in accounts if account is not None]
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
    def __init__(self, account: dict):
        self.account = account
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
            ctrls = AccountsCardCreator(self.page.session.get("MRFarmer.accounts"))
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
        