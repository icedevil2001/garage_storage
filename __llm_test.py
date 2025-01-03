


import os
import google.generativeai as genai
from dotenv import load_dotenv
from utils import gemmia_image_resize, thumbnail_image, plot_bounding_boxes
from PIL import Image, ImageOps
import json
from rich import print

load_dotenv()


import base64
from openai import OpenAI

client = OpenAI()

# Function to encode the image
def encode_image(image_path):
    img = gemmia_image_resize(image_path)
    img.save("resized_img.jpg")

    with open("resized_img.jpg", "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# Path to your image
# image_path = "path_to_your_image.jpg"

# Getting the base64 string
base64_image = encode_image(img_path)

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
            "text": "Return bounding boxes as a JSON array with labels. Never return masks or code fencing. Limit to 25 objects. Output a JSON list where each entry contains the 2D bounding box in \"box_2d\" and a text label in \"label\"."
            }
        ]
        },
        {
            "role": "user",
            "content": [
                
                {
                    "type": "text",
                    "text": "What is in this image?",
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

content = json.loads(response.choices[0].message.content)
bounding_boxes = content["objects"]
print(bounding_boxes)


img = Image.open("resized_img.jpg")
img = ImageOps.exif_transpose(img)
bounding_boxes_json = json.dumps(bounding_boxes)
bounding_img = plot_bounding_boxes(img, bounding_boxes_json, raw_cords=False)
bounding_img.save("bounding_boxes.jpeg")
bounding_img.show()

