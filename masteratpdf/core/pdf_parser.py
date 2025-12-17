import fitz

def extract_all(pdf_path: str):
    doc = fitz.open(pdf_path)
    data = {"pages": [], "images": [], "links": [], "fonts": [], "toc": doc.get_toc()}
    for page_num, page in enumerate(doc, start=1):
        text_dict = page.get_text("dict")
        images = page.get_image_info(xrefs=True)
        links = page.get_links()
        data["pages"].append({"number": page_num, "text_dict": text_dict})
        data["images"].extend(images)
        data["links"].extend(links)
    doc.close()
    return data