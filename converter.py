# Libraries:
import tabula
import os
import pandas as pd
import fitz
import re
import numpy as np
from unidecode import unidecode
from PyPDF2 import PdfReader

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
        self.markdown_text = []

    def extract_tables(self):

        # Get PDF Length:
        formatLog = open("formatLog.txt", "w", encoding="utf-8")
        reader = PdfReader(self.pdf)
        n = len(reader.pages)

        # Parse each page for tables --> store tables with page index
        for i in range(1, n + 1):
            tables = tabula.read_pdf(self.pdf, pages = i, stream = True)
            # print(f"Page: {i} --> {len(tables)}")
            
            for table in tables:
                if i in self.tables: 
                    self.tables[i].append(table) # if existing table, add more to list
                else: 
                    self.tables[i] = table

        print(len(self.tables))    

        # for k, v in self.tables.items():
        #     print(f"Page: {k} w/ {len(v)} tables")

        # print(self.tables[28])

        #     # Output Tables
        #     if not os.path.isdir(t_folder):
        #         os.mkdir(t_folder)
            
        #     for i, table in enumerate(self.tables, start = 1):
        #         table.to_markdown(os.path.join(t_folder, f"table_{i}.md"), index=False)

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

        formatLog = open("tables.txt", "w", encoding="utf-8")

        #     # Output Tables
        #     if not os.path.isdir(t_folder):
        #         os.mkdir(t_folder)
            
        #     for i, table in enumerate(self.tables, start = 1):
        #         table.to_markdown(os.path.join(t_folder, f"table_{i}.md"), index=False)


        # Create markdown text
        for _, row in self.text.iterrows():
            text = row.text
            page = row.page
            header = row.headers

            # Insert table --> pop 
            if text == "<table>":
                # print(text)
                table = self.tables.popitem()
                formatLog.write(f"\nPage: {page}, Type: {type(table)}\n--------------------\n{table}\n")
                # if table is not None:
                #     m_table = table.to_markdown()
                #     # print(m_table)
                #     formatLog.write(f"\nPage: {page}, Type: {type(table)}\n--------------------\n{table}\n")
                #     self.markdown_text.append(m_table)

            elif "h" in header:
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

        formatLog.close()
        file.close()
        return
    
    def test(self, t_folder: str):
        

        return
    


