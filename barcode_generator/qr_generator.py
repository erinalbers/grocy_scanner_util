#!/usr/bin/env python3
"""
QR Code Generator

This script reads strings from a CSV file and generates QR codes with titles.
"""

import os
import argparse
import pandas as pd
import qrcode
from PIL import Image, ImageDraw, ImageFont
import io

def generate_qrcode(text, output_dir='qrcodes', title=None, width=800, height=400, error_correction='M', index=0):
    """
    Generate a QR code image with an optional title.
    
    Args:
        text (str): The text to encode in the QR code
        output_dir (str): Directory to save the QR code images
        title (str): Optional title to display with the QR code
        width (int): Width of the output image
        height (int): Height of the output image
        error_correction (str): Error correction level (L, M, Q, H)
        
    Returns:
        str: Path to the generated QR code image
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate a valid filename from the text
    filename = "".join(c if c.isalnum() else "_" for c in text)
    output_path = os.path.join(output_dir, f"{index}_{filename}")
    
    # Set error correction level
    error_levels = {
        'L': qrcode.constants.ERROR_CORRECT_L,  # 7% error correction
        'M': qrcode.constants.ERROR_CORRECT_M,  # 15% error correction
        'Q': qrcode.constants.ERROR_CORRECT_Q,  # 25% error correction
        'H': qrcode.constants.ERROR_CORRECT_H   # 30% error correction
    }
    error_level = error_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_M)
    
    # Create the QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=error_level,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    
    # Create QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Create a new image with space for the title
    if title:
        # Create a new blank image
        new_image = Image.new('RGB', (width, height), 'white')
        
        # Calculate the space needed for the title (approximately 20% of height)
        title_space = int(height * 0.2)
        qr_height = height - title_space
        
        # Get original QR code dimensions
        orig_width, orig_height = qr_image.size
        
        # Calculate scaling factor to maintain aspect ratio
        scale_factor = min(width / orig_width, qr_height / orig_height)
        
        # Calculate new dimensions while maintaining aspect ratio
        new_width = int(orig_width * scale_factor)
        new_height = int(orig_height * scale_factor)
        
        # Resize the QR code maintaining aspect ratio
        qr_resized = qr_image.resize((new_width, new_height))
        
        # Calculate position to center the QR code horizontally
        x_offset = (width - new_width) // 2
        
        # Paste the QR code into the new image
        new_image.paste(qr_resized, (x_offset, 0))
        
        # Add the title text
        draw = ImageDraw.Draw(new_image)
        
        # Try to use a system font, fall back to default if not available
        try:
            font = ImageFont.truetype("Helvetica", 48)
        except IOError:
            font = ImageFont.load_default()
            
        # Calculate position for the title text (centered at the bottom)
        try:
            # For newer Pillow versions
            text_width = draw.textlength(title, font=font)
            text_x = (width - text_width) // 2
            text_y = qr_height + (title_space // 2) - (title_space * .2)  # Center text in the remaining space
        except AttributeError:
            # For older Pillow versions
            try:
                text_width, text_height = font.getsize(title)
                text_x = (width - text_width) // 2
                text_y = qr_height + (title_space // 2) - (text_height // 2)  # Center text vertically
            except AttributeError:
                # Last resort
                text_x = width // 4
                text_y = qr_height + 10
                
        # Draw the text
        draw.text((text_x, text_y), title, fill="black", font=font)
        
        # Save the image with high quality
        new_image.save(f"{output_path}.png", quality=95, dpi=(300, 300))
    else:
        # Save the original QR code if no title with high quality
        qr_image.save(f"{output_path}.png", quality=95, dpi=(300, 300))
    
    return f"{output_path}.png"

def process_csv(csv_file, output_dir='qrcodes', text_column='text', title_column=None, 
                width=800, height=400, error_correction='M', index=int):
    """
    Process a CSV file and generate QR codes for each row.
    
    Args:
        csv_file (str): Path to the CSV file
        output_dir (str): Directory to save the QR code images
        text_column (str): Column name containing the text to encode
        title_column (str): Column name containing the title text (optional)
        width (int): Width of the output image
        height (int): Height of the output image
        error_correction (str): Error correction level (L, M, Q, H)
        
    Returns:
        list: Paths to the generated QR code images
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Check if the required column exists
    if text_column not in df.columns:
        raise ValueError(f"Column '{text_column}' not found in the CSV file")
    
    # Generate QR codes for each row
    generated_files = []
    for index, row in df.iterrows():
        text = str(row[text_column])
        
        # Check if this is a row break marker
        if text.strip().startswith("ROW_BREAK"):
            # Extract section title if present (format: ROW_BREAK:Section Title or ROW_BREAK;Section Title)
            section_title = None
            if ":" in text:
                section_title = text.split(":", 1)[1].strip()
            elif ";" in text:
                section_title = text.split(";", 1)[1].strip()
                
            # Add a special marker to indicate a row break in the grid with optional section title
            if section_title:
                generated_files.append(f"ROW_BREAK;{section_title}")
                print(f"Added row break marker with section title '{section_title}' at index {index}")
            else:
                generated_files.append("ROW_BREAK")
                print(f"Added row break marker at index {index}")
            continue
            
        # Get title if title column is specified and exists
        title = None
        if title_column and title_column in df.columns:
            title = str(row[title_column])
        
        # Generate the QR code
        output_path = generate_qrcode(
            text=text,
            output_dir=output_dir,
            title=title,
            width=width,
            height=height,
            error_correction=error_correction,
            index=index,
        )
        
        generated_files.append(output_path)
        print(f"Generated QR code for '{text}': {output_path}")
    
    return generated_files

def main():
    """Main function to parse arguments and generate QR codes."""
    parser = argparse.ArgumentParser(description='Generate QR codes from a CSV file')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--error-correction', default='M', choices=['L', 'M', 'Q', 'H'],
                        help='Error correction level: L (7%), M (15%), Q (25%), H (30%)')
    parser.add_argument('--output-dir', help='Directory to save the QR code images (defaults to CSV filename without extension)')
    parser.add_argument('--text-column', default='text', help='Column name containing the text to encode')
    parser.add_argument('--title-column', help='Column name containing the title text (defaults to "title" if column exists)')
    parser.add_argument('--width', type=int, default=800, help='Width of the output image')
    parser.add_argument('--height', type=int, default=800, help='Height of the output image')
    
    args = parser.parse_args()
    
    try:
        # Set output directory based on CSV filename if not specified
        output_dir = args.output_dir
        if not output_dir:
            # Extract the base filename without extension
            csv_basename = os.path.basename(args.csv_file)
            output_dir = os.path.splitext(csv_basename)[0] + "_qr"
            print(f"Using output directory: '{output_dir}'")
        
        # Check if title column is specified or if "title" column exists in the CSV
        title_column = args.title_column
        if not title_column:
            # Try to read the CSV to check if "title" column exists
            try:
                df = pd.read_csv(args.csv_file)
                if 'title' in df.columns:
                    title_column = 'title'
                    print('Using "title" column from CSV for QR code titles')
            except Exception:
                # If there's an error reading the CSV, we'll let process_csv handle it
                pass
        
        process_csv(
            csv_file=args.csv_file,
            output_dir=output_dir,
            text_column=args.text_column,
            title_column=title_column,
            width=args.width,
            height=args.height,
            error_correction=args.error_correction
        )
        print(f"QR codes generated successfully in '{output_dir}' directory")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
