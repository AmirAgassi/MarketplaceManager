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
            for listing in listings[:2]:  # show first 2 listings
                print(f"\nListing found:")
                for key, value in listing.items():
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
            
            # get positions of all images
            image_positions = []
            for idx, image in enumerate(ws._images):
                if hasattr(image, 'anchor'):
                    top_row = image.anchor._from.row
                    left_col = image.anchor._from.col
                    image_positions.append((top_row, left_col, idx + 1))
            
            # sort by row then column
            image_positions.sort()
            position_map = {old_idx: new_idx for new_idx, (_, _, old_idx) in enumerate(image_positions, 1)}
            
            # create row to image path mapping
            row_to_image = {}
            
            # extract images with correct order
            with ZipFile(self.file_path) as archive:
                image_files = [f for f in archive.namelist() 
                             if re.match(r'xl/media/image\d+\.(png|jpeg|jpg)', f, re.I)]
                
                def get_image_number(path):
                    match = re.search(r'image(\d+)', path)
                    return int(match.group(1)) if match else 0
                
                image_files.sort(key=get_image_number)
                
                for idx, image_path in enumerate(image_files, 1):
                    try:
                        new_idx = position_map.get(idx, idx)
                        row_num = image_positions[new_idx-1][0]  # get row number for this image
                        
                        ext = os.path.splitext(image_path)[1]
                        new_filename = f"image_{new_idx:03d}{ext}"
                        new_path = images_dir / new_filename
                        
                        # extract image
                        with archive.open(image_path) as source, open(new_path, 'wb') as target:
                            target.write(source.read())
                        
                        # map row number to image path
                        row_to_image[row_num] = str(new_path)
                        
                    except Exception as img_error:
                        print(f"Warning: Error extracting image {idx}: {str(img_error)}")
            
            wb.close()
            return row_to_image
            
        except Exception as e:
            print(f"Warning: Error processing images: {str(e)}")
            return {}  # return empty mapping if image extraction fails