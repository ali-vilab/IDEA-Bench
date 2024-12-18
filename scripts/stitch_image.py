import os
import json
import csv
import argparse
from PIL import Image, ImageDraw, ImageFont


def load_image_from_local(local_path):
    """Load an image from the local file system."""
    return Image.open(local_path)


def save_image_to_local(image, local_path):
    """Save a PIL Image object to the local file system."""
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    image.save(local_path, format="JPEG")


def resize_image(img, height=512):
    """Resize images to a standard height while maintaining aspect ratio."""
    aspect_ratio = img.width / img.height
    new_width = int(height * aspect_ratio)
    return img.resize((new_width, height), Image.LANCZOS)


def stitch_images_horizontally(images):
    """Stitch images horizontally."""
    if not images:
        return None
    gap = 20
    total_width = sum(img.width for img in images) + gap * (len(images) - 1)
    max_height = max(img.height for img in images)

    stitched_row = Image.new("RGB", (total_width, max_height), (255, 255, 255))
    x_offset = 0
    for img in images:
        stitched_row.paste(img, (x_offset, 0))
        x_offset += img.width + gap

    return stitched_row


def stitch_images(input_images, output_images):
    """Stitch images based on input and output images."""
    if output_images:
        target_height = output_images[0].height
        input_images = [resize_image(img, target_height) for img in input_images]

    input_row = stitch_images_horizontally(input_images) if input_images else None
    output_row = stitch_images_horizontally(output_images) if output_images else None

    if input_row and output_row:
        total_height = input_row.height + output_row.height + 20
        stitched_image = Image.new("RGB", (max(input_row.width, output_row.width), total_height), (255, 255, 255))
        stitched_image.paste(input_row, (0, 0))
        stitched_image.paste(output_row, (0, input_row.height + 20))
    elif input_row:
        stitched_image = input_row
    else:
        stitched_image = output_row

    return stitched_image


def create_placeholder_image(output_count, width=512, height=512):
    """Create a placeholder image with a white background and black text indicating the number of outputs."""
    placeholder = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(placeholder)
    text = str(output_count)

    # Dynamically adjust font size
    font_size = min(width, height) // 2
    try:
        font = ImageFont.truetype("assets/DejaVuSans.ttf", size=font_size)
    except IOError:
        print("Warning: Unable to load 'DejaVuSans.ttf'. Using default font.")
        font = ImageFont.load_default()

    # Center the text
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2

    draw.text((text_x, text_y), text, fill="black", font=font)
    return placeholder


def process_case(case_path, source_root, output_root, stitched_root, csv_rows):
    """Process a single case directory."""
    case_id = os.path.basename(case_path)[-4:]
    meta_path = os.path.join(case_path, "meta.json")
    stitched_case_dir = case_path.replace(source_root, stitched_root)
    output_case_dir = case_path.replace(source_root, output_root)

    if not os.path.exists(meta_path):
        return

    # Load and parse meta.json
    with open(meta_path, "r", encoding="utf-8") as meta_file:
        meta_data = json.load(meta_file)
    task_name = meta_data.get("task_name", "N/A")
    uid = meta_data.get("uid", "N/A")

    # Process auto_eval.jsonl
    auto_eval_jsonl_path = os.path.join(case_path, "auto_eval.jsonl")
    if not os.path.exists(auto_eval_jsonl_path):
        return

    with open(auto_eval_jsonl_path, "r", encoding="utf-8") as jsonl_file:
        json_elements = [json.loads(line.strip()) for line in jsonl_file]

    for i, question_data in enumerate(json_elements, start=1):
        input_images_filenames = question_data.get("input_images", [])
        output_images_filenames = question_data.get("output_images", [])
        text_prompt = question_data.get("question", "")

        input_images = [
            load_image_from_local(os.path.join(case_path, img))
            for img in input_images_filenames if os.path.exists(os.path.join(case_path, img))
        ]
        output_images = [
            load_image_from_local(os.path.join(output_case_dir, img))
            for img in output_images_filenames if os.path.exists(os.path.join(output_case_dir, img))
        ]

        if len(output_images) == 0:
            continue

        # Check if "Is the number in the image the digit" is in the text prompt
        if "Is the number in the image the digit" in text_prompt:
            stitched_image = create_placeholder_image(len(output_images))
        else:
            # Stitch images
            stitched_image = stitch_images(input_images, output_images)

        # Save stitched image locally
        stitched_image_path = os.path.join(stitched_case_dir, f"000{i}.jpg")
        save_image_to_local(stitched_image, stitched_image_path)

        # Add row to CSV
        csv_rows.append([task_name, uid, case_id, i, text_prompt, stitched_image_path])


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Process image stitching and summary generation.")
    parser.add_argument("source_root", type=str, help="Path to the source root directory.")
    parser.add_argument("output_root", type=str, help="Path to the output root directory.")
    args = parser.parse_args()

    source_root = args.source_root
    output_root = args.output_root
    stitched_root = output_root + "_stitched"
    csv_output_path = os.path.join(stitched_root, "summary.csv")

    csv_rows = [["task_name", "task_id", "case_id", "question_id", "text_prompt", "stitched_image"]]

    print(source_root)
    input()
    for root, dirs, _ in os.walk(source_root):
        for case_dir in dirs:
            case_path = os.path.join(root, case_dir)
            process_case(case_path, source_root, output_root, stitched_root, csv_rows)

    os.makedirs(stitched_root, exist_ok=True)
    with open(csv_output_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(csv_rows)

    print(f"CSV file saved to {csv_output_path}")


if __name__ == "__main__":
    main()