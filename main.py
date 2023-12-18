from converter import Converter
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

# Create MarkDown PDF
td_report = Converter("Reports\CIBC\Compass Central.pdf")
td_report.extract_tables(post_process="yes")
td_report.extract_text(min_cols = 2, min_txt=2) 
td_report.generate_headers()
td_report.generate_markdown()

# text_list = td_report.get_markdown()
# text = ", ".join(text_list)
# # print(text)

# # Create Chunks
# headers_to_split_on = [
#     ("#", "Header 1"),
#     ("##", "Header 2"),
#     ("###", "Header 3"),
# ]

# markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

# md_header_splits = markdown_splitter.split_text(text)
# # print(md_header_splits)

# chunk_size = 1000
# chunk_overlap = 30
# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size=chunk_size, chunk_overlap=chunk_overlap
# )

# # Split
# splits = text_splitter.split_documents(md_header_splits)
# print(splits[150])