import fitz
import base64

def pdf_to_images(pdf_bytes: bytes, max_pages: int = 15):
    """
    Renders PDF pages to base64 JPEG images for high speed & low payload size.
    """
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for index, page in enumerate(document):
        if index >= max_pages:
            break
        # 2.0x resolution gives ~150 DPI, ultra crisp for handwriting & mathematical diagrams
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        image_bytes = pix.tobytes("jpeg", jpg_quality=92)
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        pages.append({
            "page": index + 1,
            "image": image_base64,
            "width": pix.width,
            "height": pix.height
        })

    return pages
