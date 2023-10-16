# Libraries:
import fitz
import pandas as pd
import re
import numpy as np
from unidecode import unidecode
import os

# Regex Patterns:
# NOTE: Regex Patterns Explained in ReadME
NUMBERS = r'^\s*(\([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)|[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)$'

# few examples what this regex expression returns
# EG.
# 100,000
# dev branch --> for code reviews
# markdown post processor
# backup
# moving forward --> hold on overall, continue parser

# Driver Code:
if __name__ == "__main__":
    pdf = fitz.open("./PDFs/TD/q323shareholders.pdf")
    file = open("output.md", "w", encoding = "utf-8")
    log = open("log.txt", "w", encoding = "utf-8")

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
                            if re.search(NUMBERS, text) == None:
                                log_output = f"Page: {page}, Font Size: {font_size}, Upper: {is_upper}, Bold: {is_bold}, block number: {block_no}, Text: {text}"
                                log.write(log_output + "\n")
                                rows.append((xmin, ymin, xmax, ymax, text, is_upper, is_bold, span_font, font_size))
            # print("------------------------------------")

    text_df = pd.DataFrame(rows, columns=['xmin','ymin','xmax','ymax', 'text', 'is_upper','is_bold','span_font', 'font_size'])

    # Create Scores --> used for formatting text in markdown:
    span_scores = []
    special = '[(_:/,#%\=@)]'

    for index, row in text_df.iterrows():
        score = round(row.font_size)
        text = row.text
        if not re.search(special, text): # if text is not special chars
            if row.is_bold: score += 1  # if bold or uppercase --> increase score
            if row.is_upper: score += 1
        # print(f"Score: {score}")
        span_scores.append(score)

    # Gather scores and score freq (counts) and create score dict
    values, counts = np.unique(span_scores, return_counts = True)
    # print(f"Values: {values}, Counts: {counts}")

    style_dict = {}
    for value, count in zip(values, counts):
        style_dict[value] = count
    sorted(style_dict.items(), key=lambda x: x[1])
    # print(style_dict)

    # Create markdown font tags 
    p_size = max(style_dict, key=style_dict.get) # get font_size with most occurance --> this will be general paragraph font
    idx = 0 # used for creating specific header or paragraph font format
    tag = {}

    for size in sorted(values, reverse = True):
        # print(f"Size: {size}, idx: {idx}")
        idx += 1 # 
        if size == p_size:
            idx = 0
            tag[size] = "p" # regular font
        if size > p_size: tag[size] = 'h{0}'.format(idx) # font size larger then avg --> header font
        if size < p_size: tag[size] = 's{0}'.format(idx) # font size smaller then avg --> small font
    
    # Assign tags to original text_df
    span_tags = [tag[score] for score in span_scores]
    text_df['tag'] = span_tags

    # Divide Content into lists:
    heading_list = []
    text_list = []
    tmp_list = []

    tag_to_header = {
        'h1': '# ',
        'h2': "## ",
        'h3': "### ",
        'h4': "#### ",
        'h5': '##### ',
        'h6': '###### '
    }

    # Filtering Logic
    for index, row in text_df.iterrows():
        text = row.text
        tag = row.tag
        # print(f"Tag: {tag}, text: {text}")
        if 'h' in tag:
            # print(f"Heading: {text}, Tag: {tag}")
            header_style = tag_to_header.get(tag)
            heading_list.append(f'{header_style}{text}')
            text_list.append('\n'.join(tmp_list))
            tmp_list = []

        else: tmp_list.append(text)
    
    text_list.append('\n'.join(tmp_list))
    text_list = text_list[1:]
    text_df = pd.DataFrame(zip(heading_list, text_list),columns=['heading', 'content'])

    # newlog = open("newlog.txt", "w", encoding = "utf-8")

    # Output to MD:
    for index, row in text_df.iterrows():
        heading = row['heading']
        content = row['content']
        file.write(f'{heading}\n{content}\n\n')

    # Close all Files
    pdf.close()
    file.close()
    log.close()
    # newlog.close()