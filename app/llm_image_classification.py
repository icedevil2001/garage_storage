# import os
# import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image, ImageOps
import json
from rich import print
from pathlib import Path
from .utils import resize_image, thumbnail_image, plot_bounding_boxes, encode_image
load_dotenv()


import base64
from openai import OpenAI

client = OpenAI()


def llm_classification(img_path: str) -> Image:
    """
    Function to classify objects in an image using OpenAI's GPT-4 Vision API
    Args:
        img_path (str): Path to the image file to resized image
    """
    
    base64_image = encode_image(img_path)

    # Make API call to OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={
            "type": "json_object"
        },
        temperature=1,
        max_completion_tokens=2048,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "Return bounding boxes as a JSON array with labels. Never return masks or code fencing. Limit to 50 objects. Output a JSON list where each entry contains the 2D bounding box in \"box_2d\" and a text label in \"label\" and Short description  in \"description\". For example: [{\"box_2d\": [0, 0, 100, 100], \"label\": \"dog\", \"description\": \"A white dog in the image\"}]. Yes, there are books in the image. Please try and extract the title and add that to the description."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please classify the objects in this image.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )

    print(response.choices[0].message.content)

    # Process response
    content = json.loads(response.choices[0].message.content)
    bounding_boxes = content["objects"]

    # Create and save image with bounding boxes
    # img = Image.open("resized_img.jpg")
    # img = ImageOps.exif_transpose(img)
    # bounding_boxes_json = json.dumps(bounding_boxes)
    # bounding_img = plot_bounding_boxes(img, bounding_boxes_json, raw_cords=False)
    # bounding_img.save("bounding_boxes.jpeg")
    
    return content["objects"]
