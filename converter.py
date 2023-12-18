# Libraries:
import tabula
import os
import pandas as pd
import fitz
import re
import numpy as np
from unidecode import unidecode
from PyPDF2 import PdfReader
import math
import requests
from bs4 import BeautifulSoup

# Constants:
# NOTE: Regex Patterns described in readme:
# NUMBERS = r'^\s*(\([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)|[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)$'
NUMBERS = r'^\s*(\([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)|[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*$'
SYMBOLS = r'^\s*[$%]'
PERCENTAGES = r'^\s*\d+(\.\d+)?\s*%'
TAG_TO_MARKDOWN = {
    'h1': '# ',
    'h2': "## ",
    'h3': "### ",
    'h4': "#### ",
    'h5': "##### ",
    'h6': "###### "
}

class Converter:
    def __init__(self, filePath: str):
        self.pdf = filePath
        self.tables = {} # dict stores tables with page as keys
        self.text = None # Dataframe
        self.markdown_text = [] # NOTE: Change to self.markdown_text[[]]
        self.page_nums = 0

    def extract_tables(self, post_process: str):
        """
        - Gets length of PDF and extracts tables from each page
        - Saves tables and page # as dictionary
        """
        # Get PDF Length:
        # formatLog = open("tables.txt", "w", encoding="utf-8")
        reader = PdfReader(self.pdf)
        n = len(reader.pages)
        self.page_nums = n

        # Parse each page for tables --> store tables with page index
        for i in range(1, n + 1):
            tables = tabula.read_pdf(self.pdf, pages = i, stream = True)
            
            for table in tables:
                # Post-Processing:
                if post_process == "yes":
                    # For each col --> duplicate cell values that are merged across multiple rows
                    # - create new col and append new vals
                    for col in table.columns:
                        dup_val = "nan"
                        new_col = []
                        # for i, value in table[col].iteritems():
                        #     if isinstance(value, float) and math.isnan(value):
                        #         # print(value)
                        #         value = dup_val
                        #     else: dup_val = value
                        #     # print(f'Row {i}, {type(value)}: {value}')
                        #     new_col.append(value)
                        # # print('\n')
                        # table[col] = new_col # Updating entire col

                # logText = f"Page: {i}, table type: {type(table)} --> \n{table}\n----------------------------------------------------\n"
                # formatLog.write(logText)
                if i in self.tables: self.tables[i].append(table) # if existing page, append table to list
                else: self.tables[i] = [table]

        # # # Testing:
        # for k, v in self.tables.items():
        #     logText = f"Page: {k}, table type: {type(v)} --> \n{v}\n----------------------------------------------------\n"
        #     formatLog.write(logText)

        # formatLog.close() 
        return

    # Extract Text and Gather Stats
    def extract_text(self, min_cols: int, min_txt: int):
        """
        - Extracts Text
        - Generates Log of Text
        - Uses regex expressions to match for strings that would normally exist within a table
        - NOTE: Params for inserting table
            - min_cols # of columns required (table occurances) to add table meta data
            - min_txt # of regular text values required to reset table detection and allow for new detection
        - Table occurance is detected and meta data is added at page location to insert table during markdown generation
        """
        # Open PDF for reading and log for tracking stats
        pdf = fitz.open(self.pdf)
        textLog = open("textLog.txt", "w", encoding="utf-8")

        # Iterate through pages and save as blocks
        block_dict = {}
        page_num = 1 # key for dictionary

        for page in pdf:
            file_dict = page.get_text('dict') # Retrieve page as dictionary
            block = file_dict['blocks'] 
            block_dict[page_num] = block 
            page_num += 1 # increment page

        # Iterate through each block --> span --> line 
        # Create stats from text (font size, uppercase, bolding, etc...)
        rows = []

        # Declarations for tracking consecutive accounting or text occurances
        account_i = 0 # compared with min_cols
        text_i = 0 # compared with min_txt
        detection = True

        for page, blocks in block_dict.items():
            for block in blocks:
                block_no = block["number"] # text block
                if block["type"] == 0: # only wish to retrieve text
                    for line in block["lines"]:
                        for span in line["spans"]:

                            # Gather statistics --> append to dataframe for analysis and markdown generation:
                            font_size = span['size']
                            xmin, ymin, xmax, ymax = list(span["bbox"])
                            text = unidecode(span['text'])
                            span_font = span["font"]
                            is_upper = False
                            is_bold = False

                            if "bold" in span_font.lower():
                                is_bold = True
                            if re.sub("[\(\[].*?[\)\]]", "", text).isupper():
                                is_upper = True

                            # If Non Empty Text and Text is not within table --> add text
                            if text.replace(" ","") !=  "":

                                # Table Filteration Logic --> NOTE All regex stuff goes here
                                if re.search(NUMBERS, text) == None and re.search(SYMBOLS, text) == None and re.search(PERCENTAGES, text) == None:
                                    log_output = f"Page: {page}, Font Size: {font_size}, Upper: {is_upper}, Bold: {is_bold}, block number: {block_no}, Text: {text}"
                                    textLog.write(log_output + "\n")
                                    rows.append((page, xmin, ymin, xmax, ymax, text, is_upper, is_bold, span_font, font_size))
                                    text_i += 1
                                    account_i = 0

                                # Accounting Detected
                                else: 
                                    textLog.write(f"Accounting Found: {text}\n")
                                    account_i += 1
                                    text_i = 0

                            # Add Table:
                            if account_i == min_cols and detection:
                                detection = False
                                textLog.write(f"Add Table here\n")
                                rows.append((page, xmin, ymin, xmax, ymax, "<table>", is_upper, is_bold, span_font, font_size))
                        
                            # Reset Table detection:
                            if text_i == min_txt and not detection:
                                detection = True
                                # textLog.write(f"Look for table again\n")


        # Create text dataframe and close files:
        self.text = pd.DataFrame(rows, columns=['page', 'xmin','ymin','xmax','ymax', 'text', 'is_upper','is_bold','span_font', 'font_size'])
        textLog.close()
        pdf.close()
        return
    
    def generate_headers(self):
        """
        - Generate font frequencies for formatting text
        - Collect font frequencies
        """
        # formatLog = open("formatLog.txt", "w", encoding="utf-8")

        # Create (Rounded) font freqs and reassign to column:
        rounded_font = []

        for _, row in self.text.iterrows():
            font_size = round(row.font_size)
            rounded_font.append(font_size)

        self.text["font_size"] = rounded_font
        font_freq = self.text["font_size"].value_counts().sort_index(ascending=False)
        # print(f"Type: {type(font_freq)}:\n{font_freq}")
        
        # print("------------------------")

        # Assign headers according to font freq:
        header = {}
        idx = 0 # NOTE: Collecting sub fonts for additional formatting (s1, s2, etc...)
        p_size = font_freq.idxmax() # font size with most occurances --> this will be general paragraph font

        for font in font_freq.index:
            idx += 1
            if font == p_size:
                idx = 0 # reset the index --> switching to sub fonts
                header[font] = "p"
            if font > p_size: header[font]= "h{0}".format(idx)
            if font < p_size: header[font]= "s{0}".format(idx)

        # print(header)
        # print("------------------------")

        # Assign tags to text dataframe --> NOTE: append each tag column to df (headers, bullets, lists, etc...):
        headers = [] # header tags (h1, h2, etc...)
        for _, row in self.text.iterrows():

            # Headers:
            font_size = row.font_size
            tag = header.get(font_size)
            headers.append(tag)

        self.text["headers"] = headers 

        # formatLog.close()
        return

    def generate_markdown(self):
        """
            
        """

        formatLog = open("formatLog.txt", "w", encoding="utf-8")

        # Create markdown text
        for _, row in self.text.iterrows():
            text = row.text
            page = row.page
            header = row.headers

            # Insert table --> pop 
            # NOTE: this logic may create issue with dumping all pages at end of page either way (ie. no tables left)
            if text == "<table>":
                # If page and table exists in tables dict --> pop it
                if page in self.tables and self.tables[page]: 
                    table = self.tables[page].pop(0)
                    # formatLog.write(f"Page: {page}, Type Table {type(table)}")
                    if table is not None:
                        # formatLog.write(f"\nPage: {page}, type of table: {type(table)} --> \n{table}\n-----------------------------------\n")
                        m_table = table.to_markdown()
                        self.markdown_text.append(m_table)             

            # Insert Text as header
            elif "h" in header:
                m_header = TAG_TO_MARKDOWN.get(header)
                m_text = f"\n{m_header}{text}\n" 
                self.markdown_text.append(m_text)

            # Insert text w/ bullet/list:

            # Insert text as reg
            else: self.markdown_text.append(text)
            self.markdown_text.append("\n") # new line char for markdown formatting     
   
        # Dumping left over tables
        for i in range(1, self.page_nums + 1):
            if i in self.tables and self.tables[i]: 
                table = self.tables[i].pop(0)
                if table is not None:
                    m_table = table.to_markdown()
                    self.markdown_text.append(m_table)
                    self.markdown_text.append("\n")
                    self.markdown_text.append("\n")   
        
        # Output to markdown file
        file = open("output.md", "w", encoding="utf-8")
        # for line in self.markdown_text:
        #     file.write(f"{line}")
        for line in self.markdown_text:
            file.write(f"{line}")

        formatLog.close()
        file.close()
        
        return
    
    def get_markdown(self):
        return self.markdown_text
    
