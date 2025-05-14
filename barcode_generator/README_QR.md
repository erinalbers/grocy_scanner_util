# QR Code Generator

A Python utility for generating QR codes from CSV data.

## Features

- Generate QR codes from CSV data
- Add custom titles to QR codes
- Customize QR code dimensions
- Adjustable error correction levels
- High-quality output for reliable scanning
- Create printable PDF grids of QR codes

## Requirements

- Python 3.6+
- Required packages:
  - qrcode
  - pillow
  - pandas
  - reportlab

## Installation

```bash
pip3 install qrcode pillow pandas reportlab
```

## Usage

### Basic Usage

```bash
python3 qr_generator.py sample_data.csv
```

This will read the CSV file and generate QR codes for each row, saving them in a directory named after the CSV file with "_qr" appended.

### Advanced Options

```bash
python3 qr_generator.py sample_data.csv --error-correction H --output-dir my_qrcodes --text-column product_code --title-column product_name --width 1000 --height 1000
```

### Creating a PDF Grid of QR Codes

```bash
python3 qr_grid.py sample_data.csv --columns 4 --rows 4 --page-size letter
```

This will generate individual QR codes and then create a PDF with the QR codes arranged in a grid layout (4x4 by default) for printing.

### Command Line Arguments

- `csv_file`: Path to the CSV file (required)
- `--error-correction`: Error correction level (default: M)
  - L: 7% error correction
  - M: 15% error correction
  - Q: 25% error correction
  - H: 30% error correction
- `--output-dir`: Directory to save the QR code images (defaults to CSV filename + "_qr")
- `--text-column`: Column name containing the text to encode (default: text)
- `--title-column`: Column name containing the title text (defaults to "title" if column exists)
- `--width`: Width of the output image (default: 800)
- `--height`: Height of the output image (default: 800)

#### Additional Options for qr_grid.py

- `--output-pdf`: Path to the output PDF file (defaults to {output_dir}_grid.pdf)
- `--page-size`: Page size for the PDF (choices: letter, a4, default: letter)
- `--margin`: Margin in inches (default: 0.5)
- `--columns`: Number of columns in the grid (default: 4)
- `--rows`: Number of rows in the grid (default: 4)
- `--spacing`: Spacing between QR codes in inches (default: 0.2)
- `--label-height`: Height of each label in inches (optional)

## CSV Format

The CSV file should contain at least one column with the text to encode in the QR code. Optionally, it can include a column for the title text.

Example:

```csv
text,title
123456789012,Product A
987654321098,Product B
```

## Examples

Generate QR codes using the default settings:
```bash
python3 qr_generator.py data.csv
```

Generate QR codes with high error correction:
```bash
python3 qr_generator.py data.csv --error-correction H
```

Use custom column names:
```bash
python3 qr_generator.py products.csv --text-column product_id --title-column product_name
```

## Error Correction Levels

QR codes include error correction capability to restore data if the code is damaged or partially obscured:

- **L (Low)**: 7% of data can be restored
- **M (Medium)**: 15% of data can be restored
- **Q (Quartile)**: 25% of data can be restored
- **H (High)**: 30% of data can be restored

Higher error correction makes QR codes more reliable but also more complex (denser).
