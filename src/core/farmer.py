import json
import os
import platform
import random
import subprocess
import time
import urllib.parse
from urllib3.exceptions import MaxRetryError, NewConnectionError
from pathlib import Path
from datetime import date, datetime, timedelta
from notifiers import get_notifier
import copy
import flet as ft
from typing import List, Union
from .exceptions import *

import ipapi
import requests
from func_timeout import FunctionTimedOut, func_set_timeout
from random_word import RandomWords
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoAlertPresentException,
                                        NoSuchElementException,
                                        SessionNotCreatedException,
                                        TimeoutException,
                                        UnexpectedAlertPresentException,
                                        InvalidSessionIdException,
                                        JavascriptException,
                                        ElementNotVisibleException,
                                        WebDriverException)
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


PC_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.46'
MOBILE_USER_AGENT = 'Mozilla/5.0 (Linux; Android 12; SM-N9750) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36 EdgA/110.0.1587.41'


class Farmer:
    base_url = "https://rewards.microsoft.com"
    
    def __init__(self, page: ft.Page, parent, home_page, accounts_page):
        from ..ui.app_layout import UserInterface
        from ..ui.home import Home
        from ..ui.accounts import Accounts
        
        self.page = page
        self.parent: UserInterface = parent
        self.home_page: Home = home_page
        self.accounts_page: Accounts = accounts_page
        self.accounts: list = self.page.session.get("MRFarmer.accounts")
        self.accounts_path = Path(self.page.client_storage.get("MRFarmer.accounts_path"))
        self.browser: WebDriver = None
        self.points_counter: int = 0
        self.finished_accounts: list = []
        self.locked_accounts: list = []
        self.suspended_accounts: list = []
        self.current_account: dict = None
        self.browser: WebDriver = None
        self.starting_points: int = None
        self.point_counter: int = 0
        self.account_index: int = None
        self.lang, self.geo, self.tz = self.get_ccode_lang_and_offset()
    
    def create_message(self):
        """Create message from logs to send to Telegram"""
        today = date.today().strftime("%d/%m/%Y")
        total_earned = 0
        total_overall = 0
        message = f'📅 Daily report {today}\n\n'
        for index, account in enumerate(self.accounts, 1):
            redeem_message = None
            if account["log"].get("Redeem goal title", None):
                redeem_title = account["log"].get("Redeem goal title", None)
                redeem_price = account["log"].get("Redeem goal price")
                redeem_count = account["log"]["Points"] // redeem_price
                if redeem_count > 1:
                    redeem_message = f"🎁 Ready to redeem: {redeem_title} for {redeem_price} points ({redeem_count}x)\n\n"
                else:
                    redeem_message = f"🎁 Ready to redeem: {redeem_title} for {redeem_price} points\n\n"
            if account["log"]['Last check'] == str(date.today()):
                status = '✅ Farmed'
                new_points = account["log"]["Today's points"]
                total_earned += new_points
                total_points = account["log"]["Points"]
                total_overall += total_points
                message += f"{index}. {account['username']}\n📝 Status: {status}\n⭐️ Earned points: {new_points}\n🏅 Total points: {total_points}\n"
                if redeem_message:
                    message += redeem_message
                else:
                    message += "\n"
            elif account["log"]['Last check'] == 'Your account has been suspended':
                status = '❌ Suspended'
                message += f"{index}. {account['username']}\n📝 Status: {status}\n\n"
            elif account["log"]['Last check'] == 'Your account has been locked':
                status = '⚠️ Locked'
                message += f"{index}. {account['username']}\n📝 Status: {status}\n\n"
            elif account["log"]['Last check'] == 'Unusual activity detected':
                status = '⚠️ Unusual activity detected'
                message += f"{index}. {account['username']}\n📝 Status: {status}\n\n"
            elif account["log"]['Last check'] == 'Unknown error':
                status = '⛔️ Unknown error occurred'
                message += f"{index}. {account['username']}\n📝 Status: {status}\n\n"
            else:
                status = f'Farmed on {account["log"]["Last check"]}'
                new_points = account["log"]["Today's points"]
                total_earned += new_points
                total_points = account["log"]["Points"]
                total_overall += total_points
                message += f"{index}. {account['username']}\n📝 Status: {status}\n⭐️ Earned points: {new_points}\n🏅 Total points: {total_points}\n"
                if redeem_message:
                    message += redeem_message
                else:
                    message += "\n"
        message += f"💵 Total earned points: {total_earned} (${total_earned/1300:0.02f}) (€{total_earned/1500:0.02f})"
        message += f"\n💵 Total points overall: {total_overall} (${total_overall/1300:0.02f}) (€{total_overall/1500:0.02f})"
        return message

    def send_report_to_messenger(self, message: str):
        if self.page.client_storage.get("MRFarmer.send_to_telegram"):
            self.send_to_telegram(message)
        if self.page.client_storage.get("MRFarmer.send_to_discord"):
            self.send_to_discord(message)
            
    def send_to_telegram(self, message: str):
        t = get_notifier('telegram')
        token = self.page.client_storage.get("MRFarmer.telegram_token")
        chat_id = self.page.client_storage.get("MRFarmer.telegram_chat_id")
        t.notify(message=message, token=token, chat_id=chat_id)
        
    def send_to_discord(self, message: str):
        webhook_url = self.page.client_storage.get("MRFarmer.discord_webhook_url")
        if len(message) > 2000:
            messages = [message[i:i+2000] for i in range(0, len(message), 2000)]
            for ms in messages:
                content = {"username": "⭐️ Microsoft Rewards Bot ⭐️", "content": ms}
                response = requests.post(webhook_url, json=content)
        else:
            content = {"username": "⭐️ Microsoft Rewards Bot ⭐️", "content": message}
            response = requests.post(webhook_url, json=content) 
        if response.status_code == 204:
            pass
        else:
            self.parent.open_snack_bar(f"Couldn't send report message to your Discord with status code {response.status_code}")
            
    def check_internet_connection(self):
        system = platform.system()
        while True:
            try:
                if not self.parent.is_farmer_running:
                    return False
                if system == "Windows":
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.check_output(["ping", "-n", "1", "8.8.8.8"], timeout=5, startupinfo=si)
                elif system == "Linux":
                    subprocess.check_output(["ping", "-c", "1", "8.8.8.8"], timeout=5)
                self.home_page.update_section("-")
                self.home_page.update_detail("-")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                self.home_page.update_section("No internet connection...")
                self.home_page.update_detail("Checking...")
                time.sleep(1)
    
    def get_or_create_logs(self):
        """Read logs and check whether account farmed or not"""
        # check that if any of accounts has farmed today or not.
        for account in self.accounts:
            if account["log"]["Last check"] == str(date.today()) and list(account["log"].keys()) == [
                "Last check",
                "Today's points",
                "Points"
            ]:
                self.finished_accounts.append(account["username"])
            elif account["log"]["Last check"] == "Your account has been suspended":
                self.suspended_accounts.append(account["username"])
            elif account["log"]["Last check"] == str(date.today()) and list(account["log"].keys()) == [
                "Last check", 
                "Today's points", 
                "Points",
                "Daily",
                "Punch cards",
                "More promotions",
                "MSN shopping game",
                "PC searches",
                "Mobile searches"
            ]:
                if not self.does_account_need_farm(account):
                    self.current_account = account
                    self.account_index = self.accounts.index(account)
                    self.clean_logs()
                    self.finished_accounts.append(account["username"])
                    self.current_account = None
                else:
                    continue
            else:
                account["log"]["Daily"] = False
                account["log"]["Punch cards"] = False
                account["log"]["More promotions"] = False
                account["log"]["MSN shopping game"] = False
                account["log"]["PC searches"] = False 
                account["log"]["Mobile searches"] = False
            if not isinstance(account["log"]["Points"], int):
                account["log"]["Points"] = 0
        self.update_accounts()
        self.home_page.update_overall_infos()
        
    def update_accounts(self):
        """Update logs with new data"""
        accounts = copy.deepcopy(self.accounts)
        for account in accounts:
            account["log"].pop("Redeem goal title", None)
            account["log"].pop("Redeem goal price", None)
        self.page.session.set("MRFarmer.accounts", accounts)
        self.parent.update_accounts_file()
        
    def clean_logs(self):
        """Delete Daily, Punch cards, More promotions, PC searches and Mobile searches from logs"""
        self.accounts[self.account_index]["log"].pop("Daily", None)
        self.accounts[self.account_index]["log"].pop("Punch cards", None)
        self.accounts[self.account_index]["log"].pop("More promotions", None)
        self.accounts[self.account_index]["log"].pop("MSN shopping game", None)
        self.accounts[self.account_index]["log"].pop("PC searches", None)
        self.accounts[self.account_index]["log"].pop("Mobile searches", None)
    
    def is_pc_need(self, account: dict) -> bool:
        """Check if browser for PC is needed or not based on farm options and account status"""
        if self.page.client_storage.get("MRFarmer.daily_quests") and account["log"]["Daily"] == False:
            return True
        elif self.page.client_storage.get("MRFarmer.punch_cards") and account["log"]["Punch cards"] == False:
            return True
        elif self.page.client_storage.get("MRFarmer.more_activities") and account["log"]["More promotions"] == False:
            return True
        elif self.page.client_storage.get("MRFarmer.msn_shopping_game") and account["log"]["MSN shopping game"] == False:
            return True
        elif self.page.client_storage.get("MRFarmer.pc_search") and account["log"]["PC searches"] == False:
            return True
        else:
            return False
    
    def does_account_need_farm(self, account: dict):
        """Check that does the account need to be farmed based on logs and options"""
        conditions = []
        if self.page.client_storage.get("MRFarmer.daily_quests") and not account["log"]["Daily"]:
            conditions.append(True)
        if self.page.client_storage.get("MRFarmer.punch_cards") and not account["log"]["Punch cards"]:
            conditions.append(True)
        if self.page.client_storage.get("MRFarmer.more_activities") and not account["log"]["More promotions"]:
            conditions.append(True)
        if self.page.client_storage.get("MRFarmer.msn_shopping_game") and not account["log"]["MSN shopping game"]:
            conditions.append(True)
        if self.page.client_storage.get("MRFarmer.pc_search") and not account["log"]["PC searches"]:
            conditions.append(True)
        if self.page.client_storage.get("MRFarmer.mobile_search") and not account["log"]["Mobile searches"]:
            conditions.append(True)
        if any(conditions):
            return True
        else:
            return False
    
    def is_element_exists(self, _by: By, element: str) -> bool:
        '''Returns True if given element exists else False'''
        try:
            self.browser.find_element(_by, element)
        except NoSuchElementException:
            return False
        return True
    
    def find_between(self, s: str, first: str, last: str) -> str:
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""
    
    def is_proxy_working(self, proxy: str):
        '''Check if proxy is working or not'''
        try:
            requests.get("https://www.google.com/", proxies={"https": proxy}, timeout=5)
            return True
        except:
            return False
    
    @staticmethod
    def account_browser(page: ft.Page, account: dict, accounts_page) -> WebDriver:
        def create_browser():
            if page.client_storage.get("MRFarmer.edge_webdriver"):
                options = EdgeOptions()
            else:
                options = ChromeOptions()
            accounts_path = Path(page.client_storage.get("MRFarmer.accounts_path"))
            options.add_argument(f'--user-data-dir={accounts_path.parent}/Profiles/{account["username"]}/PC')
            options.add_argument("user-agent=" + page.client_storage.get("MRFarmer.pc_user_agent"))
            options.add_argument('lang=en')
            options.add_argument('--disable-blink-features=AutomationControlled')
            prefs = {
                "profile.default_content_setting_values.geolocation": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "webrtc.ip_handling_policy": "disable_non_proxied_udp",
                "webrtc.multiple_routes_enabled": False,
                "webrtc.nonproxied_udp_enabled" : False,
                "detach": True
            }
            options.add_experimental_option("prefs", prefs)
            options.add_experimental_option("useAutomationExtension", False)
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            if page.client_storage.get("MRFarmer.headless"):
                options.add_argument("--headless")
            if page.client_storage.get("MRFarmer.use_proxy") and account.get("proxy", False):
                options.add_argument(f'--proxy-server={account["proxy"]}')
            options.add_argument('log-level=3')
            options.add_argument("--start-maximized")
            if page.client_storage.get("MRFarmer.edge_webdriver"):
                browser_service = EdgeService()
            else:
                browser_service = ChromeService()
            if platform.system() == 'Linux':
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
            if platform.system() == 'Windows':
                browser_service.creationflags = subprocess.CREATE_NO_WINDOW
            if page.client_storage.get("MRFarmer.edge_webdriver"):
                browser = webdriver.Edge(options=options, service=browser_service)
            else:
                browser = webdriver.Chrome(options=options, service=browser_service)
            return browser
        browser = create_browser()
        while accounts_page.is_browser_running_status() and isinstance(browser, WebDriver):
            time.sleep(1)
            continue
        else:
            if isinstance(browser, WebDriver):
                browser.quit()
            
    def browser_setup(self, isMobile: bool = False, user_agent = PC_USER_AGENT):
        # Create Chrome browser
        if self.page.client_storage.get("MRFarmer.edge_webdriver"):
            options = EdgeOptions()
        else:
            options = ChromeOptions()
        if self.page.client_storage.get("MRFarmer.session"):
            if not isMobile:
                options.add_argument(f'--user-data-dir={self.accounts_path.parent}/Profiles/{self.current_account["username"]}/PC')
            else:
                options.add_argument(f'--user-data-dir={self.accounts_path.parent}/Profiles/{self.current_account["username"]}/Mobile')
        options.add_argument("user-agent=" + user_agent)
        options.add_argument('lang=' + self.lang.split("-")[0])
        options.add_argument('--disable-blink-features=AutomationControlled')
        prefs = {"profile.default_content_setting_values.geolocation": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "webrtc.ip_handling_policy": "disable_non_proxied_udp",
                "webrtc.multiple_routes_enabled": False,
                "webrtc.nonproxied_udp_enabled" : False}
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        if self.page.client_storage.get("MRFarmer.headless"):
            options.add_argument("--headless")
        if self.page.client_storage.get("MRFarmer.use_proxy") and self.current_account.get("proxy", False):
            if self.is_proxy_working(self.current_account["proxy"]):
                options.add_argument(f'--proxy-server={self.current_account["proxy"]}')
                self.home_page.update_proxy(self.current_account["proxy"])
            else:
                self.home_page.update_proxy(f'{self.current_account["proxy"]} not working')
        options.add_argument('log-level=3')
        options.add_argument("--start-maximized")
        if self.page.client_storage.get("MRFarmer.edge_webdriver"):
            browser_service = EdgeService()
        else:
            browser_service = ChromeService()
        if platform.system() == 'Linux':
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        if platform.system() == 'Windows':
            browser_service.creationflags = subprocess.CREATE_NO_WINDOW
        if self.page.client_storage.get("MRFarmer.edge_webdriver"):
            self.browser = webdriver.Edge(options=options, service=browser_service)
        else:
            self.browser = webdriver.Chrome(options=options, service=browser_service)
        return self.browser
    
    def login(self, email: str, pwd: str, isMobile: bool = False):
        """Login into  Microsoft account"""
        login_message = "Logging in..." if not isMobile else "Logging in mobile..."
        self.home_page.update_section(login_message)
        # Close welcome tab for new sessions
        if self.page.client_storage.get("MRFarmer.session"):
            self.close_welcome_tab()
        # Access to bing.com
        self.browser.get('https://login.live.com/')
        # Check if account is already logged in
        if self.page.client_storage.get("MRFarmer.session"):
            if self.browser.title == "":
                time.sleep(10)
                wait = WebDriverWait(self.browser, 10)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                wait.until(EC.presence_of_all_elements_located)
                wait.until(EC.title_contains(""))
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "html[lang]")))
                wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            if self.browser.title == "We're updating our terms" or self.is_element_exists(By.ID, 'iAccrualForm'):
                time.sleep(2)
                self.browser.find_element(By.ID, 'iNext').click()
                time.sleep(5)
            self.answer_to_security_info_update()
            # Click No thanks on break free from password question
            if self.is_element_exists(By.ID, "setupAppDesc"):
                time.sleep(2)
                self.browser.find_element(By.ID, "iCancel").click()
                time.sleep(5)
            if self.browser.title == 'Microsoft account | Home' or self.is_element_exists(By.ID, 'navs_container'):
                self.home_page.update_detail("Microsoft Rewards...")
                self.rewards_login(isMobile)
                self.home_page.update_detail("Bing...")
                self.check_bing_login(isMobile)
                return
            elif self.browser.title == 'Your account has been temporarily suspended':
                raise AccountLockedException('Your account has been locked !')
            elif self.is_element_exists(By.ID, 'mectrl_headerPicture') or 'Sign In or Create' in self.browser.title:
                self.browser.find_element(By.ID, 'mectrl_headerPicture').click()
                self.wait_until_visible(By.ID, 'i0118', 10)
                if self.is_element_exists(By.ID, 'i0118'):
                    self.browser.find_element(By.ID, "i0118").send_keys(pwd)
                    time.sleep(2)
                    self.browser.find_element(By.ID, 'idSIButton9').click()
                    time.sleep(5)
                    self.home_page.update_section("Logged in")
                    self.home_page.update_detail("Microsoft Rewards...")
                    self.rewards_login(isMobile)
                    self.home_page.update_detail("Bing...")
                    self.check_bing_login(isMobile)
                    return None
        # Wait complete loading
        self.wait_until_visible(By.ID, 'loginHeader', 10)
        # Enter email
        self.browser.find_element(By.NAME, "loginfmt").send_keys(email)
        # Click next
        self.browser.find_element(By.ID, 'idSIButton9').click()
        # Wait 2 seconds
        time.sleep(5 if not self.page.client_storage.get("MRFarmer.fast") else 2)
        # Wait complete loading
        self.wait_until_visible(By.ID, 'loginHeader', 10)
        # Enter password
        self.browser.find_element(By.ID, "i0118").send_keys(pwd)
        # Click next
        self.browser.find_element(By.ID, 'idSIButton9').click()
        # Wait 5 seconds
        time.sleep(5)
        try:
            if self.browser.title == "We're updating our terms" or self.is_element_exists(By.ID, 'iAccrualForm'):
                time.sleep(2)
                self.browser.find_element(By.ID, 'iNext').click()
                time.sleep(5)
            self.answer_to_security_info_update()
            if self.page.client_storage.get("MRFarmer.session"):
                # Click Yes to stay signed in.
                self.browser.find_element(By.ID, 'idSIButton9').click()
            else:
                # Click No.
                self.browser.find_element(By.ID, 'idBtn_Back').click()
            self.answer_to_security_info_update()
            # Click No thanks on break free from password question
            if self.is_element_exists(By.ID, "setupAppDesc"):
                time.sleep(2)
                self.browser.find_element(By.ID, "iCancel").click()
                time.sleep(5)
        except NoSuchElementException:
            # Check for if account has been locked.
            if self.browser.title == "Your account has been temporarily suspended" or self.is_element_exists(By.CLASS_NAME, "serviceAbusePageContainer  PageContainer"):
                raise AccountLockedException("Your account has been locked !")
            elif self.browser.title == "Help us protect your account":
                raise UnusualActivityException("Unusual activity detected")
            else:
                raise UnhandledException('Unknown error !')
        # Wait 5 seconds
        time.sleep(5)
        # Click Security Check
        try:
            self.browser.find_element(By.ID, 'iLandingViewAction').click()
        except (NoSuchElementException, ElementNotInteractableException) as e:
            pass
        # Wait complete loading
        try:
            self.wait_until_visible(By.ID, 'KmsiCheckboxField', 10)
        except (TimeoutException) as e:
            pass
        # Click next
        try:
            self.browser.find_element(By.ID, 'idSIButton9').click()
            # Wait 5 seconds
            time.sleep(5)
        except (NoSuchElementException, ElementNotInteractableException) as e:
            pass
        # Check Microsoft Rewards
        self.home_page.update_detail("Microsoft Rewards...")
        self.rewards_login(isMobile)
        # Check Login
        self.home_page.update_detail("Bing...")
        self.check_bing_login(isMobile)
    
    def answer_to_security_info_update(self):
        """Clicks on looks good if it asks for security info update"""
        if self.browser.title == 'Is your security info still accurate?' or self.is_element_exists(By.ID, 'iLooksGood'):
            time.sleep(2)
            self.browser.find_element(By.ID, 'iLooksGood').click()
            time.sleep(5)
            
    def rewards_login(self, isMobile: bool = False):
        """Login into Microsoft rewards and check account"""
        self.browser.get(self.base_url)
        self.answer_to_security_info_update()
        try:
            time.sleep(10 if not self.page.client_storage.get("MRFarmer.fast") else 5)
            # click on sign up button if needed
            if self.is_element_exists(By.ID, "start-earning-rewards-link"):
                self.browser.find_element(By.ID, "start-earning-rewards-link").click()
                time.sleep(5)
                self.browser.refresh()
                time.sleep(5)
        except:
            pass
        time.sleep(10 if not self.page.client_storage.get("MRFarmer.fast") else 5)
        # Check for ErrorMessage in Microsoft rewards page
        try:
            self.browser.find_element(By.ID, 'error').is_displayed()
            if self.browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute('innerHTML') == ' Uh oh, it appears your Microsoft Rewards account has been suspended.':
                raise AccountSuspendedException('Your account has been suspended !')
            elif self.browser.find_element(By.XPATH, '//*[@id="error"]/h1').get_attribute('innerHTML') == 'Microsoft Rewards is not available in this country or region.':
                raise RegionException('Microsoft Rewards is not available in your region !')
        except NoSuchElementException:
            self.answer_to_security_info_update()
            self.wait_until_visible(By.ID, 'app-host', 30)
            points = self.get_account_points()
            self.home_page.update_points_counter(points)
            if isMobile:
                self.remainingSearchesM = self.get_remaining_searches()[1]
                if not self.starting_points:
                    self.starting_points = self.get_account_points()

    def close_welcome_tab(self):
        """close welcome tab if it exists"""
        time.sleep(2)
        if len(self.browser.window_handles) > 1:
            current_window = self.browser.current_window_handle
            for handler in self.browser.window_handles:
                if handler != current_window:
                    self.browser.switch_to.window(handler)
                    time.sleep(0.5)
                    self.browser.close()
            self.browser.switch_to.window(current_window)
    
    @func_set_timeout(300)
    def check_bing_login(self, isMobile: bool = False):
        self.browser.get('https://bing.com/')
        time.sleep(15 if not self.page.client_storage.get("MRFarmer.fast") else 5)
        # try to get points at first if account already logged in
        if self.page.client_storage.get("MRFarmer.session"):
            try:
                if not isMobile:
                    try:
                        self.points_counter = int(self.browser.find_element(By.ID, 'id_rc').get_attribute('innerHTML'))
                    except ValueError:
                        if self.browser.find_element(By.ID, 'id_s').is_displayed():
                            self.browser.find_element(By.ID, 'id_s').click()
                            time.sleep(15)
                            self.check_bing_login(isMobile)
                        time.sleep(2)
                        self.points_counter = int(self.browser.find_element(By.ID, "id_rc").get_attribute("innerHTML").replace(",", ""))
                else:
                    self.browser.find_element(By.ID, 'mHamburger').click()
                    time.sleep(1)
                    self.points_counter = int(self.browser.find_element(By.ID, 'fly_id_rc').get_attribute('innerHTML'))
            except:
                pass
            else:
                self.home_page.update_points_counter(self.points_counter)
                return None
        #Accept Cookies
        try:
            self.browser.find_element(By.ID, 'bnp_btn_accept').click()
        except:
            pass
        if isMobile:
            # close bing app banner
            if self.is_element_exists(By.ID, 'bnp_rich_div'):
                try:
                    self.browser.find_element(By.XPATH, '//*[@id="bnp_bop_close_icon"]/img').click()
                except NoSuchElementException:
                    pass
            try:
                time.sleep(1)
                self.browser.find_element(By.ID, 'mHamburger').click()
            except:
                try:
                    self.browser.find_element(By.ID, 'bnp_btn_accept').click()
                except:
                    pass
                time.sleep(1)
                if self.is_element_exists(By.XPATH, '//*[@id="bnp_ttc_div"]/div[1]/div[2]/span'):
                    self.browser.execute_script("""var element = document.evaluate('/html/body/div[1]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                                            element.remove();""")
                    time.sleep(5)
                time.sleep(1)
                try:
                    self.browser.find_element(By.ID, 'mHamburger').click()
                except:
                    pass
            try:
                time.sleep(1)
                self.browser.find_element(By.ID, 'HBSignIn').click()
                time.sleep(5)
                self.answer_to_security_info_update()
            except:
                pass
            try:
                time.sleep(2)
                self.browser.find_element(By.ID, 'iShowSkip').click()
                time.sleep(3)
            except:
                if str(self.browser.current_url).split('?')[0] == "https://account.live.com/proofs/Add":
                    self.finished_accounts.append(self.current_account["username"])
                    self.accounts[self.account_index]["log"]["Last check"] = "Requires manual check!"
                    self.update_accounts()
                    raise Exception
        time.sleep(5)
        # Refresh page
        self.browser.get('https://bing.com/')
        time.sleep(15 if not self.page.client_storage.get("MRFarmer.fast") else 5)
        #Update Counter
        try:
            if not isMobile:
                try:
                    self.points_counter = int(self.browser.find_element(By.ID, 'id_rc').get_attribute('innerHTML'))
                except:
                    if self.browser.find_element(By.ID, 'id_s').is_displayed():
                        self.browser.find_element(By.ID, 'id_s').click()
                        time.sleep(15)
                        self.check_bing_login(isMobile)
                    time.sleep(5)
                    self.points_counter = int(self.browser.find_element(By.ID, "id_rc").get_attribute("innerHTML").replace(",", ""))
            else:
                try:
                    self.browser.find_element(By.ID, 'mHamburger').click()
                except:
                    try:
                        self.browser.find_element(By.ID, 'bnp_close_link').click()
                        time.sleep(4)
                        self.browser.find_element(By.ID, 'bnp_btn_accept').click()
                    except:
                        pass
                    time.sleep(1)
                    self.browser.find_element(By.ID, 'mHamburger').click()
                time.sleep(1)
                self.points_counter = int(self.browser.find_element(By.ID, 'fly_id_rc').get_attribute('innerHTML'))
        except:
            self.check_bing_login(isMobile)
        else:
            self.home_page.update_points_counter(self.points_counter)
            
    def wait_until_visible(self, by_: By, selector: str, time_to_wait: int = 10):
        WebDriverWait(self.browser, time_to_wait).until(EC.visibility_of_element_located((by_, selector)))

    def wait_until_clickable(self, by_: By, selector: str, time_to_wait: int = 10):
        WebDriverWait(self.browser, time_to_wait).until(EC.element_to_be_clickable((by_, selector)))

    def wait_until_question_refresh(self):
        tries = 0
        refreshCount = 0
        while True:
            try:
                self.browser.find_elements(By.CLASS_NAME, 'rqECredits')[0]
                return True
            except:
                if tries < 10:
                    tries += 1
                    time.sleep(0.5)
                else:
                    if refreshCount < 5:
                        self.browser.refresh()
                        refreshCount += 1
                        tries = 0
                        time.sleep(5)
                    else:
                        return False

    def wait_until_quiz_loads(self):
        tries = 0
        refreshCount = 0
        while True:
            try:
                self.browser.find_element(By.XPATH, '//*[@id="currentQuestionContainer"]')
                return True
            except:
                if tries < 10:
                    tries += 1
                    time.sleep(0.5)
                else:
                    if refreshCount < 5:
                        self.browser.refresh()
                        refreshCount += 1
                        tries = 0
                        time.sleep(5)
                    else:
                        return False

    def get_dashboard_data(self) -> dict:
        dashboard = self.find_between(self.browser.find_element(By.XPATH, '/html/body').get_attribute('innerHTML'), "var dashboard = ", ";\n        appDataModule.constant(\"prefetchedDashboard\", dashboard);")
        dashboard = json.loads(dashboard)
        return dashboard
    
    def get_account_points(self) -> int:
        return self.get_dashboard_data()['userStatus']['availablePoints']
    
    def get_redeem_goal(self):
        user_status = self.get_dashboard_data()["userStatus"]
        return (user_status["redeemGoal"]["title"], user_status["redeemGoal"]["price"])
    
    def get_ccode_lang_and_offset(self) -> tuple:
        try:
            nfo = ipapi.location()
            lang = nfo['languages'].split(',')[0]
            geo = nfo['country']
            tz = str(round(int(nfo['utc_offset']) / 100 * 60))
            return(lang, geo, tz)
        except:
            return('en-US', 'US', '-480')
        
    def get_google_trends(self, numberOfwords: int) -> list:
        search_terms = []
        i = 0
        while len(search_terms) < numberOfwords :
            i += 1
            r = requests.get('https://trends.google.com/trends/api/dailytrends?hl=' + self.lang + '&ed=' + str((date.today() - timedelta(days = i)).strftime('%Y%m%d')) + '&geo=' + self.geo + '&ns=15')
            google_trends = json.loads(r.text[6:])
            for topic in google_trends['default']['trendingSearchesDays'][0]['trendingSearches']:
                search_terms.append(topic['title']['query'].lower())
                for related_topic in topic['relatedQueries']:
                    search_terms.append(related_topic['query'].lower())
            search_terms = list(set(search_terms))
        del search_terms[numberOfwords:(len(search_terms)+1)]
        return search_terms
    
    def get_related_terms(self, word: str) -> list:
        try:
            r = requests.get('https://api.bing.com/osjson.aspx?query=' + word, headers = {'User-agent': PC_USER_AGENT})
            return r.json()[1]
        except:
            return []
        
    def reset_tabs(self):
        try:
            curr = self.browser.current_window_handle

            for handle in self.browser.window_handles:
                if handle != curr:
                    self.browser.switch_to.window(handle)
                    time.sleep(0.5)
                    self.browser.close()
                    time.sleep(0.5)

            self.browser.switch_to.window(curr)
            time.sleep(0.5)
            self.browser.get(self.base_url)
        except:
            self.browser.get(self.base_url)
        finally:
            self.wait_until_visible(By.ID, 'app-host', 30)
            
    def get_answer_code(self, key: str, string: str) -> str:
        """Get answer code for this or that quiz"""
        t = 0
        for i in range(len(string)):
            t += ord(string[i])
        t += int(key[-2:], 16)
        return str(t)
    
    def bing_searches(self, numberOfSearches: int, isMobile: bool = False):
        if not isMobile:
            self.home_page.update_section("PC Bing Searches")
        else:
            self.home_page.update_section("Mobile Bing Searches")
        self.home_page.update_detail(f"0/{numberOfSearches}")
        i = 0
        r = RandomWords()
        try:
            search_terms = r.get_random_words(limit = numberOfSearches)
            if search_terms is None:
                raise Exception
        except Exception:
            search_terms = self.get_google_trends(numberOfSearches)
            if len(search_terms) == 0:
                try:
                    words = open(f"{Path(__file__).parent.resolve()}/searchwords.txt", "r").read().splitlines()
                    search_terms = random.sample(words, numberOfSearches)
                except:
                    raise GetSearchWordsException
        for word in search_terms:
            i += 1
            self.home_page.update_detail(f"{i}/{numberOfSearches}")
            points = self.bing_search(word, isMobile)
            self.home_page.update_points_counter(points)
            if points <= self.points_counter:
                relatedTerms = self.get_related_terms(word)
                for term in relatedTerms:
                    points = self.bing_search(term, isMobile)
                    self.home_page.update_points_counter(points)
                    if points >= self.points_counter:
                        break
            if points > 0:
                self.points_counter = points
            else:
                break
            
    def bing_search(self, word: str, isMobile: bool):
        try:
            if not isMobile:
                self.browser.find_element(By.ID, 'sb_form_q').clear()
                time.sleep(1)
            else:
                self.browser.get('https://bing.com')
        except:
            self.browser.get('https://bing.com')
        time.sleep(2)
        searchbar = self.browser.find_element(By.ID, 'sb_form_q')
        if self.page.client_storage.get("MRFarmer.fast"):
            searchbar.send_keys(word)
            time.sleep(1)
        else:
            for char in word:
                searchbar.send_keys(char)
                time.sleep(0.33)
        searchbar.submit()
        time.sleep(random.randint(12, 24) if not self.page.client_storage.get("MRFarmer.fast") else random.randint(6, 9))
        points = 0
        try:
            points = self.get_points_from_bing(isMobile)
        except:
            pass
        return points
    
    def complete_promotional_items(self):
        try:
            self.home_page.update_detail("Promotional items")
            item = self.get_dashboard_data()["promotionalItem"]
            if (item["pointProgressMax"] == 100 or item["pointProgressMax"] == 200) and item["complete"] == False and item["destinationUrl"] == self.base_url:
                self.browser.find_element(By.XPATH, '//*[@id="promo-item"]/section/div/div/div/a').click()
                time.sleep(1)
                self.browser.switch_to.window(window_name = self.browser.window_handles[1])
                time.sleep(8)
                self.home_page.update_points_counter(self.get_points_from_bing(False))
                self.browser.close()
                time.sleep(2)
                self.browser.switch_to.window(window_name = self.browser.window_handles[0])
                time.sleep(2)
        except:
            pass
        
    def complete_daily_set_search(self, cardNumber: int):
        time.sleep(5)
        self.browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section/div/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-daily-set-item-content/div/a/div/span').click()
        time.sleep(1)
        self.browser.switch_to.window(window_name = self.browser.window_handles[1])
        time.sleep(random.randint(13, 17) if not self.page.client_storage.get("MRFarmer.fast") else random.randint(6, 9))
        self.home_page.update_points_counter(self.get_points_from_bing(False))
        self.browser.close()
        time.sleep(2)
        self.browser.switch_to.window(window_name = self.browser.window_handles[0])
        time.sleep(2)
        
    def complete_daily_set_survey(self, cardNumber: int):
        time.sleep(5)
        self.browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section/div/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-daily-set-item-content/div/a/div/span').click()
        time.sleep(1)
        self.browser.switch_to.window(window_name = self.browser.window_handles[1])
        time.sleep(8 if not self.page.client_storage.get("MRFarmer.fast") else 5)
        # Accept cookie popup
        if self.is_element_exists(By.ID, 'bnp_container'):
            self.browser.find_element(By.ID, 'bnp_btn_accept').click()
            time.sleep(2)
        # Click on later on Bing wallpaper app popup
        if self.is_element_exists(By.ID, 'b_notificationContainer_bop'):
            self.browser.find_element(By.ID, 'bnp_hfly_cta2').click()
            time.sleep(2)
        self.browser.find_element(By.ID, "btoption" + str(random.randint(0, 1))).click()
        time.sleep(random.randint(10, 15) if not self.page.client_storage.get("MRFarmer.fast") else 7)
        self.home_page.update_points_counter(self.get_points_from_bing(False))
        self.browser.close()
        time.sleep(2)
        self.browser.switch_to.window(window_name = self.browser.window_handles[0])
        time.sleep(2)
        
    def complete_daily_set_quiz(self, cardNumber: int):
        time.sleep(5)
        self.browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section[1]/div/mee-card-group[1]/div[1]/mee-card[{str(cardNumber)}]/div[1]/card-content[1]/mee-rewards-daily-set-item-content[1]/div[1]/a[1]/div[3]/span[1]').click()
        time.sleep(3)
        self.browser.switch_to.window(window_name = self.browser.window_handles[1])
        time.sleep(12 if not self.page.client_storage.get("MRFarmer.fast") else random.randint(5, 8))
        if not self.wait_until_quiz_loads():
            self.reset_tabs()
            return
        # Accept cookie popup
        if self.is_element_exists(By.ID, 'bnp_container'):
            self.browser.find_element(By.ID, 'bnp_btn_accept').click()
            time.sleep(2)
        self.browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        self.wait_until_visible(By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10)
        time.sleep(3)
        numberOfQuestions = self.browser.execute_script("return _w.rewardsQuizRenderInfo.maxQuestions")
        numberOfOptions = self.browser.execute_script("return _w.rewardsQuizRenderInfo.numberOfOptions")
        for _ in range(numberOfQuestions):
            if numberOfOptions == 8:
                answers = []
                for i in range(8):
                    if self.browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute("iscorrectoption").lower() == "true":
                        answers.append("rqAnswerOption" + str(i))
                for answer in answers:
                    # Click on later on Bing wallpaper app popup
                    if self.is_element_exists(By.ID, 'b_notificationContainer_bop'):
                        self.browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                        time.sleep(2)
                    self.browser.find_element(By.ID, answer).click()
                    time.sleep(5)
                    if not self.wait_until_question_refresh():
                        return
                time.sleep(5)
            elif numberOfOptions == 4:
                correctOption = self.browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")
                for i in range(4):
                    if self.browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute("data-option") == correctOption:
                        # Click on later on Bing wallpaper app popup
                        if self.is_element_exists(By.ID, 'b_notificationContainer_bop'):
                            self.browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                            time.sleep(2)
                        self.browser.find_element(By.ID, "rqAnswerOption" + str(i)).click()
                        time.sleep(5)
                        if not self.wait_until_question_refresh():
                            return
                        break
                time.sleep(5)
            self.home_page.update_points_counter(self.get_points_from_bing(False))
        time.sleep(5)
        self.browser.close()
        time.sleep(2)
        self.browser.switch_to.window(window_name = self.browser.window_handles[0])
        time.sleep(2)

    def complete_daily_set_variable_activity(self, cardNumber: int):
        time.sleep(2)
        self.browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section/div/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-daily-set-item-content/div/a/div/span').click()
        time.sleep(1)
        self.browser.switch_to.window(window_name = self.browser.window_handles[1])
        time.sleep(8)
        # Accept cookie popup
        if self.is_element_exists(By.ID, 'bnp_container'):
            self.browser.find_element(By.ID, 'bnp_btn_accept').click()
            time.sleep(2)
        try :
            self.browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
            self.wait_until_visible(By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 3)
        except (NoSuchElementException, TimeoutException):
            try:
                counter = str(self.browser.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute('innerHTML'))[:-1][1:]
                numberOfQuestions = max([int(s) for s in counter.split() if s.isdigit()])
                for question in range(numberOfQuestions):
                    # Click on later on Bing wallpaper app popup
                    if self.is_element_exists(By.ID, 'b_notificationContainer_bop'):
                        self.browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                        time.sleep(2)
                        
                    self.browser.execute_script(f'document.evaluate("//*[@id=\'QuestionPane{str(question)}\']/div[1]/div[2]/a[{str(random.randint(1, 3))}]/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
                    time.sleep(8)
                    self.home_page.update_points_counter(self.get_points_from_bing(False))
                time.sleep(5)
                self.browser.close()
                time.sleep(2)
                self.browser.switch_to.window(window_name=self.browser.window_handles[0])
                time.sleep(2)
                return
            except NoSuchElementException:
                time.sleep(random.randint(5, 9))
                self.browser.close()
                time.sleep(2)
                self.browser.switch_to.window(window_name = self.browser.window_handles[0])
                time.sleep(2)
                return
        time.sleep(3)
        correctAnswer = self.browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")
        if self.browser.find_element(By.ID, "rqAnswerOption0").get_attribute("data-option") == correctAnswer:
            self.browser.find_element(By.ID, "rqAnswerOption0").click()
        else :
            self.browser.find_element(By.ID, "rqAnswerOption1").click()
        time.sleep(10)
        self.home_page.update_points_counter(self.get_points_from_bing(False))
        self.browser.close()
        time.sleep(2)
        self.browser.switch_to.window(window_name = self.browser.window_handles[0])
        time.sleep(2)
        
    def complete_daily_set_this_or_that(self, cardNumber: int):
        time.sleep(2)
        self.browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-daily-set-section/div/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-daily-set-item-content/div/a/div/span').click()
        time.sleep(1)
        self.browser.switch_to.window(window_name=self.browser.window_handles[1])
        time.sleep(15 if not self.page.client_storage.get("MRFarmer.fast") else random.randint(5, 8))
        # Accept cookie popup
        if self.is_element_exists(By.ID, 'bnp_container'):
            self.browser.find_element(By.ID, 'bnp_btn_accept').click()
            time.sleep(2)
        if not self.wait_until_quiz_loads():
            self.reset_tabs()
            return
        self.browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        self.wait_until_visible(By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10)
        time.sleep(5)
        for _ in range(10):
            # Click on later on Bing wallpaper app popup
            if self.is_element_exists(By.ID, 'b_notificationContainer_bop'):
                self.browser.find_element(By.ID, 'bnp_hfly_cta2').click()
                time.sleep(2)
            
            answerEncodeKey = self.browser.execute_script("return _G.IG")

            answer1 = self.browser.find_element(By.ID, "rqAnswerOption0")
            answer1Title = answer1.get_attribute('data-option')
            answer1Code = self.get_answer_code(answerEncodeKey, answer1Title)

            answer2 = self.browser.find_element(By.ID, "rqAnswerOption1")
            answer2Title = answer2.get_attribute('data-option')
            answer2Code = self.get_answer_code(answerEncodeKey, answer2Title)

            correctAnswerCode = self.browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")

            if (answer1Code == correctAnswerCode):
                answer1.click()
                time.sleep(15 if not self.page.client_storage.get("MRFarmer.fast") else 7)
            elif (answer2Code == correctAnswerCode):
                answer2.click()
                time.sleep(15 if not self.page.client_storage.get("MRFarmer.fast") else 7)
            self.home_page.update_points_counter(self.get_points_from_bing(False))

        time.sleep(5)
        self.browser.close()
        time.sleep(2)
        self.browser.switch_to.window(window_name=self.browser.window_handles[0])
        time.sleep(2)
    
    def complete_daily_set(self):
        self.home_page.update_section("Daily Set")
        d = self.get_dashboard_data()
        todayDate = datetime.today().strftime('%m/%d/%Y')
        todayPack = []
        for date, data in d['dailySetPromotions'].items():
            if date == todayDate:
                todayPack = data
        for activity in todayPack:
            try:
                if activity['complete'] == False:
                    cardNumber = int(activity['offerId'][-1:])
                    if activity['promotionType'] == "urlreward":
                        self.home_page.update_detail(f'Search of card {str(cardNumber)}')
                        self.complete_daily_set_search(cardNumber)
                    if activity['promotionType'] == "quiz":
                        if activity['pointProgressMax'] == 50 and activity['pointProgress'] == 0:
                            self.home_page.update_detail(f'This or That of card {str(cardNumber)}')
                            self.complete_daily_set_this_or_that(cardNumber)
                        elif (activity['pointProgressMax'] == 40 or activity['pointProgressMax'] == 30) and activity['pointProgress'] == 0:
                            self.home_page.update_detail(f"Quiz of card {str(cardNumber)}")
                            self.complete_daily_set_quiz(cardNumber)
                        elif activity['pointProgressMax'] == 10 and activity['pointProgress'] == 0:
                            searchUrl = urllib.parse.unquote(urllib.parse.parse_qs(urllib.parse.urlparse(activity['destinationUrl']).query)['ru'][0])
                            searchUrlQueries = urllib.parse.parse_qs(urllib.parse.urlparse(searchUrl).query)
                            filters = {}
                            for filter in searchUrlQueries['filters'][0].split(" "):
                                filter = filter.split(':', 1)
                                filters[filter[0]] = filter[1]
                            if "PollScenarioId" in filters:
                                self.home_page.update_detail(f"Poll of card {str(cardNumber)}")
                                self.complete_daily_set_survey(cardNumber)
                            else:
                                self.home_page.update_detail(f"Quiz of card {str(cardNumber)}")
                                self.complete_daily_set_variable_activity(cardNumber)
            except Exception as e:
                if self.page.client_storage.get("MRFarmer.save_errors"):
                    self.save_errors(str(e))
                self.reset_tabs()
        self.accounts[self.account_index]["log"]["Daily"] = True
        self.update_accounts() 
        
    def complete_punch_card(self, url: str, childPromotions: dict):
        self.browser.get(url)
        for child in childPromotions:
            if child['complete'] == False:
                if child['promotionType'] == "urlreward":
                    self.browser.execute_script("document.getElementsByClassName('offer-cta')[0].click()")
                    time.sleep(1)
                    self.browser.switch_to.window(window_name = self.browser.window_handles[1])
                    time.sleep(random.randint(13, 17))
                    self.browser.close()
                    time.sleep(2)
                    self.browser.switch_to.window(window_name = self.browser.window_handles[0])
                    time.sleep(2)
                if child['promotionType'] == "quiz" and child['pointProgressMax'] >= 50 :
                    self.browser.find_element(By.XPATH, '//*[@id="rewards-dashboard-punchcard-details"]/div[2]/div[2]/div[7]/div[3]/div[1]/a').click()
                    time.sleep(1)
                    self.browser.switch_to.window(window_name = self.browser.window_handles[1])
                    time.sleep(15)
                    try:
                        self.browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
                    except:
                        pass
                    time.sleep(5)
                    self.wait_until_visible(By.XPATH, '//*[@id="currentQuestionContainer"]', 10)
                    numberOfQuestions = self.browser.execute_script("return _w.rewardsQuizRenderInfo.maxQuestions")
                    AnswerdQuestions = self.browser.execute_script("return _w.rewardsQuizRenderInfo.CorrectlyAnsweredQuestionCount")
                    numberOfQuestions -= AnswerdQuestions
                    for question in range(numberOfQuestions):
                        answer = self.browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")
                        self.browser.find_element(By.XPATH, f'//input[@value="{answer}"]').click()
                        time.sleep(15)
                    time.sleep(5)
                    self.browser.close()
                    time.sleep(2)
                    self.browser.switch_to.window(window_name=self.browser.window_handles[0])
                    time.sleep(2)
                    self.browser.refresh()
                    break
                elif child['promotionType'] == "quiz" and child['pointProgressMax'] < 50:
                    self.browser.execute_script("document.getElementsByClassName('offer-cta')[0].click()")
                    time.sleep(1)
                    self.browser.switch_to.window(window_name = self.browser.window_handles[1])
                    time.sleep(8)
                    counter = str(self.browser.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute('innerHTML'))[:-1][1:]
                    numberOfQuestions = max([int(s) for s in counter.split() if s.isdigit()])
                    for question in range(numberOfQuestions):
                        self.browser.execute_script('document.evaluate("//*[@id=\'QuestionPane' + str(question) + '\']/div[1]/div[2]/a[' + str(random.randint(1, 3)) + ']/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
                        time.sleep(10)
                    time.sleep(5)
                    self.browser.close()
                    time.sleep(2)
                    self.browser.switch_to.window(window_name = self.browser.window_handles[0])
                    time.sleep(2)
                    self.browser.refresh()
                    break
                
    def complete_punch_cards(self):
        punchCards = self.get_dashboard_data()['punchCards']
        self.home_page.update_section("Punch cards")
        self.home_page.update_detail("-")
        for punchCard in punchCards:
            try:
                if punchCard['parentPromotion'] != None and punchCard['childPromotions'] != None and punchCard['parentPromotion']['complete'] == False and punchCard['parentPromotion']['pointProgressMax'] != 0:
                    url = punchCard['parentPromotion']['attributes']['destination']
                    self.complete_punch_card(url, punchCard['childPromotions'])
            except Exception as e:
                if self.page.client_storage.get("MRFarmer.save_errors"):
                    self.save_errors(str(e))
                self.reset_tabs()
        time.sleep(2)
        self.browser.get(self.base_url)
        time.sleep(2)
        self.accounts[self.account_index]["log"]["Punch cards"] = True
        self.update_accounts()
        
    def complete_more_promotion_search(self, cardNumber: int):
        self.browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-more-activities-card/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-more-activities-card-item/div/a/div/span').click()
        time.sleep(1)
        self.browser.switch_to.window(window_name = self.browser.window_handles[1])
        time.sleep(random.randint(13, 17) if not self.page.client_storage.get("MRFarmer.fast") else random.randint(5, 8))
        self.home_page.update_points_counter(self.get_points_from_bing(False))
        self.browser.close()
        time.sleep(2)
        self.browser.switch_to.window(window_name = self.browser.window_handles[0])
        time.sleep(2)
        
    def complete_more_promotion_quiz(self, cardNumber: int):
        self.browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-more-activities-card/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-more-activities-card-item/div/a/div/span').click()
        time.sleep(1)
        self.browser.switch_to.window(window_name=self.browser.window_handles[1])
        time.sleep(8 if not self.page.client_storage.get("MRFarmer.fast") else 5)
        if not self.wait_until_quiz_loads():
            self.reset_tabs()
            return
        CurrentQuestionNumber = self.browser.execute_script("return _w.rewardsQuizRenderInfo.currentQuestionNumber")
        if CurrentQuestionNumber == 1 and self.is_element_exists(By.XPATH, '//*[@id="rqStartQuiz"]'):
            self.browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        self.wait_until_visible(By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10)
        time.sleep(3)
        numberOfQuestions = self.browser.execute_script("return _w.rewardsQuizRenderInfo.maxQuestions")
        Questions = numberOfQuestions - CurrentQuestionNumber + 1
        numberOfOptions = self.browser.execute_script("return _w.rewardsQuizRenderInfo.numberOfOptions")
        for _ in range(Questions):
            if numberOfOptions == 8:
                answers = []
                for i in range(8):
                    if self.browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute("iscorrectoption").lower() == "true":
                        answers.append("rqAnswerOption" + str(i))
                for answer in answers:
                    self.browser.find_element(By.ID, answer).click()
                    time.sleep(5)
                    if not self.wait_until_question_refresh():
                        return
                time.sleep(5)
            elif numberOfOptions == 4:
                correctOption = self.browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")
                for i in range(4):
                    if self.browser.find_element(By.ID, "rqAnswerOption" + str(i)).get_attribute("data-option") == correctOption:
                        self.browser.find_element(By.ID, "rqAnswerOption" + str(i)).click()
                        time.sleep(5)
                        if not self.wait_until_question_refresh():
                            return
                        break
                time.sleep(5)
            self.home_page.update_points_counter(self.get_points_from_bing(False))
        time.sleep(5)
        self.browser.close()
        time.sleep(2)
        self.browser.switch_to.window(window_name=self.browser.window_handles[0])
        time.sleep(2)
        
    def complete_more_promotion_ABC(self, cardNumber: int):
        self.browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-more-activities-card/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-more-activities-card-item/div/a/div/span').click()
        time.sleep(1)
        self.browser.switch_to.window(window_name=self.browser.window_handles[1])
        time.sleep(8 if not self.page.client_storage.get("MRFarmer.fast") else 5)
        counter = str(self.browser.find_element(By.XPATH, '//*[@id="QuestionPane0"]/div[2]').get_attribute('innerHTML'))[:-1][1:]
        numberOfQuestions = max([int(s) for s in counter.split() if s.isdigit()])
        for question in range(numberOfQuestions):
            self.browser.execute_script(f'document.evaluate("//*[@id=\'QuestionPane{str(question)}\']/div[1]/div[2]/a[{str(random.randint(1, 3))}]/div", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()')
            time.sleep(8 if not self.page.client_storage.get("MRFarmer.fast") else 5)
        time.sleep(5)
        self.home_page.update_points_counter(self.get_points_from_bing(False))
        self.browser.close()
        time.sleep(2)
        self.browser.switch_to.window(window_name=self.browser.window_handles[0])
        time.sleep(2)
        
    def complete_more_promotion_this_or_that(self, cardNumber: int):
        self.browser.find_element(By.XPATH, f'//*[@id="app-host"]/ui-view/mee-rewards-dashboard/main/div/mee-rewards-more-activities-card/mee-card-group/div/mee-card[{str(cardNumber)}]/div/card-content/mee-rewards-more-activities-card-item/div/a/div/span').click()
        time.sleep(1)
        self.browser.switch_to.window(window_name=self.browser.window_handles[1])
        time.sleep(8 if not self.page.client_storage.get("MRFarmer.fast") else 5)
        if not self.wait_until_quiz_loads():
            self.reset_tabs()
            return
        CrrentQuestionNumber = self.browser.execute_script("return _w.rewardsQuizRenderInfo.currentQuestionNumber")
        NumberOfQuestionsLeft = 10 - CrrentQuestionNumber + 1
        if CrrentQuestionNumber == 1 and self.is_element_exists(By.XPATH, '//*[@id="rqStartQuiz"]'):
            self.browser.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        self.wait_until_visible(By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10)
        time.sleep(3)
        for _ in range(NumberOfQuestionsLeft):
            answerEncodeKey = self.browser.execute_script("return _G.IG")

            answer1 = self.browser.find_element(By.ID, "rqAnswerOption0")
            answer1Title = answer1.get_attribute('data-option')
            answer1Code = self.get_answer_code(answerEncodeKey, answer1Title)

            answer2 = self.browser.find_element(By.ID, "rqAnswerOption1")
            answer2Title = answer2.get_attribute('data-option')
            answer2Code = self.get_answer_code(answerEncodeKey, answer2Title)

            correctAnswerCode = self.browser.execute_script("return _w.rewardsQuizRenderInfo.correctAnswer")

            if (answer1Code == correctAnswerCode):
                answer1.click()
                time.sleep(8 if not self.page.client_storage.get("MRFarmer.fast") else 5)
            elif (answer2Code == correctAnswerCode):
                answer2.click()
                time.sleep(8 if not self.page.client_storage.get("MRFarmer.fast") else 5)
            self.home_page.update_points_counter(self.get_points_from_bing(False))

        time.sleep(5)
        self.browser.close()
        time.sleep(2)
        self.browser.switch_to.window(window_name=self.browser.window_handles[0])
        time.sleep(2)
        
    def complete_more_promotions(self):
        self.home_page.update_section("More activities")
        morePromotions = self.get_dashboard_data()['morePromotions']
        i = 0
        for promotion in morePromotions:
            try:
                i += 1
                if promotion['complete'] == False and promotion['pointProgressMax'] != 0:
                    if promotion['promotionType'] == "urlreward":
                        self.home_page.update_detail("Search card")
                        self.complete_more_promotion_search(i)
                    elif promotion['promotionType'] == "quiz":
                        if promotion['pointProgressMax'] == 10:
                            self.home_page.update_detail("ABC card")
                            self.complete_more_promotion_ABC(i)
                        elif promotion['pointProgressMax'] == 30 or promotion['pointProgressMax'] == 40:
                            self.home_page.update_detail("Quiz card")
                            self.complete_more_promotion_quiz(i)
                        elif promotion['pointProgressMax'] == 50:
                            self.home_page.update_detail("This or that card")
                            self.complete_more_promotion_this_or_that(i)
                    else:
                        if promotion['pointProgressMax'] == 100 or promotion['pointProgressMax'] == 200:
                            self.home_page.update_detail("Search card")
                            self.complete_more_promotion_search(i)
                if promotion['complete'] == False and promotion['pointProgressMax'] == 100 and promotion['promotionType'] == "" \
                    and promotion['destinationUrl'] == self.base_url:
                        self.home_page.update_detail("Search card")
                        self.complete_more_promotion_search(i)
            except Exception as e:
                if self.page.client_storage.get("MRFarmer.save_errors"):
                    self.save_errors(str(e))
                self.reset_tabs()
        self.home_page.update_section("-")
        self.home_page.update_detail("-")
        self.accounts[self.account_index]["log"]['More promotions'] = True
        self.update_accounts()
    
    def complete_msn_shopping_game_quiz(self):

        def expand_shadow_element(element, index: int = None) -> Union[List[WebElement], WebElement]:
            """Returns childrens of shadow element, if index provided it returns the element at that index"""
            if index is not None:
                shadow_root = WebDriverWait(self.browser, 45).until(
                    EC.visibility_of(self.browser.execute_script('return arguments[0].shadowRoot.children', element)[index])
                )
            else:
                # wait to visible one element then get the list
                WebDriverWait(self.browser, 45).until(
                    EC.visibility_of(self.browser.execute_script('return arguments[0].shadowRoot.children', element)[0])
                )
                shadow_root = self.browser.execute_script('return arguments[0].shadowRoot.children', element)
            return shadow_root

        def get_children(element) -> List[WebElement]:
            children = self.browser.execute_script('return arguments[0].children', element)
            return children
        
        def get_sign_in_button() -> WebElement:
            """check wheather user is signed in or not and return the button to sign in"""
            script_to_user_pref_container = 'document.getElementsByTagName("shopping-page-base")[0]\
                .shadowRoot.children[0].children[1].children[0]\
                .shadowRoot.children[0].shadowRoot.children[0]\
                .getElementsByClassName("user-pref-container")[0]'
            WebDriverWait(self.browser, 60).until(EC.visibility_of(
                self.browser.execute_script(f'return {script_to_user_pref_container}')
                )
            )
            button = WebDriverWait(self.browser, 60).until(EC.visibility_of(
                    self.browser.execute_script(
                        f'return {script_to_user_pref_container}.\
                        children[0].children[0].shadowRoot.children[0].\
                        getElementsByClassName("me-control")[0]'
                    )
                )
            )
            return button
            
        def sign_in():
            self.home_page.update_detail("Signing in")
            sign_in_button = get_sign_in_button()
            sign_in_button.click()
            time.sleep(5)
            self.wait_until_visible(By.ID, 'newSessionLink', 10)
            self.browser.find_element(By.ID, 'newSessionLink').click()
            self.answer_to_security_info_update()
            self.home_page.update_detail("Waiting for elements")
            self.wait_until_visible(By.TAG_NAME, 'shopping-page-base', 60)
            expand_shadow_element(self.browser.find_element(By.TAG_NAME, 'shopping-page-base'), 0)
            self.home_page.update_detail("Checking signed in state")
            get_sign_in_button()
            time.sleep(5 if self.page.client_storage.get("MRFarmer.fast") else 10)
        
        def get_gaming_card() -> Union[WebElement, bool]:
            shopping_page_base_childs = expand_shadow_element(self.browser.find_element(By.TAG_NAME, 'shopping-page-base'), 0)
            shopping_homepage = shopping_page_base_childs.find_element(By.TAG_NAME, 'shopping-homepage')
            msft_feed_layout = expand_shadow_element(shopping_homepage, 0).find_element(By.TAG_NAME, 'msft-feed-layout')
            cards = expand_shadow_element(msft_feed_layout)
            for card in cards:
                if card.get_attribute("gamestate") == "active":
                    return card
            else:
                return False
        
        def click_correct_answer():
            options_container = expand_shadow_element(gaming_card, 1)
            options_elements = get_children(get_children(options_container)[1])
            # click on the correct answer in options_elements
            correct_answer = options_elements[int(gaming_card.get_attribute("_correctAnswerIndex"))]
            # click to show the select button
            correct_answer.click()
            time.sleep(1)
            # click 'select' button
            select_button = correct_answer.find_element(By.CLASS_NAME, 'shopping-select-overlay-button')
            WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable(select_button))
            select_button.click()
        
        def click_play_again():
            time.sleep(random.randint(4, 6))
            options_container = expand_shadow_element(gaming_card)[1]
            get_children(options_container)[0].find_element(By.TAG_NAME, 'button').click()
        
        try:
            tries = 0
            while tries <= 4:
                tries += 1
                self.home_page.update_section(f"MSN shopping game - try ({tries})")
                self.browser.get("https://www.msn.com/en-us/shopping")
                self.home_page.update_detail("Waiting for elements")
                self.wait_until_visible(By.TAG_NAME, 'shopping-page-base', 60)
                time.sleep(15)
                self.home_page.update_detail("Waiting for sign in state")
                try:
                    sign_in_button = get_sign_in_button()
                except:
                    if tries == 4:
                        raise ElementNotVisibleException("Sign in button did not show up")
                else:
                    break
            time.sleep(5)
            if "Sign in" in sign_in_button.text:
                sign_in()
            self.home_page.update_detail("Locating gaming card")
            gaming_card = get_gaming_card()
            scrolls = 0
            while not gaming_card and scrolls <= 5:
                scrolls += 1
                self.home_page.update_detail(f"Locating gaming card - scrolling ({scrolls}/5)")
                self.browser.execute_script("window.scrollBy(0, 300);")
                time.sleep(10)
                gaming_card = get_gaming_card()
                if gaming_card:
                    self.browser.execute_script("arguments[0].scrollIntoView();", gaming_card)
                    self.home_page.update_detail("Gaming card found")
                    time.sleep(random.randint(7, 10))
                if scrolls == 5 and not gaming_card:
                    raise GamingCardNotFound("Gaming card not found")
            self.home_page.update_detail("Answering questions")
            for _ in range(10):
                try:
                    click_correct_answer()
                    click_play_again()
                    time.sleep(random.randint(5, 7))
                except (NoSuchElementException, JavascriptException):
                    break
        except GamingCardNotFound:
            self.home_page.update_detail("Gaming card not found")
        except Exception as e:
            if self.page.client_storage.get("MRFarmer.save_errors"):
                self.save_errors(str(e))
            self.home_page.update_detail("Failed to complete")
        else:
            self.home_page.update_detail("Completed")
        finally:
            self.browser.get(self.base_url)
            self.accounts[self.account_index]["log"]["MSN shopping game"] = True
            self.update_accounts()
            self.home_page.update_section("-")
            self.home_page.update_detail("-")
            self.wait_until_visible(By.ID, 'app-host', 30)
        
    def get_remaining_searches(self):
        dashboard = self.get_dashboard_data()
        searchPoints = 1
        counters = dashboard['userStatus']['counters']
        if not 'pcSearch' in counters:
            return 0, 0
        progressDesktop = counters['pcSearch'][0]['pointProgress'] + counters['pcSearch'][1]['pointProgress']
        targetDesktop = counters['pcSearch'][0]['pointProgressMax'] + counters['pcSearch'][1]['pointProgressMax']
        if targetDesktop == 33 :
            #Level 1 EU
            searchPoints = 3
        elif targetDesktop == 55 :
            #Level 1 US
            searchPoints = 5
        elif targetDesktop == 102 :
            #Level 2 EU
            searchPoints = 3
        elif targetDesktop >= 170 :
            #Level 2 US
            searchPoints = 5
        remainingDesktop = int((targetDesktop - progressDesktop) / searchPoints)
        remainingMobile = 0
        if dashboard['userStatus']['levelInfo']['activeLevel'] != "Level1":
            progressMobile = counters['mobileSearch'][0]['pointProgress']
            targetMobile = counters['mobileSearch'][0]['pointProgressMax']
            remainingMobile = int((targetMobile - progressMobile) / searchPoints)
        return remainingDesktop, remainingMobile
    
    def get_points_from_bing(self, isMobile: bool = False):
        try:
            if not isMobile:
                try:
                    points = int(self.browser.find_element(By.ID, 'id_rc').get_attribute('innerHTML'))
                except ValueError:
                    points = int(self.browser.find_element(By.ID, 'id_rc').get_attribute('innerHTML').replace(",", ""))
            else:
                try:
                    self.browser.find_element(By.ID, 'mHamburger').click()
                except UnexpectedAlertPresentException:
                    try:
                        self.browser.switch_to.alert.accept()
                        time.sleep(1)
                        self.browser.find_element(By.ID, 'mHamburger').click()
                    except NoAlertPresentException:
                        pass
                time.sleep(1)
                points = int(self.browser.find_element(By.ID, 'fly_id_rc').get_attribute('innerHTML'))
        except NoSuchElementException:
            points = self.points_counter
        else:
            self.point_counter = points
        return points
    
    def disable_stop_button(self, state: bool):
        self.home_page.stop_button.disabled = state
        self.page.update()
    
    def save_errors(self, error: str):
        with open(f"{Path.cwd()}/errors.txt", "a") as f:
            f.write(f"\n-------------------{datetime.now()}-------------------\r\n")
            f.write(f"{error}\n")
    
    def perform_run(self):
        """Check whether timer is set to run it at time else run immediately"""
        if self.page.client_storage.get("MRFarmer.timer_switch"):
            requested_time = self.page.client_storage.get("MRFarmer.timer")
            self.home_page.update_section(f"Waiting for {requested_time}")
            self.home_page.update_overall_infos()
            while datetime.now().strftime("%H:%M") != requested_time:
                if not self.parent.is_farmer_running:
                    return None
                time.sleep(1)
            else:
                self.get_or_create_logs()
                return self.run()
        self.get_or_create_logs()
        return self.run()
    
    def run(self):
        for account in self.accounts:
            while self.parent.get_farming_status():
                try:
                    self.current_account = account
                    self.account_index = self.accounts.index(account)
                    if account["username"] in self.finished_accounts or account["username"] in self.suspended_accounts:
                        break
                    if account["log"]["Last check"] != str(date.today()):
                        account["log"]["Last check"] = str(date.today())
                        self.update_accounts()
                    self.home_page.update_current_account(account["username"])
                    self.home_page.update_overall_infos()
                    redeem_goal_title = ""
                    if self.is_pc_need(account):

                        self.browser_setup(False, self.page.client_storage.get("MRFarmer.pc_user_agent"))
                        self.disable_stop_button(False)
                        self.login(account["username"], account["password"])
                        self.home_page.update_detail("Logged in")
                        
                        self.browser.get(self.base_url)
                        self.wait_until_visible(By.ID, 'app-host', 30)
                        self.starting_points = self.get_account_points()
                        redeem_goal_title, redeem_goal_price = self.get_redeem_goal()
                        self.points_counter = self.starting_points
                        self.home_page.update_points_counter(self.points_counter)

                        if self.page.client_storage.get("MRFarmer.daily_quests") and not account["log"]["Daily"]:
                            self.complete_daily_set()

                        if self.page.client_storage.get("MRFarmer.punch_cards") and not account["log"]["Punch cards"]:
                            self.complete_punch_cards()

                        if self.page.client_storage.get("MRFarmer.more_activities") and not account["log"]["More promotions"]:
                            self.complete_more_promotions()

                        if self.page.client_storage.get("MRFarmer.msn_shopping_game") and not account["log"]["MSN shopping game"]:
                            self.complete_msn_shopping_game_quiz()
                            self.home_page.update_points_counter(self.get_account_points())
                        
                        if self.page.client_storage.get("MRFarmer.pc_search") and not account["log"]["PC searches"]:
                            remainingSearches = self.get_remaining_searches()[0]
                            if remainingSearches > 0:
                                self.bing_searches(remainingSearches)
                            account["log"]["PC searches"] = True
                            self.update_accounts()
                            
                        self.disable_stop_button(True)
                        self.browser.quit()
                        self.home_page.update_detail("-")
                        self.home_page.update_section("-")
                        

                    if self.page.client_storage.get("MRFarmer.mobile_search") and not account["log"]["Mobile searches"]:
                        self.browser_setup(True, account.get('mobile_user_agent', self.page.client_storage.get("MRFarmer.mobile_user_agent")))
                        self.disable_stop_button(False)
                        self.login(account["username"], account["password"], True)
                        if (
                            (
                                self.page.client_storage.get("MRFarmer.send_to_telegram") or
                                self.page.client_storage.get("MRFarmer.send_to_discord")
                            ) and
                            redeem_goal_title == ""
                        ):
                            self.browser.get(self.base_url)
                            self.wait_until_visible(By.ID, 'app-host', 30)
                            redeem_goal_title, redeem_goal_price = self.get_redeem_goal()
                        if self.remainingSearchesM > 0:
                            self.bing_searches(self.remainingSearchesM, True)
                        account["log"]["Mobile searches"] = True
                        self.update_accounts()
                        self.disable_stop_button(True)
                        self.browser.quit()
                        self.home_page.update_detail("-")
                        self.home_page.update_section("-")

                    self.finished_accounts.append(account["username"])
                    if account["log"]["Points"] > 0 and self.points_counter >= account["log"]["Points"]:
                        account["log"]["Today's points"] = self.points_counter - account["log"]["Points"]
                    else:
                        account["log"]["Today's points"] = self.points_counter - self.starting_points
                    account["log"]["Points"] = self.points_counter
                    
                    if (
                        (self.page.client_storage.get("MRFarmer.send_to_telegram") or self.page.client_storage.get("MRFarmer.send_to_discord")) and
                        redeem_goal_title != "" and
                        redeem_goal_price <= self.points_counter
                    ):
                        account["log"]["Redeem goal title"] = redeem_goal_title
                        account["log"]["Redeem goal price"] = redeem_goal_price
                        
                    self.clean_logs()
                    self.update_accounts()
                    self.accounts_page.sync_accounts()

                    self.home_page.update_points_counter(0)
                    self.home_page.update_overall_infos()
                    if self.page.client_storage.get("MRFarmer.use_proxy") and account.get("proxy", False):
                        self.home_page.update_proxy("None")
                    break
                    
                except AccountLockedException:
                    self.browser.quit()
                    self.browser = None
                    account["log"]["Last check"] = "Your account has been locked"
                    self.locked_accounts.append(account["username"])
                    self.update_accounts()
                    self.accounts_page.sync_accounts()
                    self.clean_logs()
                    if self.page.client_storage.get("MRFarmer.use_proxy") and account.get("proxy", False):
                        self.home_page.update_proxy("None")
                    break
                
                except AccountSuspendedException:
                    self.browser.quit()
                    self.browser = None
                    self.suspended_accounts.append(account["username"])
                    account["log"]["Last check"] = "Your account has been suspended"
                    account["log"]["Today's points"] = "N/A" 
                    account["log"]["Points"] = "N/A" 
                    self.clean_logs()
                    self.update_accounts()
                    self.accounts_page.sync_accounts()
                    self.finished_accounts.append(account["username"])
                    self.home_page.update_overall_infos()
                    if self.page.client_storage.get("MRFarmer.use_proxy") and account.get("proxy", False):
                        self.home_page.update_proxy("-")
                    break
                
                except UnusualActivityException:
                    self.browser.quit()
                    self.browser = None
                    account["log"]["Last check"] = "Unusual activity detected"
                    self.finished_accounts.append(account["username"])       
                    self.update_accounts()
                    self.accounts_page.sync_accounts()
                    self.clean_logs()
                    self.home_page.finished()
                    if self.page.client_storage.get("MRFarmer.use_proxy") and account.get("proxy", False):
                        self.home_page.update_proxy("-")
                    return None
                    
                except RegionException:
                    self.browser.quit()
                    self.browser = None
                    self.home_page.finished()
                    self.home_page.update_section("Not available in your region")
                    return None
                
                except GetSearchWordsException:
                    self.browser.quit()
                    self.browser = None
                    account["log"]["Last check"] = "Couldn't get search words"
                    self.finished_accounts.append(account["username"])       
                    self.update_accounts()
                    self.accounts_page.sync_accounts()
                    self.clean_logs()
                    if self.page.client_storage.get("MRFarmer.use_proxy") and account.get("proxy", False):
                        self.home_page.update_proxy("-")
                    break
                
                except UnhandledException:
                    self.browser.quit()
                    self.browser = None
                    account["log"]["Last check"] = "Unknown error"
                    self.finished_accounts.append(account["username"])
                    self.update_accounts()
                    self.accounts_page.sync_accounts()
                    self.clean_logs()
                    if self.page.client_storage.get("MRFarmer.use_proxy") and account.get("proxy", False):
                        self.home_page.update_proxy("-")
                    break
                
                except (InvalidSessionIdException, MaxRetryError, NewConnectionError):
                    try:
                        self.browser.quit()
                    except:
                        pass
                    self.browser = None
                    if not self.parent.is_farmer_running:
                        self.home_page.finished()
                        return None
                    internet = self.check_internet_connection()
                    if internet:
                        pass
                    else:
                        self.home_page.finished()
                        return None
                    
                except SessionNotCreatedException:
                    self.browser = None
                    self.home_page.update_section("Webdriver error")
                    self.home_page.update_detail("Webdriver has outdated")
                    self.parent.display_error("Webdriver error", "Webdriver has outdated. Please update your Webdriver.")
                    self.home_page.finished()
                    return None
                    
                except (Exception, FunctionTimedOut) as e:
                    if "executable needs to be in PATH" in str(e):
                        self.parent.display_error("Webdriver error", str(e))
                        self.home_page.finished()
                        return None
                    try:
                        self.browser.quit()
                    except:
                        pass
                    self.starting_points = None
                    self.browser = None
                    if self.page.client_storage.get("MRFarmer.save_errors"):
                        self.save_errors(str(e))
                    internet = self.check_internet_connection()
                    if internet:
                        pass
                    else:
                        self.home_page.finished()
                        return None
            else:
                return       
        else:
            if self.page.client_storage.get("MRFarmer.send_to_telegram") or self.page.client_storage.get("MRFarmer.send_to_discord"):
                message = self.create_message()
                self.send_report_to_messenger(message)
            self.update_accounts()
            if self.page.client_storage.get("MRFarmer.shutdown"):
                os.system("shutdown /s /t 10")
            self.home_page.finished()
        