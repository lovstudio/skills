#!/usr/bin/env python3
import os
import sys
import argparse
import time
import io
import subprocess
import shutil
from PIL import Image
from google import genai
from google.genai import types

def generate_image(prompt, output_file, quality='low', show_ascii=False):
    # Get API key from environment
    api_key = os.environ.get("ZENMUX_API_KEY")
    if not api_key:
        print("Error: ZENMUX_API_KEY environment variable is not set.")
        sys.exit(1)

    client = genai.Client(
        api_key=api_key,
        vertexai=True,
        http_options=types.HttpOptions(
            api_version='v1',
            base_url='https://zenmux.ai/api/vertex-ai'
        ),
    )

    print(f"Generating image for prompt: {prompt[:50]}...")

    try:
        # Map quality string to MediaResolution enum
        resolution_map = {
            'low': types.MediaResolution.MEDIA_RESOLUTION_LOW,
            'medium': types.MediaResolution.MEDIA_RESOLUTION_MEDIUM,
            'high': types.MediaResolution.MEDIA_RESOLUTION_HIGH
        }

        # Default to low if not specified or invalid
        resolution = resolution_map.get(quality, types.MediaResolution.MEDIA_RESOLUTION_LOW)

        response = client.models.generate_content(
            model="google/gemini-3-pro-image-preview",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                media_resolution=resolution
            )
        )

        image_saved = False
        if response.parts:
            for part in response.parts:
                if part.text is not None:
                    print(f"Model response: {part.text}")
                if part.inline_data is not None:
                    # Get raw bytes
                    img_data = part.inline_data.data

                    # Save to file
                    with open(output_file, 'wb') as f:
                        f.write(img_data)
                    print(f"Image saved successfully to {output_file}")

                    # Open image with system viewer (macOS)
                    if sys.platform == 'darwin':
                        try:
                            subprocess.run(["open", output_file], check=False)
                            print(f"Opened image in default viewer.")
                        except Exception as e:
                            print(f"Warning: Failed to open image: {e}")

                    # Optional ASCII preview
                    if show_ascii:
                        try:
                            # Create PIL Image for ASCII preview
                            image = Image.open(io.BytesIO(img_data))
                            print("\n" + "="*40)
                            print("ASCII PREVIEW")
                            print("="*40)
                            print_ascii(image)
                            print("\n" + "="*40)
                        except Exception as e:
                            print(f"Warning: Could not generate ASCII preview: {e}")

                    image_saved = True
        else:
            print("Response contained no parts.")

        if not image_saved:
            print("No image was returned in the response.")
            sys.exit(1)

    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def print_ascii(image, width=60):
    """Prints an ASCII representation of the image."""
    try:
        # Determine dimensions safely
        if hasattr(image, 'size'):
            img_width, img_height = image.size
        elif hasattr(image, 'width') and hasattr(image, 'height'):
            img_width = image.width
            img_height = image.height
        else:
            # Try to force load if it's a lazy object or similar
            if hasattr(image, 'load'):
                image.load()
                if hasattr(image, 'size'):
                    img_width, img_height = image.size
                else:
                    print(f"Cannot determine dimensions for object: {type(image)}")
                    return
            else:
                print(f"Cannot determine dimensions for object: {type(image)}")
                return

        aspect_ratio = img_height / img_width
        # Terminal characters are roughly twice as tall as they are wide
        new_height = int(width * aspect_ratio * 0.5)

        # Ensure minimum dimensions
        if new_height < 1: new_height = 1

        # Resize image
        img = image.resize((width, new_height))
        # Convert to grayscale
        img = img.convert('L')

        pixels = list(img.getdata())

        # ASCII chars from dark to light
        chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]

        # Map pixels to characters
        new_pixels = [chars[pixel * (len(chars)-1) // 255] for pixel in pixels]
        new_pixels = ''.join(new_pixels)

        # Split string of chars into multiple strings of length equal to new width and print
        new_pixels_count = len(new_pixels)
        ascii_image = [new_pixels[index:index + width] for index in range(0, new_pixels_count, width)]
        print("\n".join(ascii_image))
    except Exception as e:
        print(f"Error creating ASCII art: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate images using ZenMux/Gemini")
    parser.add_argument("prompt", help="The image description prompt")
    parser.add_argument("-o", "--output", default="generated_image.png", help="Output filename")
    parser.add_argument("-q", "--quality", choices=['low', 'medium', 'high'], default="low", help="Image generation quality (default: low)")
    parser.add_argument("--ascii", action="store_true", help="Show ASCII preview in terminal")

    args = parser.parse_args()

    generate_image(args.prompt, args.output, args.quality, args.ascii)
