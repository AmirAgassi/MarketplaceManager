import curses
import os
from typing import List, Dict, Callable
from datetime import datetime
from ..utils.db_handler import DatabaseHandler
from ..marketplace_bot import MarketplaceBot

class MenuUI:
    def __init__(self):
        self.db = DatabaseHandler()
        self.bot = MarketplaceBot()
        
    def start(self):
        curses.wrapper(self.main_menu)
    
    def main_menu(self, stdscr):
        # setup colors
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # success
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # error/pending
        curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)   # info
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK) # warning
        
        # hide cursor and enable keypad
        curses.curs_set(0)
        stdscr.keypad(True)  # enable keypad mode for arrow keys
        
        current_selection = 0
        menu_items = [
            "1. Process New Excel File",
            "2. View Database Listings",
            "3. Post Pending Listings",
            "4. Exit"
        ]
        
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # title
            title = "Facebook Marketplace Bot Manager"
            stdscr.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD | curses.color_pair(3))
            stdscr.hline(2, 0, '-', width)
            
            # status section
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status, COUNT(*) FROM listings GROUP BY status")
                stats = dict(cursor.fetchall())
            
            stdscr.addstr(4, 2, "Database Status:", curses.A_BOLD)
            stdscr.addstr(5, 4, f"Pending: {stats.get('pending', 0)}", curses.color_pair(2))
            stdscr.addstr(5, 20, f"Posted: {stats.get('posted', 0)}", curses.color_pair(1))
            stdscr.addstr(5, 35, f"Total: {sum(stats.values())}")
            
            # menu section
            stdscr.hline(7, 0, '-', width)
            
            for idx, item in enumerate(menu_items):
                if idx == current_selection:
                    stdscr.addstr(9 + idx, 2, f"-> {item}", curses.A_BOLD | curses.color_pair(1))
                else:
                    stdscr.addstr(9 + idx, 4, item, curses.color_pair(3))
            
            # help section
            stdscr.hline(14, 0, '-', width)
            stdscr.addstr(15, 2, "Navigate: ↑/↓ or [1-4] Select Option | Enter or [q] Quit", curses.color_pair(4))
            
            # handle input
            choice = stdscr.getch()
            
            if choice == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif choice == curses.KEY_DOWN and current_selection < len(menu_items) - 1:
                current_selection += 1
            elif choice == ord('\n'):  # Enter key
                if current_selection == len(menu_items) - 1:  # Exit option
                    break
                elif current_selection == 0:
                    self.select_excel_file(stdscr)
                elif current_selection == 1:
                    self.view_database(stdscr)
                elif current_selection == 2:
                    self.post_listings(stdscr)
            elif choice in [ord('1'), ord('2'), ord('3'), ord('4')]:
                selection = choice - ord('1')
                if selection == 3:  # Exit option
                    break
                elif selection == 0:
                    self.select_excel_file(stdscr)
                elif selection == 1:
                    self.view_database(stdscr)
                elif selection == 2:
                    self.post_listings(stdscr)
            elif choice == ord('q'):
                break
    
    def select_excel_file(self, stdscr):
        # enable keypad mode
        stdscr.keypad(True)
        
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        excel_files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
        
        if not excel_files:
            self.show_message(stdscr, "No Excel files found in data directory!", error=True)
            return
            
        current_selection = 0
        
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # header
            stdscr.addstr(0, 0, "Select Excel File", curses.A_BOLD | curses.color_pair(3))
            stdscr.hline(1, 0, '-', width)
            
            # file list
            for idx, file in enumerate(excel_files):
                if idx == current_selection:
                    stdscr.addstr(idx + 3, 2, "-> " + file, curses.A_BOLD | curses.color_pair(1))
                else:
                    stdscr.addstr(idx + 3, 4, file)
            
            # help text
            stdscr.hline(height-2, 0, '-', width)
            stdscr.addstr(height-1, 2, "↑/↓: Navigate | Enter: Select | q: Back", curses.color_pair(4))
            
            key = stdscr.getch()
            
            if key == curses.KEY_UP and current_selection > 0:
                current_selection -= 1
            elif key == curses.KEY_DOWN and current_selection < len(excel_files) - 1:
                current_selection += 1
            elif key == ord('\n'):  # Enter key
                selected_file = os.path.join(data_dir, excel_files[current_selection])
                self.process_excel_file(stdscr, selected_file)
                break
            elif key == ord('q'):
                break
    
    def view_database(self, stdscr):
        page = 0
        items_per_page = 15
        
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # header
            stdscr.addstr(0, 0, "Database Listings", curses.A_BOLD | curses.color_pair(3))
            stdscr.hline(1, 0, '-', width)
            
            # column headers
            stdscr.addstr(2, 2, "Item Code", curses.A_BOLD)
            stdscr.addstr(2, 15, "Description", curses.A_BOLD)
            stdscr.addstr(2, width - 25, "Status", curses.A_BOLD)
            stdscr.addstr(2, width - 15, "Created", curses.A_BOLD)
            stdscr.hline(3, 0, '-', width)
            
            # get data
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM listings")
                total_items = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT item_code, description, status, created_at 
                    FROM listings 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (items_per_page, page * items_per_page))
                listings = cursor.fetchall()
            
            # show listings
            for idx, listing in enumerate(listings):
                y_pos = idx + 4
                if y_pos < height - 3:
                    status_color = curses.color_pair(1) if listing[2] == 'posted' else curses.color_pair(2)
                    created_date = datetime.strptime(listing[3], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    
                    stdscr.addstr(y_pos, 2, f"{listing[0][:10]}")
                    stdscr.addstr(y_pos, 15, f"{listing[1][:50]}...")
                    stdscr.addstr(y_pos, width - 25, f"[{listing[2]}]", status_color)
                    stdscr.addstr(y_pos, width - 15, created_date)
            
            # footer
            stdscr.hline(height-2, 0, '-', width)
            page_info = f"Page {page + 1}/{(total_items + items_per_page - 1) // items_per_page}"
            stdscr.addstr(height-1, 2, f"↑/↓: Navigate | q: Back | {page_info}", curses.color_pair(4))
            
            key = stdscr.getch()
            if key == ord('q'):
                break
            elif key == curses.KEY_DOWN and (page + 1) * items_per_page < total_items:
                page += 1
            elif key == curses.KEY_UP and page > 0:
                page -= 1
    
    def post_listings(self, stdscr):
        page = 0
        items_per_page = 15
        selected_items = set()
        current_selection = 0
        
        # enable keypad mode
        stdscr.keypad(True)
        
        while True:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # header
            stdscr.addstr(0, 0, "Select Listings to Post", curses.A_BOLD | curses.color_pair(3))
            stdscr.hline(1, 0, '-', width)
            
            # column headers
            stdscr.addstr(2, 2, "[ ]", curses.A_BOLD)  # checkbox
            stdscr.addstr(2, 7, "Item Code", curses.A_BOLD)
            stdscr.addstr(2, 20, "Title", curses.A_BOLD)
            stdscr.addstr(2, 45, "Description", curses.A_BOLD)
            stdscr.addstr(2, width - 25, "Price", curses.A_BOLD)
            stdscr.addstr(2, width - 15, "Created", curses.A_BOLD)
            stdscr.hline(3, 0, '-', width)
            
            # get pending listings
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM listings WHERE status = 'pending'")
                total_items = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT item_code, title, description, price, created_at 
                    FROM listings 
                    WHERE status = 'pending'
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (items_per_page, page * items_per_page))
                listings = cursor.fetchall()
            
            # show listings
            for idx, listing in enumerate(listings):
                y_pos = idx + 4
                if y_pos < height - 3:
                    # arrow and checkbox
                    checkbox = "[X]" if listing[0] in selected_items else "[ ]"
                    if idx == current_selection:
                        stdscr.addstr(y_pos, 0, "-> ", curses.A_BOLD | curses.color_pair(1))
                        stdscr.addstr(y_pos, 2, checkbox, curses.A_BOLD | curses.color_pair(1))
                    else:
                        stdscr.addstr(y_pos, 2, checkbox)
                    
                    # listing details
                    created_date = datetime.strptime(listing[4], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                    price_str = f"${listing[3]:.2f}" if listing[3] else "N/A"
                    
                    # truncate strings to fit
                    item_code = listing[0][:10]
                    title = listing[1][:20] + "..." if len(listing[1]) > 20 else listing[1]
                    description = listing[2][:30] + "..." if len(listing[2]) > 30 else listing[2]
                    
                    stdscr.addstr(y_pos, 7, item_code)
                    stdscr.addstr(y_pos, 20, title)
                    stdscr.addstr(y_pos, 45, description)
                    stdscr.addstr(y_pos, width - 25, price_str)
                    stdscr.addstr(y_pos, width - 15, created_date)
            
            # footer
            stdscr.hline(height-3, 0, '-', width)
            selected_count = len(selected_items)
            status_line = f"Selected: {selected_count} | Page {page + 1}/{(total_items + items_per_page - 1) // items_per_page}"
            stdscr.addstr(height-2, 2, status_line, curses.color_pair(3))
            stdscr.addstr(height-1, 2, "↑/↓: Navigate | ←/→: Change Page | Space: Select | Enter: Post | a: Select All | q: Back", 
                         curses.color_pair(4))
            
            # handle input
            key = stdscr.getch()
            
            if key == ord('q'):
                break
            elif key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]:
                if key == curses.KEY_UP:
                    if current_selection > 0:
                        current_selection -= 1
                    elif page > 0:  # if at top of page, go to previous page
                        page -= 1
                        current_selection = items_per_page - 1
                elif key == curses.KEY_DOWN:
                    if current_selection < len(listings) - 1:
                        current_selection += 1
                    elif (page + 1) * items_per_page < total_items:  # if at bottom of page, go to next page
                        page += 1
                        current_selection = 0
                elif key == curses.KEY_LEFT and page > 0:  # previous page
                    page -= 1
                    current_selection = 0
                elif key == curses.KEY_RIGHT and (page + 1) * items_per_page < total_items:  # next page
                    page += 1
                    current_selection = 0
            elif key == ord(' '):  # Space to toggle selection
                if current_selection < len(listings):
                    item_code = listings[current_selection][0]
                    if item_code in selected_items:
                        selected_items.remove(item_code)
                    else:
                        selected_items.add(item_code)
                    # move to next item after selection
                    if current_selection < len(listings) - 1:
                        current_selection += 1
            elif key == ord('a'):  # Select all on current page
                for listing in listings:
                    selected_items.add(listing[0])
            elif key == ord('\n') and selected_items:  # Enter to post selected
                if self.confirm_post_selected(stdscr, len(selected_items)):
                    self.post_selected_listings(stdscr, selected_items)
                    break
            elif key == curses.KEY_NPAGE:  # Page Down
                if (page + 1) * items_per_page < total_items:
                    page += 1
                    current_selection = 0
            elif key == curses.KEY_PPAGE:  # Page Up
                if page > 0:
                    page -= 1
                    current_selection = 0

    def confirm_post_selected(self, stdscr, count: int) -> bool:
        height, width = stdscr.getmaxyx()
        stdscr.clear()
        msg = f"Are you sure you want to post {count} selected listings?"
        stdscr.addstr(height//2 - 2, (width - len(msg))//2, msg)
        stdscr.addstr(height//2, (width - 20)//2, "Press Y to confirm")
        stdscr.addstr(height//2 + 1, (width - 20)//2, "Press N to cancel")
        
        while True:
            choice = stdscr.getch()
            if choice in [ord('y'), ord('Y')]:
                return True
            if choice in [ord('n'), ord('N')]:
                return False

    def post_selected_listings(self, stdscr, selected_items: set):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE listings SET status = 'posted' WHERE item_code IN ({})".format(
                        ','.join('?' * len(selected_items))
                    ), 
                    tuple(selected_items)
                )
                conn.commit()
                count = cursor.rowcount
            
            self.show_message(stdscr, f"Successfully posted {count} listings!")
        except Exception as e:
            self.show_message(stdscr, f"Error posting listings: {str(e)}", error=True)
    
    def show_message(self, stdscr, message: str, error: bool = False):
        """show a message box with a message"""
        height, width = stdscr.getmaxyx()
        msg_color = curses.color_pair(2) if error else curses.color_pair(1)
        
        stdscr.clear()
        stdscr.addstr(height//2, (width - len(message))//2, message, msg_color | curses.A_BOLD)
        stdscr.addstr(height//2 + 2, (width - 20)//2, "Press any key...", curses.color_pair(4))
        stdscr.refresh()
        stdscr.getch()
    
    def process_excel_file(self, stdscr, file_path: str):
        """process excel file with progress indicator"""
        try:
            stdscr.clear()
            height, width = stdscr.getmaxyx()
            
            # show processing message
            msg = f"Processing: {os.path.basename(file_path)}"
            stdscr.addstr(height//2 - 1, (width - len(msg))//2, msg, curses.color_pair(3))
            stdscr.addstr(height//2 + 1, (width - 20)//2, "Please wait...", curses.color_pair(4))
            stdscr.refresh()
            
            # process the file
            self.bot.process_excel_file(file_path)
            
            # show success message
            self.show_message(stdscr, "File processed successfully!")
            
        except Exception as e:
            self.show_message(stdscr, f"Error: {str(e)}", error=True)