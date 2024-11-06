import pandas as pd
import os
from pathlib import Path
import openpyxl
from zipfile import ZipFile
import re

def extract_images():
    # setup paths
    data_dir = Path('data')
    excel_file = data_dir / 'listings.xlsx'
    images_dir = data_dir / 'images'
    
    # create images directory if it doesn't exist
    images_dir.mkdir(exist_ok=True)
    
    try:
        # first get positions from openpyxl
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
        
        # get positions of all images
        image_positions = []
        for idx, image in enumerate(ws._images):
            # get the anchor position (top-left corner)
            if hasattr(image, 'anchor'):
                top_row = image.anchor._from.row  # vertical position
                left_col = image.anchor._from.col  # horizontal position
                image_positions.append((top_row, left_col, idx + 1))
        
        # sort by row (vertical position) then by column
        image_positions.sort()
        position_map = {old_idx: new_idx for new_idx, (_, _, old_idx) in enumerate(image_positions, 1)}
        
        print(f"Found {len(image_positions)} positioned images")
        
        # now extract images with the correct order
        with ZipFile(excel_file) as archive:
            # find all image files
            image_files = [f for f in archive.namelist() 
                         if re.match(r'xl/media/image\d+\.(png|jpeg|jpg)', f, re.I)]
            
            # extract number from image path for sorting
            def get_image_number(path):
                match = re.search(r'image(\d+)', path)
                return int(match.group(1)) if match else 0
            
            # sort image files by their number
            image_files.sort(key=get_image_number)
            
            # extract each image with new ordering
            for idx, image_path in enumerate(image_files, 1):
                try:
                    new_idx = position_map.get(idx, idx)
                    ext = os.path.splitext(image_path)[1]
                    new_filename = f"image_{new_idx:03d}{ext}"  # pad with zeros for proper sorting
                    new_path = images_dir / new_filename
                    
                    with archive.open(image_path) as source, open(new_path, 'wb') as target:
                        target.write(source.read())
                    print(f"Extracted {image_path} -> {new_path} (position: row {image_positions[new_idx-1][0]})")
                    
                except Exception as img_error:
                    print(f"Error extracting image {idx}: {str(img_error)}")
        
        print("\nDone! Check the 'data/images' directory for extracted images.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        wb.close()

if __name__ == "__main__":
    extract_images() 