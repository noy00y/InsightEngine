# Libraries:
import tabula
import os
import pandas as pd
import fitz
import re
import numpy as np
from unidecode import unidecode

# Constants:
# NOTE: Regex Patterns described in readme:
NUMBERS = r'^\s*(\([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)|[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)$'
SYMBOLS = r'^\s*[$%]'
TAG_TO_HEADER = {
    'h1': '# ',
    'h2': "## ",
    'h3': "### ",
    'h4': "#### ",
    'h5': '##### ',
    'h6': '###### '
}

class Converter:
    def __init__(self, filePath: str):
        self.pdf = filePath
        self.tables = None
        self.text = None # Dataframe
        self.output = []

    # Extract Text and Gather Stats
    def extract_text(self):
        """
        - Extracts Text
        - Generates Log
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
                                if re.search(NUMBERS, text) == None and re.search(SYMBOLS, text) == None:
                                    log_output = f"Page: {page}, Font Size: {font_size}, Upper: {is_upper}, Bold: {is_bold}, block number: {block_no}, Text: {text}"
                                    textLog.write(log_output + "\n")
                                    rows.append((xmin, ymin, xmax, ymax, text, is_upper, is_bold, span_font, font_size))

        # Create text dataframe and close files:
        self.text = pd.DataFrame(rows, columns=['xmin','ymin','xmax','ymax', 'text', 'is_upper','is_bold','span_font', 'font_size'])
        textLog.close()
        pdf.close()
        return
    
    def generate_format(self):
        """
        - Generate font frequencies for formatting text
        """
        formatLog = open("formatLog.txt", "w", encoding="utf-8")
        span_scores = [] # collect font sizes as scores
        special = '[(_:/,#-%\=@)]'
        for _, row in self.text.iterrows():
            score = round(row.font_size) # round font size
            text = row.text
            if not re.search(special, text): # if text is not special chars
                if row.is_bold: score += 1  # if bold or uppercase --> increase score
                if row.is_upper: score += 1
            # print(f"Score: {score}")
            span_scores.append(score)

        # Gather scores (font) and score freq (counts) --> store in score dict
        values, counts = np.unique(span_scores, return_counts = True)
        style_dict = {} # holds frequency for each font size

        for value, count in zip(values, counts):
            style_dict[value] = count
        sorted(style_dict.items(), key=lambda x: x[1])

        # Create Markdown font tags:
        p_size = max(style_dict, key=style_dict.get) # get font_size with most occurance --> this will be general paragraph font
        idx = 0 # used for creating specific header or paragraph font format
        tag = {} 

        for size in sorted(values, reverse=True):
            idx += 1 # 
            if size == p_size:
                idx = 0
                tag[size] = "p" # regular font
            if size > p_size: tag[size] = 'h{0}'.format(idx) # font size larger then avg --> header font
            if size < p_size: tag[size] = 's{0}'.format(idx) # font size smaller then avg --> small font


        # Assign Tags to original text dataframe:
        span_tags = [tag[score] for score in span_scores]
        self.text["tag"] = span_tags

        # Create Header and Text 
        for index, row in self.text.iterrows():
            text = row.text
            tag = row.tag
            if 'h' in tag:
                header = TAG_TO_HEADER.get(tag)
                header_output = f"{header}{text}"
                self.output.append(header_output)
            self.output.append(text)

        formatLog.close()
        return

    def extract_tables(self):

        

        return
    
    def generate_markdown(self):
    
        file = open("output.md", "w", encoding="utf-8")

        for line in self.output:
            file.write(f"{line}\n")
        
        file.close()
        return
    


