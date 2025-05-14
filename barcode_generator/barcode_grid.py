#!/usr/bin/env python3
"""
Barcode Grid Generator

This script extends the barcode_generator.py functionality to create a PDF grid
of barcodes for printing purposes.
"""

import os
import argparse
import pandas as pd
from PIL import Image
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import barcode_generator

def create_barcode_grid(barcode_files, output_file='barcode_grid.pdf', 
                        page_size='letter', margin=0.5, columns=2, 
                        spacing=0.2, label_height=None):
    """
    Create a PDF with a grid of barcodes.
    
    Args:
        barcode_files (list): List of paths to barcode image files
        output_file (str): Path to the output PDF file
        page_size (str): Page size ('letter' or 'a4')
        margin (float): Margin in inches
        columns (int): Number of columns in the grid
        spacing (float): Spacing between barcodes in inches
        label_height (float): Height of each label in inches (None for auto)
    
    Returns:
        str: Path to the generated PDF file
    """
    # Set page dimensions
    if page_size.lower() == 'letter':
        page_width, page_height = letter
    else:  # a4
        page_width, page_height = A4
    
    # Convert margin and spacing to points (1 inch = 72 points)
    margin_pts = margin * inch
    spacing_pts = spacing * inch
    
    # Calculate usable area
    usable_width = page_width - (2 * margin_pts)
    usable_height = page_height - (2 * margin_pts)
    
    # Calculate barcode width based on columns
    barcode_width = (usable_width - (spacing_pts * (columns - 1))) / columns
    
    # Create PDF canvas
    c = canvas.Canvas(output_file, pagesize=(page_width, page_height))
    
    # Position tracking
    x, y = margin_pts, page_height - margin_pts
    col = 0
    
    for img_path in barcode_files:
        # Open the image to get its dimensions
        img = Image.open(img_path)
        img_width, img_height = img.size
        
        # Calculate scaling factor to fit within column width
        scale = barcode_width / img_width
        
        # Calculate scaled height
        scaled_height = img_height * scale
        
        # Use specified label height if provided
        if label_height:
            scaled_height = label_height * inch
            # Recalculate scale to maintain aspect ratio within the label height
            if scaled_height < img_height * scale:
                scale = scaled_height / img_height
                barcode_width_actual = img_width * scale
            else:
                barcode_width_actual = barcode_width
        else:
            barcode_width_actual = barcode_width
        
        # Check if we need to move to a new row
        if col >= columns:
            y -= (scaled_height + spacing_pts)
            x = margin_pts
            col = 0
            
            # Check if we need a new page
            if y < margin_pts:
                c.showPage()
                y = page_height - margin_pts
        
        # Calculate x position to center the barcode in its column
        x_centered = x + (barcode_width - barcode_width_actual) / 2
        
        # Draw the barcode
        c.drawImage(img_path, x_centered, y - scaled_height, 
                   width=img_width * scale, height=img_height * scale)
        
        # Move to next column
        x += barcode_width + spacing_pts
        col += 1
        
        # Check if we need to move to a new row after the last column
        if col >= columns:
            y -= (scaled_height + spacing_pts)
            x = margin_pts
            col = 0
            
            # Check if we need a new page
            if y < margin_pts:
                c.showPage()
                y = page_height - margin_pts
    
    # Save the PDF
    c.save()
    return output_file

def main():
    """Main function to parse arguments and generate barcode grid."""
    parser = argparse.ArgumentParser(description='Generate a PDF grid of barcodes from a CSV file')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--barcode-type', default='code128', 
                        choices=['code128', 'ean13', 'ean8', 'upca', 'isbn13', 'isbn10', 'issn', 'code39', 'pzn'],
                        help='Type of barcode to generate')
    parser.add_argument('--output-dir', help='Directory to save the barcode images (defaults to CSV filename without extension)')
    parser.add_argument('--text-column', default='text', help='Column name containing the text to encode')
    parser.add_argument('--title-column', help='Column name containing the title text (defaults to "title" if column exists)')
    parser.add_argument('--width', type=int, default=400, help='Width of each barcode image')
    parser.add_argument('--height', type=int, default=300, help='Height of each barcode image')
    parser.add_argument('--output-pdf', help='Path to the output PDF file (defaults to {output_dir}_grid.pdf)')
    parser.add_argument('--page-size', default='letter', choices=['letter', 'a4'], help='Page size for the PDF')
    parser.add_argument('--margin', type=float, default=0.5, help='Margin in inches')
    parser.add_argument('--columns', type=int, default=2, help='Number of columns in the grid')
    parser.add_argument('--spacing', type=float, default=0.2, help='Spacing between barcodes in inches')
    parser.add_argument('--label-height', type=float, help='Height of each label in inches (optional)')
    
    args = parser.parse_args()
    
    try:
        # Set output directory based on CSV filename if not specified
        output_dir = args.output_dir
        if not output_dir:
            # Extract the base filename without extension
            csv_basename = os.path.basename(args.csv_file)
            output_dir = os.path.splitext(csv_basename)[0]
            print(f"Using output directory: '{output_dir}'")
        
        # Generate individual barcodes
        barcode_files = barcode_generator.process_csv(
            csv_file=args.csv_file,
            barcode_type=args.barcode_type,
            output_dir=output_dir,
            text_column=args.text_column,
            title_column=args.title_column,
            width=args.width,
            height=args.height
        )
        
        # Set output PDF path if not specified
        output_pdf = args.output_pdf
        if not output_pdf:
            output_pdf = f"{output_dir}_grid.pdf"
        
        # Create the barcode grid PDF
        pdf_path = create_barcode_grid(
            barcode_files=barcode_files,
            output_file=output_pdf,
            page_size=args.page_size,
            margin=args.margin,
            columns=args.columns,
            spacing=args.spacing,
            label_height=args.label_height
        )
        
        print(f"Barcode grid PDF generated successfully: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
