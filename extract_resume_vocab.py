import fitz 
import re
import os
import pandas as pd

def split_pdf_left_right(pdf_path):
    left_text = []
    right_text = []

    with fitz.open(pdf_path) as doc:
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            page_width = page.rect.width
            mid_x = page_width / 3 

            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span["text"].strip()
                        if not text:
                            continue
                        x = span["bbox"][0]
                        if x < mid_x:
                            left_text.append(text)
                        else:
                            right_text.append(text)

    return "\n".join(left_text), "\n".join(right_text)

def extract_text_by_section(pdf_path, category = None):
    sections = {
        "Category": category, 
        "Role": "",
        "Name": "",
        "Top Skills": "",
        "Summary": "",
        "Experience": "",
        "Education": "",
        "Languages": "",
        "Certifications": "",
        "Honors-Awards": "",
        "Contact": ""
    }

    try:
        left_text, right_text = split_pdf_left_right(pdf_path)

        left_patterns = {
            "Contact": r"(?:Contact|Coordonnées)\n([\s\S]+?)(?=\n(?:Top Skills|Principales compétences)|\n(?:Languages|Langues)|\n(?:Certifications|Certificats)|\n(?:Honors-Awards|Distinctions)|\n(?:Publications)|$)",
            "Top Skills": r"(?:Top Skills|Principales compétences)\n([\s\S]+?)(?=\n(?:Languages|Langues)|\n(?:Certifications|Certificats)|\n(?:Honors-Awards|Distinctions)|\n(?:Publications)|$)",
            "Languages": r"(?:Languages|Langues)\n([\s\S]+?)(?=\n(?:Certifications|Certificats)|\n(?:Honors-Awards|Distinctions)|\n(?:Publications)|$)",
            "Certifications": r"(?:Certifications|Certificats)\n([\s\S]+?)(?=\n(?:Honors-Awards|Distinctions)|\n(?:Publications)|$)",
            "Honors-Awards": r"(?:Honors-Awards|Distinctions)\n([\s\S]+?)(?=\n(?:Publications)|$)",
            "Publications": r"(?:Publications)\n([\s\S]+)"
        }

        for key, pattern in left_patterns.items():
            match = re.search(pattern, left_text, re.IGNORECASE)
            sections[key] = match.group(1).strip() if match else "N/A"
            
        lines = right_text.split("\n")
        if lines:
            sections["Name"] = lines[0].strip()
        if len(lines) > 1:
            sections["Role"] = lines[1].strip()

        right_patterns = {
            "Summary": r"(?:Summary|Résumé)\n([\s\S]+?)(?=\n(?:Experience|Expérience)|\n(?:Education|Éducation)|$)",
            "Experience": r"(?:Experience|Expérience)\n([\s\S]+?)(?=\n(?:Education|Éducation)|$)",
            "Education": r"(?:Education|Éducation|Formation)\n([\s\S]+)"
        }

        for key, pattern in right_patterns.items():
            match = re.search(pattern, right_text, re.IGNORECASE)
            sections[key] = match.group(1).strip() if match else "N/A"

    except Exception as e:
        print(f"Lỗi khi xử lý file {pdf_path}: {e}")

    return sections

def convert_pdfs_to_csv(dataset_folder):
    data = []

    for category in os.listdir(dataset_folder):
        category_path = os.path.join(dataset_folder, category)
        if os.path.isdir(category_path):
            for filename in os.listdir(category_path):
                if filename.endswith(".pdf"):
                    pdf_path = os.path.join(category_path, filename)
                    info = extract_text_by_section(pdf_path, category)
                    info["Filename"] = filename
                    data.append(info)

    df = pd.DataFrame(data)
    # df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    # print(f"Đã chuyển đổi thành công và lưu vào {output_csv}")
    return df

