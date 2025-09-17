import pdfplumber
import re

def extract_pdf_data(pdf_path):
    extracted = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                print(f"[Strona {page_num}] Brak tekstu.")
                continue

            lines = text.split('\n')
            for line_num, line in enumerate(lines, start=1):
                # Pomijamy linie nagłówkowe i puste
                if not line.strip() or not re.match(r"^\d+/\d+", line):
                    continue

                # Przykład linii:
                # 1/07 1 FV/1459/25 ASWO PL KOSZTY 785 87
                parts = line.strip().split()

                if len(parts) < 6:
                    print(f"[Strona {page_num}, Linia {line_num}] Pominięto (za mało pól): {line}")
                    continue

                lp = parts[0]
                nr_dowodu = parts[2]
                opis = parts[5]

                extracted.append((lp, nr_dowodu, opis))

    print(f"Znaleziono {len(extracted)} rekordów.")
    return extracted