class HTML_Converter:
    def __init__(self, path: str):
        self.page = path
        self.tables = []
    
    def parse(self):
        formatLog = open("tables.txt", "w", encoding="utf-8")
        table_index = 1

        with open(self.page) as fp:
            soup = BeautifulSoup(fp, 'html.parser')
            tables = soup.find_all("table")
            for table in tables:
                t_headers = [] # table header
                t_data = [] # table data
                for tbody in table.find_all('tbody'):
                    rows = tbody.find_all("tr") # Table Rows
    
                    # Append first row as table headers
                    for headers in rows[0]:
                        text = HTML_Converter.clean_text(headers.get_text())
                        t_headers.append(text)

                    # Loop through each table row and append as row data
                    for i in range(1, len(rows)):
                        row_data = []
                        cols = rows[i].find_all("td") # cols is a list of the cells for the row
                        if (cols != []): # if cols not empty
                            for cell in cols: # iterates through each cell in that row
                                cell_text = "" # to be appended to row_data

                                # If cell exists as bullet list --> parse as so
                                cell_vals = cell.find_all("li")
                                if cell_vals: 
                                    for val in cell_vals:
                                        text = HTML_Converter.clean_text(val.get_text()) # reg text
                                        link = val.find("a", href=True) 
                                        if link: 
                                            url = link.get('href')
                                            cell_text += f"[{text}]({url})\n" # keep links if exist
                                        else: cell_text += f"{text}\n" # else keep just text

                                # Else --> append as reg text
                                else: 
                                    text = HTML_Converter.clean_text(cell.get_text())
                                    link = cell.find("a", href=True)
                                    if link:
                                        url = link.get("href")
                                        cell_text = f"[{text}]({url})\n" # keep links if exist
                                    else: cell_text = f"{text}\n" # else keep just text

                                # append to rows
                                row_data.append(cell_text)
                        t_data.append(row_data)

                # Create DF:
                if len(t_headers) > 0: 
                    df = pd.DataFrame(t_data, columns=t_headers)
                    df.to_markdown(os.path.join("friday_test", f"table_{table_index}.md"), index = False)

                    logText = f"Table: {df}\n"
                    formatLog.write(logText)
                table_index += 1
        formatLog.close()
        return
    
    @staticmethod
    def clean_text(text: str):
        return text.encode('ascii', 'ignore').decode("utf-8").lstrip("\n ")

if __name__ == "__main__":
    KC = HTML_Converter("Compass Central.html")
    KC.parse()