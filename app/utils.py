import qrcode
import random
import string
import csv
import os
import re
import json
from io import StringIO
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageOps
import base64
from pathlib import Path
from .logger_config import setup_logger
logger = setup_logger(None)  # Pass None since we don't need Flask app context here
from app.models import Box
from hashlib import md5
from typing import Union
from werkzeug.utils import secure_filename



def image_hash(image_path: Path) -> str:
    """Generate a hash for an image file."""
    image_path = Path(image_path)
    with open(image_path, "rb") as f:
        return md5(f.read()).hexdigest()


def generate_qr_id():
    """Generate a random QR code ID."""
    letters = ''.join(random.choices(string.ascii_uppercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=4))
    qrcode_id = f"{letters}{numbers}"
    logger.info(f"Generated QR code ID: {qrcode_id}")
    return qrcode_id


def sequential_qr_id(box_id=None):
    """Generate a sequential QR code ID.
    example: AA00001, AA00002, ..., AA99999, AB00001, AB00002, ...
    """
    if box_id:
        # last_qr = Box.query.filter_by(id=box_id).first()
        last_qr = box_id
    else:
        last_qr = Box.query.order_by(Box.id.desc()).first()

    logger.info(f"Last QR code ID: {last_qr.id if last_qr else None}")
    alphabet = string.ascii_uppercase
    alphabet_dict = dict(zip(alphabet, range(0, 26)))

    if last_qr:
        last_qr_id = last_qr.id
        last_qr_id = last_qr_id[2:]
        new_qr_id = int(last_qr_id) + 1
        new_qr_id = f"{new_qr_id:06}"
        logger.info(f"New QR code ID: {new_qr_id}")
        # Extract the letters and numbers
        last_letters = last_qr.id[:2]

        
        # Check if we need to increment letters
        if int(new_qr_id) > 9999:
            # Convert AA to next sequence using alphabet_dict
            first_letter = last_letters[0]
            second_letter = last_letters[1]
            second_letter_idx = alphabet_dict[second_letter]

            if second_letter_idx == 25:  # Z is at index 25
                first_letter_idx = alphabet_dict[first_letter]
                first_letter = alphabet[first_letter_idx + 1]
                second_letter = alphabet[0]  # Reset to A
            else:
                second_letter = alphabet[second_letter_idx + 1]
                new_qr_id = "000001"  # Reset number sequence
                new_letters = f"{first_letter}{second_letter}"
        else:
            new_letters = last_letters
            
        new_qr_id = f"{new_letters}{new_qr_id}"
    else:
        new_qr_id = "AA000001"
    while Box.query.filter_by(qr_code_id=new_qr_id).first():
        logger.info(f"QR code ID {new_qr_id} already exists. Generating a new one.")
        last_qr_id = int(new_qr_id[2:]) + 1
        new_qr_id = f"{new_qr_id[:2]}{last_qr_id:06}"
    return new_qr_id


def add_qr_code_to_image(image_path, qr_code_id, name=None):
    font_size = 35
    font_family = "Arial"
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    # Use black color as a single integer value (0)
    # Load a larger font (you may need to adjust the size)
    font = ImageFont.truetype(font_family, font_size)
    # Get text size to center it
    text_width = draw.textlength(qr_code_id, font=font)
    text_x = (img.size[0] - text_width) // 2
    text_y = img.size[1] - 35

    if name:
        ## Name and QR code id
        draw.text((text_x, text_y + font_size ), f"{name} - {qr_code_id}", font=font, fill=0)
    ## QR code id
    draw.text((text_x, text_y), qr_code_id, font=font, fill=0)

    img.save(image_path)
    return image_path  


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


def thumbnail_image(image_path, size):
    image = Image.open(image_path)
    image.thumbnail(size)
    return image


def save_image_with_hash(image_path: Path) -> str:
    """Save an image with a hash of its contents as the filename and resize.
     Returns the new filename.
     """
    image_path = Path(image_path)
    ext = image_path.suffix

    resized_image = resize_image(image_path)
    resized_image.save(image_path)  # Save the resized image
    new_filename = image_path.parent / f"{image_hash(image_path)}{ext}"
    image_path.rename(new_filename)
    logger.info(f"Saved image as: {new_filename}")
    return new_filename


def resize_image(image_path, size=1024):
    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image)
    width, height = image.size
   
    # print(f"Original Image Size: {width}x{height}")
    logger.debug(f"Original Image Size: {width}x{height}")
    if width > height:
        new_width = size
        new_height = int(size * height / width)
    else:
        new_height = size
        new_width = int(size * width / height)
    # print(f"Resized Image Size: {new_width}x{new_height}")
    logger.debug(f"Resized Image Size: {new_width}x{new_height}")
    resize_img = image.resize(
        (new_width, new_height), 
        # resample=Image.Resampling.LANCZOS
        )
    return resize_img


def parse_json(json_input: str) -> str:
    match = re.search(r"```json\n(.*?)```", json_input, re.DOTALL)
    json_input = match.group(1) if match else ""
    return json_input


def plot_bounding_boxes(img: Image, bounding_boxes: str, raw_cords: bool=False) -> Image:
    width, height = img.size
    colors = [colorname for colorname in ImageColor.colormap.keys()]
    draw = ImageDraw.Draw(img)

    # bounding_boxes = parse_json(bounding_boxes)

    for bounding_box in json.loads(bounding_boxes):
        color = random.choice(colors)
        if raw_cords:
            ## no need to covert to absolute coordinates
            abs_x1, abs_y1, abs_x2, abs_y2 = bounding_box["box_2d"]
        else:
            # Convert normalized coordinates to absolute coordinates
            abs_y1 = int(bounding_box["box_2d"][0] / 1000 * height)
            abs_x1 = int(bounding_box["box_2d"][1] / 1000 * width)
            abs_y2 = int(bounding_box["box_2d"][2] / 1000 * height)
            abs_x2 = int(bounding_box["box_2d"][3] / 1000 * width)

        if abs_x1 > abs_x2:
            abs_x1, abs_x2 = abs_x2, abs_x1

        if abs_y1 > abs_y2:
            abs_y1, abs_y2 = abs_y2, abs_y1

        print(
            f"Absolute Co-ordinates: {bounding_box['label']}, {abs_y1}, {abs_x1},{abs_y2}, {abs_x2}",
        )

        draw.rectangle(((abs_x1, abs_y1), (abs_x2, abs_y2)), outline=color, width=4)

        # Draw label
        draw.text(
            (abs_x1 + 8, abs_y1 + 6),
            bounding_box["label"],
            fill=color,
            font=ImageFont.truetype(
                "Arial.ttf",
                # "path/to/your/font.ttf",
                size=14,
            ),
        )

    return img


def encode_image(image_path: Path) -> str:
    """Encode an image file as a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

