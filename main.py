from converter import Converter

td_report = Converter("Reports\Bank Of America\The Supplemental Information_2Q23_ADA.pdf")
td_report.extract_tables()
td_report.extract_text(min_cols = 2, min_txt=2) 
td_report.generate_headers()
td_report.generate_markdown()
# td_report.test("test_boc")