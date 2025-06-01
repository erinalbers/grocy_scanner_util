#!/usr/bin/env python3
"""
QR Code Grid Generator

This script extends the qr_generator.py functionality to create a PDF grid
of QR codes for printing purposes, with a default of 4 rows and 4 columns per page.
"""

import os
import argparse
import pandas as pd
from PIL import Image
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import qr_generator

def create_qrcode_grid(qrcode_files, output_file='qrcode_grid.pdf', 
                      page_size='letter', margin=0, columns=3, rows=3,
                      spacing=0, label_height=None):
    """
    Create a PDF with a grid of QR codes.
    
    Args:
        qrcode_files (list): List of paths to QR code image files
        output_file (str): Path to the output PDF file
        page_size (str): Page size ('letter' or 'a4')
        margin (float): Margin in inches
        columns (int): Number of columns in the grid
        rows (int): Number of rows in the grid (used to calculate spacing)
        spacing (float): Spacing between QR codes in inches
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
    
    # Calculate QR code width based on columns
    qrcode_width = (usable_width - (spacing_pts * (columns - 1))) / columns
    
    # Calculate QR code height based on rows (if rows is specified)
    qrcode_height = (usable_height - (spacing_pts * (rows - 1))) / rows
    
    # Create PDF canvas
    c = canvas.Canvas(output_file, pagesize=(page_width, page_height))
    
    # Position tracking
    x, y = margin_pts, page_height - margin_pts
    col = 0
    row = 0
    
    for img_path in qrcode_files:
        # Open the image to get its dimensions
        img = Image.open(img_path)
        img_width, img_height = img.size
        
        # Calculate scaling factor to fit within column width and row height
        scale_width = qrcode_width / img_width
        scale_height = qrcode_height / img_height
        scale = min(scale_width, scale_height)  # Use the smaller scale to maintain aspect ratio
        
        # Calculate scaled dimensions
        scaled_width = img_width * scale
        scaled_height = img_height * scale
        
        # Use specified label height if provided
        if label_height:
            scaled_height = label_height * inch
            # Recalculate scale to maintain aspect ratio within the label height
            if scaled_height < img_height * scale:
                scale = scaled_height / img_height
                scaled_width = img_width * scale
        
        # Calculate position to center the QR code in its cell
        x_centered = x + (qrcode_width - scaled_width) / 2
        y_position = y - scaled_height
        
        # Draw the QR code
        c.drawImage(img_path, x_centered, y_position, 
                   width=scaled_width, height=scaled_height)
        
        # Move to next column
        x += qrcode_width + spacing_pts
        col += 1
        
        # Check if we need to move to a new row
        if col >= columns:
            x = margin_pts
            y -= (qrcode_height + spacing_pts)
            col = 0
            row += 1
            
            # Check if we need a new page
            if row >= rows:
                c.showPage()
                x = margin_pts
                y = page_height - margin_pts
                row = 0
    
    # Save the PDF
    c.save()
    return output_file

def main():
    """Main function to parse arguments and generate QR code grid."""
    parser = argparse.ArgumentParser(description='Generate a PDF grid of QR codes from a CSV file')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--error-correction', default='M', choices=['L', 'M', 'Q', 'H'],
                        help='Error correction level: L (7%), M (15%), Q (25%), H (30%)')
    parser.add_argument('--output-dir', help='Directory to save the QR code images (defaults to CSV filename without extension)')
    parser.add_argument('--text-column', default='text', help='Column name containing the text to encode')
    parser.add_argument('--title-column', help='Column name containing the title text (defaults to "title" if column exists)')
    parser.add_argument('--width', type=int, default=800, help='Width of each QR code image')
    parser.add_argument('--height', type=int, default=800, help='Height of each QR code image')
    parser.add_argument('--output-pdf', help='Path to the output PDF file (defaults to {output_dir}_grid.pdf)')
    parser.add_argument('--page-size', default='letter', choices=['letter', 'a4'], help='Page size for the PDF')
    parser.add_argument('--margin', type=float, default=0, help='Margin in inches')
    parser.add_argument('--columns', type=int, default=3, help='Number of columns in the grid')
    parser.add_argument('--rows', type=int, default=3, help='Number of rows in the grid')
    parser.add_argument('--spacing', type=float, default=0, help='Spacing between QR codes in inches')
    parser.add_argument('--label-height', type=float, help='Height of each label in inches (optional)')
    
    args = parser.parse_args()
    
    try:
        # Set output directory based on CSV filename if not specified
        output_dir = args.output_dir
        if not output_dir:
            # Extract the base filename without extension
            csv_basename = os.path.basename(args.csv_file)
            output_dir = os.path.splitext(csv_basename)[0] + "_qr"
            print(f"Using output directory: '{output_dir}'")
        
        # Generate individual QR codes
        qrcode_files = qr_generator.process_csv(
            csv_file=args.csv_file,
            output_dir=output_dir,
            text_column=args.text_column,
            title_column=args.title_column,
            width=args.width,
            height=args.height,
            error_correction=args.error_correction
        )
        
        # Set output PDF path if not specified
        output_pdf = args.output_pdf
        if not output_pdf:
            output_pdf = f"{output_dir}_grid.pdf"
        
        # Create the QR code grid PDF
        pdf_path = create_qrcode_grid(
            qrcode_files=qrcode_files,
            output_file=output_pdf,
            page_size=args.page_size,
            margin=args.margin,
            columns=args.columns,
            rows=args.rows,
            spacing=args.spacing,
            label_height=args.label_height
        )
        
        print(f"QR code grid PDF generated successfully: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
