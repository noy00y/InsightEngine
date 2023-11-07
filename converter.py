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
# NUMBERS = r'^\s*(\([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)|[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)$'
NUMBERS = r'^\s*(\([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)|[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*$'
SYMBOLS = r'^\s*[$%]'
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
        self.tables = None
        self.text = None # Dataframe
        self.markdown_text = []

    def extract_tables(self, t_folder: str):
        self.tables = tabula.read_pdf(self.pdf, pages = "all")
        
        # Output Tables
        if not os.path.isdir(t_folder):
            os.mkdir(t_folder)
        
        for i, table in enumerate(self.tables, start = 1):
            table.to_markdown(os.path.join(t_folder, f"table_{i}.md"), index=False)

        return

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

                                else: textLog.write(f"Accounting Found: {text}\n")

        # Create text dataframe and close files:
        self.text = pd.DataFrame(rows, columns=['xmin','ymin','xmax','ymax', 'text', 'is_upper','is_bold','span_font', 'font_size'])
        textLog.close()
        pdf.close()
        return
    
    def generate_headers(self):
        """
        - Generate font frequencies for formatting text
        - Collect font frequencies
        """
        formatLog = open("formatLog.txt", "w", encoding="utf-8")

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

        formatLog.close()
        return

    def generate_markdown(self):

        # Create markdown text
        for _, row in self.text.iterrows():
            text = row.text
            header = row.headers

            if "h" in header:
                m_header = TAG_TO_MARKDOWN.get(header)
                m_text = f"\n{m_header}{text}\n" 
                self.markdown_text.append(m_text)
            else: self.markdown_text.append(text)
            self.markdown_text.append("\n")
    
        # Output to markdown file
        file = open("output.md", "w", encoding="utf-8")
        for line in self.markdown_text:
            # print(line)
            file.write(f"{line}")
            # file.write(f"{line}\n")

        file.close()
        return
    
    def test(self):

        return
    


