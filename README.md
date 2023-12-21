# InsightEngine

## Introduction to PDF Parsing:
- PDF documents encode data from documents as pixel data on a 2D plane (computer graphics) or using a non standard encoding scheme. As a result there is no standard format for parsing PDFs (ie. no differentation in how to process text, images, tables, etc...)
- PDF parsing is usually most efficent and accurate when parser is highly customized to a specific pdf format or set of similar documents

## High Level Design
- In the context of InsightEngine, the domain of financial reports to parse range from various canadian and american banks meaning the engine should be generalized enough to ensure a smooth automation process of PDF's to markdown
- (New Feature): HTML Parser
    - Parse tables with embedded links

## Specific Approach 
- Table parsing done entirely with Tabula-py (requires Java Installation)
- Pure text is parsed with PyMuPDF (not including tables)
- Regex expressions are used to identity parts of text which exist within tables and thus ignored while parsing for text
- Parsed Text and Tables are later joined together in the same markdown using the following logic
    - `extract_text()` function takes in two params including min_cols and min_txt
    - min_cols represents the min # of accounting values to detect before a table can be placed in text
    - min_txt represents the min # of regular text values to detect before we can reset table detection and look to add more tables
    - using both params we can accurately determine where to insert tables in the text

## Regex Explanation

1. Expression for matching number patterns commonly found in the tables of financial reports (accounting values, etc...)

```python
NUMBERS = r'^\s*(\([-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)|[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?)$'
```

Examples of matching numbers:

- 123
- 1,234
- 12,345.67
- -1,234.56
- (-789)
- (-1,234.56)

2. Expression for matching symbols found alongside accounting numbers

```python
SYMBOLS = r'^\s*[$%]'
```

Example of matching text:
- $

3. Expression for matching percentages found alongside accounting numbers
```python
PERCENTAGES = r'^\s*\d+(\.\d+)?\s*%'
```

Examples of matching numbers:
- 0.94 %
- 0.79 %
- 1.00 %

## Testing Tools

`cat output.md | wo` get # of tokens

