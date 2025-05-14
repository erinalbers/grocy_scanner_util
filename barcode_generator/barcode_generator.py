#!/usr/bin/env python3
"""
Barcode Generator

This script reads strings from a CSV file and generates barcodes with titles.
"""

import os
import argparse
import pandas as pd
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont
import io

def generate_barcode(text, barcode_type='code128', output_dir='barcodes', title=None, width=400, height=300):
    """
    Generate a barcode image with an optional title.
    
    Args:
        text (str): The text to encode in the barcode
        barcode_type (str): The type of barcode to generate (default: code128)
        output_dir (str): Directory to save the barcode images
        title (str): Optional title to display with the barcode
        width (int): Width of the output image
        height (int): Height of the output image
        
    Returns:
        str: Path to the generated barcode image
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate a valid filename from the text
    filename = "".join(c if c.isalnum() else "_" for c in text)
    output_path = os.path.join(output_dir, f"{filename}")
    
    # Create the barcode
    barcode_class = barcode.get_barcode_class(barcode_type)
    
    # Create a writer with better settings for scanning
    writer = ImageWriter()
    # Adjust writer properties for better scanning
    writer.module_width = 1  # Wider bars
    writer.module_height = 20.0  # Taller bars
    writer.quiet_zone = 6.5  # Larger quiet zone
    writer.font_size = 8  # Smaller text
    writer.text_distance = .5  # Text distance
    
    barcode_instance = barcode_class(text, writer=writer)
    
    # Generate the barcode image
    barcode_bytes = io.BytesIO()
    barcode_instance.write(barcode_bytes)
    barcode_image = Image.open(barcode_bytes)
    
    # Create a new image with space for the title
    if title:
        # Create a new blank image
        new_image = Image.new('RGB', (width, height), 'white')
        
        # Calculate the space needed for the title (approximately 20% of height)
        title_space = int(height * 0.2)
        barcode_height = height - title_space
        
        # Get original barcode dimensions
        orig_width, orig_height = barcode_image.size
        
        # Calculate scaling factor to maintain aspect ratio
        # Use a smaller scale factor to avoid resizing the barcode too much
        # which can make it harder to scan
        scale_factor = min(0.9, min(width / orig_width, barcode_height / orig_height))

        # Calculate new dimensions while maintaining aspect ratio
        new_width = int(orig_width * scale_factor)
        new_height = int(orig_height * scale_factor)
        
        # Resize the barcode maintaining aspect ratio
        barcode_resized = barcode_image.resize((new_width, new_height))
        
        # Calculate position to center the barcode horizontally
        x_offset = (width - new_width) // 2
        
        # Paste the barcode into the new image
        new_image.paste(barcode_resized, (x_offset, 0))
        
        # Add the title text
        draw = ImageDraw.Draw(new_image)
        
        # Try to use a system font, fall back to default if not available
        try:
            font = ImageFont.truetype("Arial", 24)
        except IOError:
            font = ImageFont.load_default()
        
        # Calculate position for the title text (centered at the bottom)
        try:
            # For newer Pillow versions
            text_width = draw.textlength(title, font=font)
            text_x = (width - text_width) // 2
            text_y = barcode_height + (title_space // 2) - (title_space * .2) # Center text in the remaining space
        except AttributeError:
            # For older Pillow versions
            try:
                text_width, text_height = font.getsize(title)
                text_x = (width - text_width) // 2
                text_y = barcode_height + (title_space // 2) - (text_height * 3)  # Center text vertically
            except AttributeError:
                # Last resort
                text_x = width // 4
                text_y = barcode_height + 10
                
        # Draw the text
        draw.text((text_x, text_y), title, fill="black", font=font)
        
        # Save the image with high quality
        new_image.save(f"{output_path}.png", quality=95, dpi=(300, 300))
    else:
        # Save the original barcode if no title with high quality
        barcode_image.save(f"{output_path}.png", quality=95, dpi=(300, 300))
    
    return f"{output_path}.png"

def process_csv(csv_file, barcode_type='code128', output_dir='barcodes', 
                text_column='text', title_column=None, width=400, height=300):
    """
    Process a CSV file and generate barcodes for each row.
    
    Args:
        csv_file (str): Path to the CSV file
        barcode_type (str): Type of barcode to generate
        output_dir (str): Directory to save the barcode images
        text_column (str): Column name containing the text to encode
        title_column (str): Column name containing the title text (optional)
        width (int): Width of the output image
        height (int): Height of the output image
        
    Returns:
        list: Paths to the generated barcode images
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Check if the required column exists
    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in the CSV file")
    
    # Generate barcodes for each row
    generated_files = []
    for index, row in df.iterrows():
        text = str(row[text_column])
        
        # Get title if title column is specified and exists
        title = None
        if title_column and title_column in df.columns:
            title = str(row[title_column])
        
        # Generate the barcode
        output_path = generate_barcode(
            text=text,
            barcode_type=barcode_type,
            output_dir=output_dir,
            title=title,
            width=width,
            height=height
        )
        
        generated_files.append(output_path)
        print(f"Generated barcode for '{text}': {output_path}")
    
    return generated_files

def main():
    """Main function to parse arguments and generate barcodes."""
    parser = argparse.ArgumentParser(description='Generate barcodes from a CSV file')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--barcode-type', default='code128', 
                        choices=['code128', 'ean13', 'ean8', 'upca', 'isbn13', 'isbn10', 'issn', 'code39', 'pzn'],
                        help='Type of barcode to generate')
    parser.add_argument('--output-dir', help='Directory to save the barcode images (defaults to CSV filename without extension)')
    parser.add_argument('--text-column', default='text', help='Column name containing the text to encode')
    parser.add_argument('--title-column', help='Column name containing the title text (defaults to "title" if column exists)')
    parser.add_argument('--width', type=int, default=400, help='Width of the output image')
    parser.add_argument('--height', type=int, default=300, help='Height of the output image')
    
    args = parser.parse_args()
    
    try:
        # Set output directory based on CSV filename if not specified
        output_dir = args.output_dir
        if not output_dir:
            # Extract the base filename without extension
            csv_basename = os.path.basename(args.csv_file)
            output_dir = os.path.splitext(csv_basename)[0]
            print(f"Using output directory: '{output_dir}'")
        
        # Check if title column is specified or if "title" column exists in the CSV
        title_column = args.title_column
        if not title_column:
            # Try to read the CSV to check if "title" column exists
            try:
                df = pd.read_csv(args.csv_file)
                if 'title' in df.columns:
                    title_column = 'title'
                    print('Using "title" column from CSV for barcode titles')
            except Exception:
                # If there's an error reading the CSV, we'll let process_csv handle it
                pass
        
        process_csv(
            csv_file=args.csv_file,
            barcode_type=args.barcode_type,
            output_dir=output_dir,
            text_column=args.text_column,
            title_column=title_column,
            width=args.width,
            height=args.height
        )
        print(f"Barcodes generated successfully in '{output_dir}' directory")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
