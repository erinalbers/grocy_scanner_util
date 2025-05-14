# Barcode Generator

A Python utility for generating barcodes from CSV data.

## Features

- Generate barcodes from CSV data
- Support for multiple barcode formats (Code128, EAN13, etc.)
- Add custom titles to barcodes
- Customize barcode dimensions
- Create printable PDF grids of barcodes

## Requirements

- Python 3.6+
- Required packages:
  - python-barcode
  - pillow
  - pandas
  - reportlab

## Installation

```bash
pip3 install python-barcode pillow pandas reportlab
```

## Usage

### Basic Usage

```bash
python3 barcode_generator.py sample_data.csv
```

This will read the CSV file and generate barcodes for each row, saving them in a `barcodes` directory.

### Advanced Options

```bash
python3 barcode_generator.py sample_data.csv --barcode-type ean13 --output-dir my_barcodes --text-column product_code --title-column product_name --width 800 --height 400
```

### Creating a PDF Grid of Barcodes

```bash
python3 barcode_grid.py sample_data.csv --columns 3 --page-size letter
```

This will generate individual barcodes and then create a PDF with the barcodes arranged in a grid layout for printing.

### Command Line Arguments

- `csv_file`: Path to the CSV file (required)
- `--barcode-type`: Type of barcode to generate (default: code128)
  - Supported types: code128, ean13, ean8, upca, isbn13, isbn10, issn, code39, pzn
- `--output-dir`: Directory to save the barcode images (defaults to CSV filename without extension)
- `--text-column`: Column name containing the text to encode (default: text)
- `--title-column`: Column name containing the title text (defaults to "title" if column exists)
- `--width`: Width of the output image (default: 800)
- `--height`: Height of the output image (default: 400)

#### Additional Options for barcode_grid.py

- `--output-pdf`: Path to the output PDF file (defaults to {output_dir}_grid.pdf)
- `--page-size`: Page size for the PDF (choices: letter, a4, default: letter)
- `--margin`: Margin in inches (default: 0.5)
- `--columns`: Number of columns in the grid (default: 2)
- `--spacing`: Spacing between barcodes in inches (default: 0.2)
- `--label-height`: Height of each label in inches (optional)

## CSV Format

The CSV file should contain at least one column with the text to encode in the barcode. Optionally, it can include a column for the title text.

Example:

```csv
text,title
123456789012,Product A
987654321098,Product B
```

## Examples

Generate barcodes using the default settings:
```bash
python3 barcode_generator.py data.csv
```

Generate EAN-13 barcodes with custom dimensions:
```bash
python3 barcode_generator.py data.csv --barcode-type ean13 --width 800 --height 400
```

Use custom column names:
```bash
python3 barcode_generator.py products.csv --text-column product_id --title-column product_name
```
