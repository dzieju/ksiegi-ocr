from pdf2image import convert_from_path
from PIL import Image, ImageTk, ImageDraw
import tkinter as tk
from tkinter import ttk
import pytesseract

PDF_PATH = "zakupy7.pdf"

# Import poppler utilities for automatic path detection
try:
    from tools.poppler_utils import get_poppler_path, check_pdf_file_exists
    POPPLER_PATH = get_poppler_path()
    if POPPLER_PATH:
        print(f"PDF crop tool: Poppler detected at: {POPPLER_PATH}")
    else:
        print("PDF crop tool: Warning: Poppler not detected, using fallback path")
        POPPLER_PATH = r"C:\poppler\Library\bin"  # Fallback
        
# Import poppler utilities for automatic path detection
try:
    from tools.poppler_utils import get_poppler_path, check_pdf_file_exists
    POPPLER_PATH = get_poppler_path()
    if POPPLER_PATH:
        print(f"PDF crop tool: Poppler detected at: {POPPLER_PATH}")
    else:
        print("PDF crop tool: Warning: Poppler not detected, using fallback path")
        POPPLER_PATH = r"C:\poppler\Library\bin"  # Fallback
        
    # Check if PDF file exists before proceeding
    pdf_exists, pdf_message = check_pdf_file_exists(PDF_PATH)
    if not pdf_exists:
        print(f"PDF file check failed: {pdf_message}")
        exit(1)
    else:
        print(f"PDF file validated: {pdf_message}")
        
except ImportError as e:
    print(f"PDF crop tool: Failed to import poppler_utils, using fallback path: {e}")
    POPPLER_PATH = r"C:\poppler\Library\bin"  # Fallback

# Import tesseract utilities for automatic path detection
try:
    from tools.tesseract_utils import get_tesseract_path
    TESSERACT_PATH = get_tesseract_path()
    if TESSERACT_PATH:
        print(f"PDF crop tool: Tesseract detected at: {TESSERACT_PATH}")
    else:
        print("PDF crop tool: Warning: Tesseract not detected, using fallback path")
        TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Fallback
except ImportError as e:
    print(f"PDF crop tool: Failed to import tesseract_utils, using fallback path: {e}")
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Fallback

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Współrzędne cropa:
left, right = 503, 771
top, bottom = 332, 2377

# Wczytaj pierwszą stronę PDF jako obrazek w 300dpi
images = convert_from_path(PDF_PATH, dpi=300, poppler_path=POPPLER_PATH)
img = images[0]
width, height = img.size
print(f"Obrazek ma rozmiar: {width}x{height} px (DPI=300)")

def draw_rectangle_on_img(img, l, t, r, b):
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)
    draw.rectangle([l, t, r, b], outline="red", width=4)
    return img_copy

img_for_draw = draw_rectangle_on_img(img, left, top, right, bottom)

root = tk.Tk()
root.title("Znajdź współrzędne kolumny PDF (DPI=300)")

# Frame na scrollable canvas
frame_canvas = tk.Frame(root)
frame_canvas.pack(fill=tk.BOTH, expand=True)

# Scrollbary
vbar = tk.Scrollbar(frame_canvas, orient=tk.VERTICAL)
hbar = tk.Scrollbar(frame_canvas, orient=tk.HORIZONTAL)

# Canvas z paskami przewijania
canvas = tk.Canvas(frame_canvas,
                   width=800, height=600,
                   yscrollcommand=vbar.set,
                   xscrollcommand=hbar.set,
                   scrollregion=(0,0,width,height))

vbar.config(command=canvas.yview)
hbar.config(command=canvas.xview)
vbar.pack(side=tk.RIGHT, fill=tk.Y)
hbar.pack(side=tk.BOTTOM, fill=tk.X)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tk_img = ImageTk.PhotoImage(img_for_draw)
img_id = canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)

coord_label = tk.Label(root, text="Kliknij na obraz, by zobaczyć współrzędne (x, y)")
coord_label.pack()

def on_click(event):
    x = int(canvas.canvasx(event.x))
    y = int(canvas.canvasy(event.y))
    coord_label.config(text=f"Klik: x={x}, y={y}")
    print(f"Kliknąłeś: x={x}, y={y}")

canvas.bind("<Button-1>", on_click)

def show_crop():
    crop = img.crop((left, top, right, bottom))
    crop.show()
    crop.save("debug_crop.png")
    print("Crop zapisany do debug_crop.png")
    # --- Tylko czysty OCR ---
    ocr_text = pytesseract.image_to_string(crop, lang='pol+eng')
    print("==== OCR SUROWY ====")
    print(ocr_text)
    print("====================")
    lines = [l.strip() for l in ocr_text.split('\n') if l.strip()]
    for i, line in enumerate(lines):
        print(f"OCR linia {i+1}: {line}")

btn_crop = tk.Button(root, text="Pokaż wycinek cropa, zapisz i OCR", command=show_crop)
btn_crop.pack()

def update_crop():
    global left, right, top, bottom, tk_img, img_for_draw, img_id
    try:
        l = int(entry_left.get())
        r = int(entry_right.get())
        t = int(entry_top.get())
        b = int(entry_bottom.get())
        img_for_draw = draw_rectangle_on_img(img, l, t, r, b)
        tk_img = ImageTk.PhotoImage(img_for_draw)
        canvas.itemconfig(img_id, image=tk_img)
        print(f"Nowe wartości: left={l}, right={r}, top={t}, bottom={b}")
    except Exception as e:
        print("Błąd w polach współrzędnych:", e)

frame = tk.Frame(root)
frame.pack()

tk.Label(frame, text="left:").grid(row=0, column=0)
entry_left = tk.Entry(frame, width=5)
entry_left.insert(0, str(left))
entry_left.grid(row=0, column=1)

tk.Label(frame, text="right:").grid(row=0, column=2)
entry_right = tk.Entry(frame, width=5)
entry_right.insert(0, str(right))
entry_right.grid(row=0, column=3)

tk.Label(frame, text="top:").grid(row=0, column=4)
entry_top = tk.Entry(frame, width=5)
entry_top.insert(0, str(top))
entry_top.grid(row=0, column=5)

tk.Label(frame, text="bottom:").grid(row=0, column=6)
entry_bottom = tk.Entry(frame, width=5)
entry_bottom.insert(0, str(bottom))
entry_bottom.grid(row=0, column=7)

btn_update = tk.Button(frame, text="Aktualizuj crop", command=update_crop)
btn_update.grid(row=0, column=8, padx=10)

canvas.xview_moveto(0)
canvas.yview_moveto(0)

root.mainloop()