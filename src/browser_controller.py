from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from typing import Optional
import undetected_chromedriver as uc

class BrowserController:
    def __init__(self):
        self.driver: Optional[Chrome] = None
        
    def initialize_driver(self):
        """initialize undetected chromedriver"""
        # placeholder for now
        print("initializing browser...")
        
    def login_to_facebook(self):
        """ensure logged into facebook"""
        # placeholder for now
        print("checking login status...")
        
    def close(self):
        """close browser"""
        if self.driver:
            self.driver.quit() 