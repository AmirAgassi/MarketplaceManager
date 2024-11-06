from .utils.excel_handler import ExcelHandler
from .listing_manager import ListingManager
from typing import List, Dict

class MarketplaceBot:
    def __init__(self):
        self.listing_manager = ListingManager()
        
    def process_excel_file(self, file_path: str):
        """process excel file and create listings"""
        # read excel file
        excel_handler = ExcelHandler(file_path)
        listings = excel_handler.read_listings()
        
        # get current listings
        current_listings = self.listing_manager.get_current_listings()
        
        # process each item
        for item in listings:
            if item['item_code'] not in current_listings:
                self.listing_manager.create_listing(item) 