import os
from pdf2image import convert_from_path


def convert_pdf_folder_to_images(
    input_folder: str,
    output_folder: str,
    dpi: int = 300,
    image_format: str = "png"
):
    """
    Converts all PDF pages in a folder to images.
    Each page is saved as one image.

    Args:
        input_folder (str): Folder containing PDF files
        output_folder (str): Folder to save images
        dpi (int): Image resolution
        image_format (str): png / jpg / tiff
    """

    os.makedirs(output_folder, exist_ok=True)

    image_count = 0

    for filename in sorted(os.listdir(input_folder)):
        if not filename.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(input_folder, filename)
        pdf_name = os.path.splitext(filename)[0]

        print(f"[INFO] Processing {filename}")

        pages = convert_from_path(pdf_path, dpi=dpi)

        for page_idx, page in enumerate(pages):
            out_name = f"{pdf_name}_page_{page_idx + 1}.{image_format}"
            out_path = os.path.join(output_folder, out_name)

            page.save(out_path, image_format.upper())
            image_count += 1

    print(f"[DONE] Saved {image_count} images")


# ------------------------------
# Example usage
# ------------------------------
if __name__ == "__main__":
    input_folder = "scrapbook"
    output_folder = "mb_images"

    convert_pdf_folder_to_images(input_folder, output_folder)
