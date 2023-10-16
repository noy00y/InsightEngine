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
        self.text = None

        # Logs:

    # Extract Text and Gather Stats
    def extract_text(self):
        pdf = fitz.open(self.pdf)
        statsLog = open("statsLog.txt", "w", encoding="utf-8")

        return
    
    def generate_format(self):

        return

    def extract_tables(self):

        return
    
    def generate_markdown(self):

        return
