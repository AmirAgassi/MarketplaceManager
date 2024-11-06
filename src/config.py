from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # api keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # file paths
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    # marketplace settings
    MARKETPLACE_URL = "https://www.facebook.com/marketplace"
    
    # browser settings
    HEADLESS = False
    
    # listing settings
    MAX_TITLE_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500 