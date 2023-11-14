# InsightEngine

## High Level Design

- Table parsing done entirely with Tabula-py (requires Java Installation)
- Pure text is parsed with PyMuPDF (not including tables)
- Regex expressions are used to identity parts of text which exist within tables and thus ignored while parsing for text
- Parsed Text and Tables are later joined together in the same markdown

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

Examples of matching numbers:

- $
- %

## Testing Tools

`cat output.md | wo` get # of tokens



- go thru docs to solve bugs --> github issues
- how other ppl solved it (table headers used for placement) --> docs, github issues ,stackoverflow
