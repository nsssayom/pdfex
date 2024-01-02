import os
import cv2
import csv
import re
import numpy as np
import pytesseract
from pdf2image.pdf2image import convert_from_path
from tqdm import tqdm
import json
import platform

# Create a log file if it doesn't exist
if not os.path.exists("extract.log"):
    with open("extract.log", "w") as f:
        json.dump({}, f)

# Read the log file and store the processed files and pages in a dictionary
with open("extract.log", "r") as f:
    processed_files = json.load(f)

# Check the operating system
if platform.system() == "Linux":
    # Check if it's an Arch-based system
    if os.path.exists("/etc/arch-release"):
        os.environ["TESSDATA_PREFIX"] = "/usr/share/tessdata/"
    else:
        os.environ["TESSDATA_PREFIX"] = "/usr/share/tesseract-ocr/4.00/tessdata/"

def write_to_csv(data, meta, filename):
    # Combine data and meta keys
    keys = list(data.keys()) + list(meta.keys())

    # Check if file exists
    file_exists = False
    try:
        with open(filename, "r") as f:
            file_exists = True
    except FileNotFoundError:
        pass

    # Open the file in append mode
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)

        # If file does not exist, write the header
        if not file_exists:
            writer.writeheader()

        # Combine data and meta into one dictionary
        row = {**data, **meta}

        # Write the row to the CSV file
        writer.writerow(row)


def extractMeta(text):
    # Define the keys to extract
    keys = [
        "অঞ্চল",
        "সিটি কর্পোরেশন/ পৌরসভা",
        "ওয়ার্ড নম্বর (ইউনিয়ন পরিষদের জন্য)",
        "ভোটার এলাকার নাম",
        "জেলা",
        "ইউনিয়ন/ওয়ার্ড/ক্যাঃ বোঃ",
        "ভোটার এলাকার নম্বর",
        "প্রকাশের তারিখ",
        "উপজেলা/থানা",
        "পোষ্টকোড",
    ]

    meta = {}

    # Split the text into lines
    lines = text.split("\n")

    # For each line, check if it contains a key and if so, extract the value and update the dictionary
    for line in lines:
        for key in keys:
            if key in line:
                # Escape parentheses in the key
                escaped_key = key.replace("(", "\\(").replace(")", "\\)")
                # Extract the value using a regular expression
                value = re.search(f"{escaped_key} *: (.*)", line)

                if value:
                    meta[key] = value.group(1)
    return meta


def extractData(text):
    # Define the keys
    keys = ["id", "নাম", "ভোটার নং", "পিতা", "মাতা", "ঠিকানা"]

    # Initialize a dictionary to store the extracted data
    data = {}

    # Extract the id
    id_match = re.search(r"(\d+)\.", text)
    if id_match:
        data["id"] = id_match.group(1)
    else:
        data["id"] = "-1"

    # Extract the other data
    for key in keys[1:]:
        # Escape parentheses in the key
        escaped_key = key.replace("(", "\\(").replace(")", "\\)")
        # Extract the value using a regular expression
        value = re.search(f"{escaped_key}: (.*)", text)
        if value:
            # Escape commas in the value
            escaped_value = value.group(1).replace(",", "\\,")
            data[key] = escaped_value
        else:
            data[key] = "--"

    # Extract the "পেশা" and "জন্ম তারিখ" fields separately
    pesha_jonmo = re.search("পেশা:(.*),জন্ম তারিখ:(.*)", text)
    if pesha_jonmo:
        data["পেশা"] = pesha_jonmo.group(1).strip()
        data["জন্ম তারিখ"] = pesha_jonmo.group(2).strip()
    else:
        data["পেশা"] = "--"
        data["জন্ম তারিখ"] = "--"

    return data


def segment_pdf(file_path):
    # Convert the PDF to images
    images = convert_from_path(file_path)
    meta = {}

    with tqdm(total=len(images), desc=f"Processing pages of {file_path}") as pbar:
        for i, image in enumerate(images):
            pbar.set_description(f"Processing page {i+1}/{len(images)} of {file_path}")

            # Skip the file or page if it's already processed
            if file_path in processed_files and i in processed_files[file_path]:
                continue

            if i < 2:  # Skip the first two pages
                continue

            # Convert the image to grayscale
            gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)

            # Convert the grayscale image back to a color image for visualization
            color = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            # Get the dimensions of the image
            height, width = gray.shape

            # Define global padding variables
            global_pad_left = 180
            global_pad_right = 180
            global_pad_top = 80
            global_pad_bottom = 220

            # Adjust the width and height of the image according to the global padding
            width = width - global_pad_left - global_pad_right
            height = height - global_pad_top - global_pad_bottom

            # Calculate the size of each rectangle
            rect_width = width // 3
            rect_height = height // 6

            # Define padding variables
            pad_left = 5
            pad_right = 5
            pad_top = 5
            pad_bottom = 5

            for row in range(6):
                for col in range(3):
                    # Calculate the coordinates of the rectangle with padding
                    x = global_pad_left + col * rect_width + pad_left
                    y = global_pad_top + row * rect_height + pad_top
                    w = rect_width - pad_left - pad_right
                    h = rect_height - pad_top - pad_bottom

                    # Draw the rectangle on the color image
                    cv2.rectangle(color, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # Extract the region from the grayscale image
                    region = gray[y : y + h, x : x + w]

                    custom_config = r"--oem 3 --psm 6"
                    text = pytesseract.image_to_string(
                        region, lang="ben", config=custom_config
                    )

                    # Clean up the lines
                    lines = [line.strip() for line in text.split("\n") if line.strip()]

                    # Join the lines back into a single string
                    text = "\n".join(lines)

                    # Extract the meta data from the first row of the third page
                    if row == 0 and i == 2:
                        temp_meta = extractMeta(text)
                        meta = {**meta, **temp_meta}
                        continue

                    # Extract the data from the other rows
                    data = extractData(text)

                    # Write the data to the CSV file
                    write_to_csv(data, meta, "output.csv")

            # Resize and display the color image
            # resized = cv2.resize(color, (800, 600))  # Change the dimensions as needed
            # cv2.imshow(f'Image {i+1}', resized)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
            # After processing a file or page, add it to the dictionary and log file
            if file_path not in processed_files:
                processed_files[file_path] = []
            processed_files[file_path].append(i)
            with open("extract.log", "w") as f:
                json.dump(processed_files, f)

            pbar.update()


# file_path = "sample.pdf"
# segment_pdf(file_path)

# Get a list of all PDF files in the 'data' directory and its subdirectories
pdf_files = []
for dirpath, dirnames, filenames in os.walk("data_test"):
    for filename in filenames:
        if filename.endswith(".pdf"):
            pdf_files.append(os.path.join(dirpath, filename))

# Process each PDF file
with tqdm(total=len(pdf_files), desc="Processing files") as pbar_files:
    for file_path in pdf_files:
        # Skip the file if it's fully processed
        if file_path in processed_files and len(processed_files[file_path]) == len(
            convert_from_path(file_path)
        ):
            continue

        segment_pdf(file_path)
        pbar_files.update()
