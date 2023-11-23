from converter import Converter

td_report = Converter("Reports\Bank Of America\The Supplemental Information_2Q23_ADA.pdf")
# td_report.extract_tables("BOC")
# td_report.extract_text()
# td_report.generate_headers()
# td_report.generate_markdown()
# td_report.test("test_boc")
td_report.e_tables("adsl;kfj")