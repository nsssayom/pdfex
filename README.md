# PDF Data Extraction

This project is designed to extract data from complex PDF files and write the extracted data to a CSV file. This can handle non-ASCII characters and complex table structures.

## Project Structure

The main script of this project is [`extract.py`](extract.py). This script walks through the `data` directory, finds all PDF files, and processes them one by one using the `segment_pdf` function.

The `segment_pdf` function converts each page of a PDF file into an image, then uses OCR (Optical Character Recognition) to extract text from the image. The extracted text is then processed to extract specific metadata and data, which are written to a CSV file.

The [`install.sh`](install.sh) script is used to set up a systemd service that runs the `extract.py` script.

## Setup

1. Install the required Python packages:

    ```sh
    pip install -r requirements.txt
    ```

2. Run the `install.sh` script to set up the systemd service:
    > This will create a new systemd service named pdfex, which will start on boot and restart automatically if it crashes. The service runs the extract.py script.

## Usage

Once the systemd service is set up, it will automatically process all PDF files in the data directory. The extracted data will be written to a CSV file named output.csv.

## Note

This project uses `Git LFS (Large File Storage)` to handle large `PDF` and `CSV` files. Make sure to install `Git LFS` before cloning the repository if you plan to work with these large files.