from pypdf import PdfReader
import sys

def read_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        with open("pdf_out.txt", "a", encoding="utf-8") as f:
            f.write(f"--- {file_path} ---\n")
            f.write(text + "\n")
    except Exception as e:
        with open("pdf_out.txt", "a", encoding="utf-8") as f:
            f.write(f"Error reading {file_path}: {e}\n")

if __name__ == "__main__":
    import os
    if os.path.exists("pdf_out.txt"):
        os.remove("pdf_out.txt")
    read_pdf(r"d:\mum_hacks practice\New folder\recursion 7.0 ppt.pdf")
    read_pdf(r"d:\mum_hacks practice\New folder\Arogya_Ai_Project_Brief_v2.pdf")
