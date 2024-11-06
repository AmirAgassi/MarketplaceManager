from openai import OpenAI
from typing import Dict
from .config import Config

class ContentGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def generate_listing_content(self, item_data: Dict) -> Dict:
        """generate title and description using openai api"""
        # placeholder for now - we'll implement the actual api call later
        prompt = f"Create a marketplace listing title and description for: {item_data}"
        
        try:
            # placeholder response
            return {
                "title": f"Generated title for {item_data.get('item_code', 'unknown')}",
                "description": f"Generated description for {item_data.get('item_code', 'unknown')}"
            }
        except Exception as e:
            raise Exception(f"error generating content: {str(e)}") 