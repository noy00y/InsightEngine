# Libraries:
import tabula
import os
import pandas as pd
import fitz
import re
import numpy as np
from unidecode import unidecode

# Regex Patterns:
NUMBERS = r'^\s*(\([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)|[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)$'

class Converter:
    def __init__(self, filePath: str):
        self.pdf = filePath
        self.tables = None
        self.text = None # Dataframe

    # Extract Text and Gather Stats
    def create_text(self):
        # Open PDF for reading and log for tracking stats
        pdf = fitz.open(self.pdf)
        statsLog = open("statsLog.txt", "w", encoding="utf-8")

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
        for page, blocks in block_dict.items():
            for block in blocks:
                block_no = block["number"] # text block
                if block["type"] == 0: # only wish to retrieve text
                    for line in block["lines"]:
                        for span in line["spans"]:
                            # Gather statistics --> append to dataframe for analysis:
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

                                # Table Filteration Logic:
                                # NOTE: All regex stuff goes here
                                if re.search(NUMBERS, text) == None:
                                    log_output = f"Page: {page}, Font Size: {font_size}, Upper: {is_upper}, Bold: {is_bold}, block number: {block_no}, Text: {text}"
                                    statsLog.write(log_output + "\n")
                                    rows.append((xmin, ymin, xmax, ymax, text, is_upper, is_bold, span_font, font_size))

        # Close files and create text dataframe:
        statsLog.close()
        pdf.close()
        self.text = pd.DataFrame(rows, columns=['xmin','ymin','xmax','ymax', 'text', 'is_upper','is_bold','span_font', 'font_size'])
        return
    
    # Generate Scores from text for formatting
    def generate_format(self):

        return

    def extract_tables(self):

        return
    
    def generate_markdown(self):

        return
