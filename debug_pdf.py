import pdfplumber

pdf_path = "D:/!Nextcloud SSL/Faktury/Ksiegowa/Ksiegi/LIPIEC-2025.pdf"

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[0]  # tylko pierwsza strona
    im = page.to_image(resolution=150)
    im.debug_tablefinder()
    im.save("debug_output.png")
