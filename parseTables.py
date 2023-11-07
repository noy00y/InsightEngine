import tabula
import os
import pandas as pd

# read PDF file and extract all the tables
tables = tabula.read_pdf("Reports\TD\q323financials-en.pdf", pages="all")

# save them in a folder:
folder_name = "tables_output"
if not os.path.isdir(folder_name):
    os.mkdir(folder_name)

# iterate over extracted tables and export as md files:
for i, table in enumerate(tables, start=1):
    # df = table.dropna(subset=[table.columns[0]]) # drop rows that have first column as NAN
    table.to_markdown(os.path.join(folder_name, f"table_{i}.md"), index=False)