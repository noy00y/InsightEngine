from converter import Converter

td_report = Converter("Reports\TD\q323financials-en.pdf")
td_report.extract_text()
# td_report.test()
td_report.generate_headers()
td_report.generate_markdown()