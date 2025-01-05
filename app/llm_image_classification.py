# import os
# import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image, ImageOps
import json
from rich import print
from pathlib import Path
from .utils import resize_image, thumbnail_image, plot_bounding_boxes, encode_image
load_dotenv()
# from logger_config import setup_logger  
# logger = setup_logger(None)
from .models import LLMUsasge
from .extensions import db 

import base64
from openai import OpenAI

client = OpenAI()


class UsageCost:

    ## Model: (input_cost/1M token, output_cost/1M token)
    ## Cost per token in dollars per 1Million tokens
    models_cost_per_token = {
        "gpt-4o-mini": (0.150, 0.600),
        "gpt-4o": (2.5, 10.00),
        "o1": (15.00, 60.00),
        "o1-mini": (3, 12.00)
    }
    def __init__(self, model: str):
        self.model = model
        self.input_cost, self.output_cost = self.models_cost_per_token.get(model, (0.0000001, 0.0000001))

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = input_tokens * (self.input_cost / 1e6) ## price per token in dollars
        output_cost = output_tokens * (self.output_cost / 1e6)
        return (input_cost, output_cost)
    
    def __repr__(self):
        return f"<UsageCost model: {self.model}, input_cost: {self.input_cost}, output_cost: {self.output_cost}>"
    




def llm_classification(img_path: str, model="gpt-4o-mini") -> Image:
    """
    Function to classify objects in an image using OpenAI's GPT-4 Vision API
    Args:
        img_path (str): Path to the image file to resized image
    """
    
    base64_image = encode_image(img_path)

    # Make API call to OpenAI
    # model = "gpt-4o-mini"
    response = client.chat.completions.create(
        model=model,
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
                        "text": "Return a JSON array containing labeled bounding boxes. Do not include masks, code fencing, or more than 50 objects. Each entry in the array should include: 'box_2d': The coordinates of the 2D bounding box as [x_min, y_min, x_max, y_max], 'label': The label identifying the object, 'description': A brief description of the object. If books are detected in the image, extract their titles (if legible) and append the title to the description in the format: 'Book title: [Title]'. Example output: [{\"box_2d\": [0, 0, 100, 100], \"label\": \"dog\", \"description\": \"A white dog in the image\"}]"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze the provided image and classify the objects. Return a JSON array of up to 50 objects.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )

    print(response)
    try:
        input_cost, output_cost = (
            UsageCost(model)
            .calculate_cost(response.usage.prompt_tokens, response.usage.completion_tokens)
        )
        total_cost = input_cost + output_cost
        llm_usage = LLMUsasge(
            model=response.model,
            completion_tokens=response.usage.completion_tokens,
            prompt_tokens=response.usage.prompt_tokens,
            total_tokens=response.usage.total_tokens,
            message=response.choices[0].message.content,
            input_cost=input_cost,
            output_cost=output_cost,
            cost=total_cost
        )
        db.session.add(llm_usage)
        db.session.commit()
    except Exception as e:
        print(e)
    
    

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


# ChatCompletion(
#     id='chatcmpl-AlrMc6z1X2gIKP6S9JHjNoDucXrvS',
#     choices=[
#         Choice(
#             finish_reason='stop',
#             index=0,
#             logprobs=None,
#             message=ChatCompletionMessage(
#                 content='{\n  "objects": [\n    {\n      "box_2d": [10, 50, 130, 150],\n      "label": "book",\n      "description": "A book 
# titled \'ROCKET SCIENCE for babies\' by Ferrie."\n    },\n    {\n      "box_2d": [140, 50, 230, 150],\n      "label": "book",\n      
# "description": "A book titled \'First Numbers\' with a yellow cover."\n    },\n    {\n      "box_2d": [240, 50, 330, 150],\n      "label": 
# "book",\n      "description": "A book titled \'ABC ELEMENTS\' with a blue cover."\n    },\n    {\n      "box_2d": [350, 50, 400, 150],\n      
# "label": "book",\n      "description": "A book titled \'GRAY\'."\n    },\n    {\n      "box_2d": [0, 0, 100, 100],\n      "label": "hand",\n  
# "description": "A hand holding the books."\n    },\n    {\n      "box_2d": [100, 0, 150, 100],\n      "label": "soft toy",\n      
# "description": "A white soft toy partially visible in the image."\n    }\n  ]\n}',
#                 refusal=None,
#                 role='assistant',
#                 audio=None,
#                 function_call=None,
#                 tool_calls=None
#             )
#         )
#     ],
#     created=1735969910,
#     model='gpt-4o-mini-2024-07-18',
#     object='chat.completion',
#     service_tier=None,
#     system_fingerprint='fp_d02d531b47',
#     usage=CompletionUsage(
#         completion_tokens=284,
#         prompt_tokens=1056,
#         total_tokens=1340,
#         completion_tokens_details=CompletionTokensDetails(
#             accepted_prediction_tokens=0,
#             audio_tokens=0,
#             reasoning_tokens=0,
#             rejected_prediction_tokens=0
#         ),
#         prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)
#     )
# )