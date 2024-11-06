from typing import Dict, List
from .content_generator import ContentGenerator
from .browser_controller import BrowserController
from .utils.db_handler import DatabaseHandler

class ListingManager:
    def __init__(self):
        self.browser = BrowserController()
        self.content_generator = ContentGenerator()
        self.db = DatabaseHandler()
        
    def get_current_listings(self) -> List[str]:
        """get list of current item codes from database"""
        return self.db.get_existing_listings()
        
    def create_listing(self, item_data: Dict):
        """create new listing on marketplace"""
        try:
            # generate content
            content = self.content_generator.generate_listing_content(item_data)
            
            # save to database
            self.db.add_listing(
                item_code=item_data.get('item_code'),
                description=content['description']
            )
            
            # placeholder for creating listing
            print(f"Creating listing for {item_data.get('item_code')}")
            print(f"Title: {content['title']}")
            print(f"Description: {content['description']}")
            
        except Exception as e:
            print(f"Error creating listing: {str(e)}")