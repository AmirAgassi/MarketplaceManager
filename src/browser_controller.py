from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Optional
import undetected_chromedriver as uc
from .config import Config
import time
import os

class BrowserController:
    def __init__(self):
        self.driver: Optional[Chrome] = None
        self.progress = None

    def set_progress(self, progress):
        """set progress bar instance"""
        self.progress = progress

    def initialize_driver(self) -> bool:
        """initialize undetected chromedriver"""
        try:
            # setup chrome options
            options = uc.ChromeOptions()
            options.headless = Config.HEADLESS
            
            # add additional options for stability
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=600,600')
            options.add_argument('--disable-dev-shm-usage')
            
            # add user data directory to persist login
            os.makedirs(Config.USER_DATA_DIR, exist_ok=True)
            options.add_argument(f'--user-data-dir={Config.USER_DATA_DIR}')
            options.add_argument('--profile-directory=Default')
            
            # initialize driver
            print("initializing browser...")
            self.driver = uc.Chrome(options=options)
            self.driver.implicitly_wait(Config.BROWSER_TIMEOUT)
            
            return True
            
        except Exception as e:
            print(f"error initializing browser: {str(e)}")
            return False
    
    def navigate_to_marketplace(self) -> bool:
        """navigate to facebook marketplace"""
        if not self.driver:
            if not self.initialize_driver():
                return False
        
        try:
            self.driver.get(Config.MARKETPLACE_URL)
            time.sleep(Config.BROWSER_WAIT_TIME)  # wait for potential redirects
            return True
        except Exception as e:
            print(f"error navigating to marketplace: {str(e)}")
            return False
    
    def close(self):
        """close browser"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"error closing browser: {str(e)}")
            finally:
                self.driver = None
    
    def check_login_status(self) -> bool:
        """check if user is logged into facebook"""
        try:
            # set a short implicit wait for this check
            self.driver.implicitly_wait(1)
            login_form = self.driver.find_elements("id", "login_popup_cta_form")
            self.driver.implicitly_wait(5)  # restore to default wait time
            return len(login_form) == 0  # if form exists, user is not logged in
        except Exception as e:
            print(f"error checking login status: {str(e)}")
            return False
    
    def post_listing(self, title: str, description: str, price: float, item_code: str, progress=None) -> bool:
        """post a listing to marketplace"""
        try:
            if progress:
                self.progress = progress
            
            # find and enter title
            self.progress.add_debug("looking for title input...")
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Title"]'))
            )
            self.progress.add_debug(f"entering title: {title[:90]}...")
            title_input.send_keys(title)
            self.progress.add_debug("title entered successfully")

            # find and enter price
            self.progress.add_debug("entering price...")
            price_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Price"]'))
            )
            price_input.send_keys(str(price))
            self.progress.add_debug("price entered successfully")

            # find and select category
            self.progress.add_debug("selecting category...")
            category_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Category"]'))
            )
            category_button.click()
            time.sleep(2)
            # wait for dropdown and select furniture
            furniture_option = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/div[1]/div/div[3]/div/div/div[2]/div/div/div[1]/div[1]/div/div/div/div/div/span/div/div[3]/div/div[1]/div/div/div/div/div/span/div/span"))
            )
            furniture_option.click()
            self.progress.add_debug("category selected successfully")

            # find and select condition
            self.progress.add_debug("selecting condition...")
            condition_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Condition"]'))
            )
            condition_button.click()

            # wait for dropdown menu to be visible
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Select an option"]'))
            )

            # wait for dropdown and select new
            new_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '[role="option"] span:first-of-type'))
            )
            new_option.click()
            self.progress.add_debug("condition selected successfully")

            # find and click photo upload button
            self.progress.add_debug("looking for photo upload button...")
            photo_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
            
            # prepare image path - try different extensions
            extensions = ['.jpg', '.jpeg', '.png']
            image_found = False
            for ext in extensions:
                image_path = os.path.join(Config.DATA_DIR, 'images', f'image_{item_code}{ext}')
                if os.path.exists(image_path):
                    photo_input.send_keys(image_path)
                    self.progress.add_debug("photo uploaded successfully")
                    image_found = True
                    break

            if not image_found:
                self.progress.add_debug(f"warning: image not found for {item_code}", error=True)
                time.sleep(1000)

            # find and enter description
            self.progress.add_debug("entering description...")
            description_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label="Description"]'))
            )
            description_input.send_keys(description)
            self.progress.add_debug("description entered successfully")

            # find and click publish button with retry logic
            self.progress.add_debug("clicking publish...")
            time.sleep(3)
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    publish_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Publish')]"))
                    )
                    time.sleep(2)  # increased wait time to ensure page is stable
                    publish_button.click()
                    self.progress.add_debug("listing published successfully")
                    
                    # handle potential "Leave Page" dialog
                    try:
                        leave_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, '/html/body/div[6]/div[1]/div/div[2]/div/div/div/div[4]/div/div[2]/div[1]'))
                        )
                        time.sleep(0.5)
                        leave_button.click()
                        self.progress.add_debug("handled leave page dialog")
                    except:
                        # no leave page dialog appeared, continue normally
                        pass
                    
                    return True
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        self.progress.add_debug(f"retry attempt {attempt + 1} for publish button...")
                        time.sleep(1)
                        continue
                    else:
                        if self.progress:
                            self.progress.add_debug(f"ERROR: {str(e)}", error=True)
                            self.progress.add_debug("Press Enter to continue...", error=True)
                            time.sleep(0.1)
                            input()
                        return False

            return False
            
        except Exception as e:
            if self.progress:
                self.progress.add_debug(f"ERROR: {str(e)}", error=True)
                self.progress.add_debug("Press Enter to continue...", error=True)
                time.sleep(0.1)
                input()
            return False