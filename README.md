# Microsoft (Bing) Rewards Farmer GUI V2
Advance Microsoft (Bing) Rewards bot with Selenium and GUI by Flet framework (Flutter).

<p align="center">
  <img src="https://user-images.githubusercontent.com/60227955/218319443-3f5ea317-e759-4e4c-a847-926b240e2806.png" alt="Main tab">
</p>

You can use the other versions if you have problem with this one:
  - [Terminal version](https://github.com/farshadz1997/Microsoft-Rewards-bot)
  - [PyQt5 version](https://github.com/farshadz1997/Microsoft-Rewards-bot-GUI)

## Installations
Follow these steps to run the app:
  - Install required packages:
    + <pre> pip install -r requirements.txt</pre>
    + Linux users also read this: https://flet.dev/docs/guides/python/getting-started#linux
  - Install Webdriver:
    * Windows:
      + Download [Chrome Webdriver](https://chromedriver.chromium.org/downloads) or
      [Edge Webdriver](https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/) same your browser version:
      + Save Webdriver in ```C:\Windows``` or Farmer directory
    * Linux:
      + <pre>apt install chromium-chromedriver</pre>
      + If you have brew: <pre>brew cask install chromedriver</pre>
  - Run ```main.pyw```.
  

## Features
I added all features from two last version plus some new features:
  - Account management and display account log
  - Support proxy for each account (Proxy must not need to login)
  - Support Mobile user agent for each account (Don't add or change this if you don't know what this is)
  - You can choose to which part of Rewards you want to be done by Bot
  - Support headless browser
  - You can use session to create profile to save cookies of your account in that (By activating this it creates so many files and it takes n GBs of files if 
  many accounts which is totally normal)
  - Shutdown your system after farm if you enabled it
  - Fast mode for high speed connection which half delays
  - Auto start to run farmer on startup application
  - Timer to run the Bot at your choosen time
  - You can use Edge webdriver instead of Chrome
  - Send daily report to your Discord server and your Telegram
  
