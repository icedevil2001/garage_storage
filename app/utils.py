import qrcode
import random
import string
import csv
import os
from io import StringIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont


def generate_qr_id():
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=6))
    return f"{letters}{numbers}"


def add_qr_code_to_image(image_path, qr_code_id):
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    # Use black color as a single integer value (0)
    # Load a larger font (you may need to adjust the size)
    font = ImageFont.truetype("Arial", 35)
    # Get text size to center it
    text_width = draw.textlength(qr_code_id, font=font)
    text_x = (img.size[0] - text_width) // 2
    text_y = img.size[1] - 35
    # Draw centered text
    draw.text((text_x, text_y), qr_code_id, font=font, fill=0)
    img.save(image_path)


def generate_qr_code(data, qr_code_id):
    # Create QR codes directory if it doesn't exist
    qr_code_dir = os.path.join('app', 'static', 'qr_codes')
    os.makedirs(qr_code_dir, exist_ok=True)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Create QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_image = qr_image.convert('RGB')
    
    # Create new image with extra space at bottom
    new_width = qr_image.size[0]
    new_height = qr_image.size[1] + 40
    new_img = Image.new('RGB', (new_width, new_height), 'white')
    
    # Paste QR code onto new image with explicit region
    new_img.paste(qr_image, (0, 0, qr_image.size[0], qr_image.size[1]))
    
    # Fix the path to avoid double qr_codes
    qr_code_path = os.path.join(qr_code_dir, f'{qr_code_id}.png')
    new_img.save(qr_code_path)
    add_qr_code_to_image(qr_code_path, qr_code_id)
    return f'qr_codes/{qr_code_id}.png'


def export_to_csv(boxes):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Box Name', 'Box Description', 'Box Location', 'Box Created At', 
                    'Box QR Code ID', 'Item Name', 'Item Description', 
                    'Item Image Path', 'Item Created At'])
    
    for box in boxes:
        for item in box.items:
            writer.writerow([
                box.name, box.description, box.location, 
                box.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                box.qr_code_id, item.name, item.description,
                item.image_path, item.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
    
    return output.getvalue()
