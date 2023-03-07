import flet as ft
import webbrowser


__VERSION__ = "1.0.0"
__AUTHOR__ = "Farshad"
__ID__ = "Farshadz1997"
__CONTENT__ = f"""
**Version: {__VERSION__}**

**Author: [{__AUTHOR__} ({__ID__})](https://github.com/farshadz1997)**

**Repository: [GitHub](https://github.com/farshadz1997/Microsoft-Rewards-bot-GUI-V2), [GitLab](https://gitlab.com/farshadzargary1997/Microsoft-Rewards-bot-GUI-V2)**

**Credits: [Charles Bel](https://github.com/charlesbel)**, the creator of main script that the modified version being used in my bot.

### **Use it at your own risk, Microsoft may ban your account!**

### Your support will be much appreciated

  - **BTC (BTC network):** bc1qn52jx934nd54vhcv6x5xxsrc7z2qvwf6atcut3
  - **ETH (ERC20):** 0x2486D75EC2675833569b85d77b01C2c37097ECc2
  - **LTC:** ltc1qc03mnemxewn6z0chfc20yw4samucg6kczmwuf8
  - **USDT (ERC20):** 0x2486D75EC2675833569b85d77b01C2c37097ECc2
"""

__LICENSE__ = """MIT License

Copyright (c) 2023 Farshad Zargari

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


class About(ft.UserControl):
    def __init__(self, parent, page: ft.Page):
        from .app_layout import UserInterface
        super().__init__()
        self.parent: UserInterface = parent
        self.page = page
        self.ui()
        self.page.update()
    
    def ui(self):
        self.title = ft.Row(
            controls=[
                ft.Text(
                    value="About",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    text_align="center",
                    expand=True,
                ),
            ]
        )
        self.content = ft.Markdown(
            value=__CONTENT__,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            on_tap_link=lambda e: webbrowser.open(e.data)
        )
        self.license_label = ft.Row([ft.Text("LICENSE", size=18, weight=ft.FontWeight.BOLD, text_align="center", expand=True)])
        self.license = ft.Markdown(__LICENSE__)
        self.about_card = ft.Card(
            expand=True,
            content=ft.Container(
                margin=ft.margin.all(15),
                alignment=ft.alignment.top_center,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.START,
                    controls=[
                        self.title,
                        ft.Divider(),
                        self.content,
                        self.license_label,
                        self.license
                    ]
                )
            )
        )
    
    def build(self):
        return ft.Container(
            margin=ft.margin.all(25),
            alignment=ft.alignment.top_center,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment="stretch",
                controls=[
                    ft.Row(
                        controls=[self.about_card],
                        alignment="center"
                    ),
                ],
            ),
        )
        