# Enhanced Mail Search UI Mockup

## New User Interface Layout

```
┌─ Księga Przychodów i Rozchodów ──────────────────────────────────────────────────┐
│  ┌─ Konfiguracja poczty ─┐  ┌─ Przeszukiwanie Poczty ─┐                         │
│  │                       │  │                         │                         │
│  └───────────────────────┘  └─────────────────────────┘                         │
│                                                                                  │
│                       Przeszukiwanie Poczty                                     │
│                                                                                  │
│  Folder przeszukiwania:     [Skrzynka odbiorcza                    ]            │
│  Co ma szukać w temacie:    [faktura                               ]            │
│  Nadawca maila:             [                                      ]            │
│                                                                                  │
│  ☐ Tylko nieprzeczytane     ☑ Tylko z załącznikami                             │
│                                                                                  │
│  Nazwa załącznika:          [pdf                                   ]            │
│  Rozszerzenie załącznika:   [pdf                                   ]            │
│                                                                                  │
│  Okres wiadomości:                                                               │
│  ○ Wszystkie  ● Ostatni miesiąc  ○ Ostatnie 3 miesiące  ○ Ostatnie 6 miesięcy │
│                                                                                  │
│       [Rozpocznij wyszukiwanie]      Znaleziono: 45 wiadomości                  │
│                                                                                  │
│ ┌── Wyniki wyszukiwania ────────────────────────────────────────────────────────┐│
│ │ Data         │ Nadawca              │ Temat                    │Status│Zał. ││
│ │─────────────┼──────────────────────┼─────────────────────────┼──────┼─────││
│ │2025-09-20 14│supplier@company.pl   │Faktura VAT 2025/09/156  │Przec. │  2  ││
│ │2025-09-19 11│billing@service.com   │Invoice #INV-2025-789    │Niepr. │  1  ││
│ │2025-09-18 16│accounting@firm.pl    │Račun 2025/456           │Przec. │  3  ││
│ │2025-09-17 09│office@supplier.com   │Bill #2025-Q3-789        │Niepr. │  1  ││
│ │2025-09-16 13│finance@company.com   │Faktura proforma 2025/123│Przec. │  2  ││
│ │                              ... (more results) ...                         ││
│ └──────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│    [Otwórz email]  [Pobierz załączniki]                                        │
│                                                                                  │
│  [< Poprzednia]  Strona 1 z 3  [Następna >]   Wyników na stronę: [20 ▼]      │
│                                                    Znaleziono: 45 wyników      │
│                                                                                  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Key UI Enhancements

### 1. Interactive Results Table
- **Before**: Plain text display with fixed formatting
- **After**: Interactive `Treeview` with:
  - Selectable rows
  - Sortable columns  
  - Resizable columns that adapt to window width
  - Double-click support for opening emails

### 2. Action Buttons
- **"Otwórz email"**: Opens selected email in default text editor
- **"Pobierz załączniki"**: Downloads attachments to temp folder and opens folder

### 3. Pagination Controls
- **Previous/Next buttons**: Navigate between pages
- **Page indicator**: "Strona X z Y" shows current position
- **Results per page**: Dropdown to select 10, 20, 50, or 100 results
- **Total count**: "Znaleziono: X wyników" shows total matches

### 4. Dynamic Width Adaptation
- Results table automatically resizes with main window
- Columns have minimum widths but expand proportionally  
- All elements use proper grid weights for responsive layout

## User Interaction Flow

1. **Search**: User fills criteria and clicks "Rozpocznij wyszukiwanie"
2. **View Results**: Interactive table shows paginated results
3. **Select Email**: Click on row to select (highlights in blue)
4. **Open Email**: Double-click row or click "Otwórz email" button
   - Creates temp file with email content
   - Opens in default text editor
5. **Get Attachments**: Click "Pobierz załączniki" 
   - Downloads all attachments to temp folder
   - Opens temp folder in file explorer
6. **Navigate**: Use pagination controls to view more results
7. **Resize**: Drag window edges - results table adapts automatically

## Technical Features

- **Thread-safe**: All operations use existing threading architecture
- **Error handling**: Graceful handling of missing emails/attachments  
- **Performance**: Limited to 500 total results for responsive UI
- **Compatibility**: Works on both Windows (os.startfile) and Linux (xdg-open)
- **Clean temp management**: Overwrites temp files on new searches