import pdfplumber

pdf_path = "ścieżka/do/twojego/pliku.pdf"  # np. "C:/Users/Biuro/Documents/faktury.pdf"
numery_faktur = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        table = page.extract_table()
        if table:
            headers = table[0]
            try:
                idx = headers.index("Nr dowodu księgowego")
                for row in table[1:]:
                    numer = row[idx]
                    if numer:
                        numery_faktur.append(numer)
            except ValueError:
                continue

print("Odczytane numery faktur:")
for numer in numery_faktur:
    print(numer)
