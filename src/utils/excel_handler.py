import pandas as pd
from typing import List, Dict
import openpyxl
from zipfile import ZipFile
import re
import os
from pathlib import Path

class ExcelHandler:
    def __init__(self, file_path: str):
        self.file_path = file_path
        
    def read_listings(self) -> List[Dict]:
        """read excel file and return list of listings"""
        try:
            # extract and map images first
            image_map = self._extract_and_map_images()
            
            # read excel data
            df = pd.read_excel(self.file_path)
            
            # map the unnamed columns to our desired names
            column_mapping = {
                'Unnamed: 0': 'description',
                'Unnamed: 1': 'image',
                'Unnamed: 2': 'item_code',
                'Unnamed: 3': 'quantity',
                'Unnamed: 4': 'price',
                'Unnamed: 5': 'total'
            }
            df = df.rename(columns=column_mapping)
            
            # remove header rows and empty rows
            df = df[df['item_code'].notna() & 
                   (df['item_code'] != 'ITEM CODE')]  # exclude header row
            
            # convert numeric columns
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df['total'] = pd.to_numeric(df['total'], errors='coerce')
            
            # clean up description (remove newlines)
            df['description'] = df['description'].str.strip()
            
            # add image paths to the dataframe
            df['image'] = df.index.map(lambda idx: image_map.get(idx))
            
            # convert dataframe to list of dicts
            listings = df.to_dict('records')
            
            # debug print
            print("\nProcessed listings:")
            for listing in listings[:6]:
                print(f"\nListing found:")
                for key, value in listing.items():
                    if isinstance(value, str) and len(value) > 90:
                        print(f"{key}: {value[:90]}...")
                    else:
                        print(f"{key}: {value}")
            
            return listings
            
        except Exception as e:
            raise Exception(f"error reading excel file: {str(e)}")
    
    def _extract_and_map_images(self) -> Dict[int, str]:
        """extract images and return mapping of row index to image path"""
        try:
            # setup image directory
            excel_path = Path(self.file_path)
            images_dir = excel_path.parent / 'images'
            images_dir.mkdir(exist_ok=True)
            
            # get image positions from openpyxl
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb.active
            
            item_codes = []
            for row in ws.iter_rows(min_col=3, max_col=3):  # column C
                value = row[0].value
                if value and str(value).strip() != 'ITEM CODE':
                    item_codes.append(value)
            
            # debug print item codes
            print("\nItem Codes in order:")
            print(item_codes)
            
            # get image positions
            image_positions = []
            for idx, image in enumerate(ws._images):
                if hasattr(image, 'anchor'):
                    row = image.anchor._from.row
                    col = image.anchor._from.col
                    image_positions.append((row, col, idx))
            
            # sort by row to maintain spreadsheet order
            image_positions.sort(key=lambda x: x[0])
            
            # debug print positions
            print("\nImage Positions (row, col, idx):")
            print(image_positions)
            
            # extract images
            with ZipFile(self.file_path) as archive:
                image_files = sorted(
                    [f for f in archive.namelist() if re.match(r'xl/media/image\d+\.(png|jpeg|jpg)', f, re.I)],
                    key=lambda x: int(re.search(r'image(\d+)', x).group(1))
                )
                
                # create mapping of row to image path
                row_to_image = {}
                for (row, col, _), item_code, image_path in zip(image_positions, item_codes, image_files):
                    ext = os.path.splitext(image_path)[1]
                    new_path = images_dir / f"image_{item_code}{ext}"
                    
                    # extract image
                    with archive.open(image_path) as source, open(new_path, 'wb') as target:
                        target.write(source.read())
                    
                    row_to_image[row] = str(new_path)
                    
                return row_to_image
                
        except Exception as e:
            print(f"Error extracting images: {str(e)}")
            return {}