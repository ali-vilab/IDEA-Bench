import os
import re
import csv
import PIL.Image
import google.generativeai as genai
import json
import sys
import signal
import base64
from datetime import datetime
from tqdm import tqdm
import argparse

genai.configure(api_key="YOUR_API_KEY")

MAX_RETRIES = 10  # Maximum number of retries for API calls
TIMEOUT = 60  # Timeout in seconds for API calls

class TimeoutException(Exception):
    """Custom exception for signaling a timeout."""
    pass

def image_to_base64(image_path):
    """Convert an image to a Base64 encoded string."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')
    
def timeout_handler(signum, frame):
    """Handler for timeout signal."""
    raise TimeoutException("API call timed out.")

# Register the timeout handler
signal.signal(signal.SIGALRM, timeout_handler)

def call_gemini_api_with_base64(text_prompt, image_path):
    """Call Gemini API using Base64 encoded image."""
    try:
        # Convert image to Base64
        base64_image = image_to_base64(image_path)
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        
        # Set an alarm for the timeout
        signal.alarm(TIMEOUT)
        try:
            response = model.generate_content([text_prompt, base64_image])
            return response.text
        finally:
            signal.alarm(0)  # Cancel the alarm
    except TimeoutException:
        print(f"API call timed out for image {image_path}.")
        return "Error: Timeout"
    except Exception as e:
        print(f"Error calling Gemini API for image {image_path}: {e}")
        return "Error"

def find_first_and_last_quote(s):
    """
    Find the positions of the first and last quotes (single or double) in a string.

    Returns:
        first (int): Position of the first quote.
        last (int): Position of the last quote.
        If no quotes are found, returns (-1, -1).
    """
    # Find the first occurrence of any quote (single or double)
    first_single = s.find("'")
    first_double = s.find('"')
    
    # Select the earliest quote as the first quote
    if first_single == -1:
        first = first_double
    elif first_double == -1:
        first = first_single
    else:
        first = min(first_single, first_double)

    # Find the last occurrence of any quote (single or double)
    last_single = s.rfind("'")
    last_double = s.rfind('"')
    
    # Select the latest quote as the last quote
    if last_single == -1:
        last = last_double
    elif last_double == -1:
        last = last_single
    else:
        last = max(last_single, last_double)

    # If no quotes are found, return (-1, -1)
    if first == -1 or last == -1 or first >= last:
        return -1, -1

    return first, last

def extract_score(response):
    """Extracts the score and reason from the response."""
    try:
        # Remove surrounding ```json or ``` markers
        response_cleaned = re.sub(r"```json|```", "", response).strip()
        
        # Extract the score (the first number after 'score': or "score":)
        score_match = re.search(r'["\']score["\']\s*:\s*(\d)', response_cleaned)
        if not score_match:
            return None, "Score not found"
        score = int(score_match.group(1))  # Extracted score
        
        # Extract the reason (everything after 'reason': or "reason":)
        reason_match = re.search(r'["\']reason["\']\s*:\s*(.+)$', response_cleaned, re.DOTALL)
        if not reason_match:
            return score, "Reason not found"
        reason = reason_match.group(1)  # Full reason including potential outer quotes

        first, last = find_first_and_last_quote(reason)
        reason = reason[first+1:last]
        
        return score, reason
    except Exception as e:
        print(f"Unexpected error during parsing: {e}")
        return None, "Unexpected error"

def get_gemini_result_with_retries(text_prompt, image_path):
    """Call Gemini API with retries if parsing fails."""
    for attempt in range(1, MAX_RETRIES + 1):
        response = call_gemini_api_with_base64(text_prompt, image_path)
        score, explanation = extract_score(response)

        if score is not None:
            return response, score, explanation  # Return valid result

        print(f"Attempt {attempt}/{MAX_RETRIES} failed for case: {image_path}. Retrying...")

    return None, None, "Max retries exceeded"  # Return placeholder if all retries fail

def save_progress(rows_with_results, eval_results_csv_path, headers):
    """Save intermediate results to CSV, including headers."""
    with open(eval_results_csv_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)  # Write the headers
        writer.writerows(rows_with_results)

def main():
    """Main function."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process a summary CSV file with Gemini API.")
    parser.add_argument("summary_csv_path", type=str, help="Path to the summary CSV file.")
    parser.add_argument("--resume", type=str, help="Path to an existing CSV file to resume progress.")
    args = parser.parse_args()

    # Paths for input and output
    summary_csv_path = args.summary_csv_path
    eval_results_dir = "eval_results"
    os.makedirs(eval_results_dir, exist_ok=True)

    # Generate a unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    eval_results_csv_path = os.path.join(eval_results_dir, f"gemini_results_{timestamp}.csv")

    # Load summary CSV
    if not os.path.exists(summary_csv_path):
        print(f"Summary CSV file not found at {summary_csv_path}. Exiting.")
        return
    with open(summary_csv_path, mode="r", encoding="utf-8") as summary_file:
        summary_reader = csv.reader(summary_file)
        summary_headers = next(summary_reader)
        summary_rows = list(summary_reader)

    # Determine columns for gemini results
    for i in range(1, 4):
        summary_headers.extend([f"gemini_result_{i}", f"score_{i}", f"explanation_{i}"])

    # Load resume CSV if provided
    processed_rows = []
    if args.resume and os.path.exists(args.resume):
        print(f"Resuming from existing file: {args.resume}")
        with open(args.resume, mode="r", encoding="utf-8") as resume_file:
            resume_reader = csv.reader(resume_file)
            processed_headers = next(resume_reader)
            processed_rows = list(resume_reader)

        # Check for header mismatch
        if processed_headers != summary_headers:
            print("Header mismatch between summary CSV and resume CSV. Exiting.")
            return

    # Determine rows to process
 
    rows_to_process = summary_rows[len(processed_rows):]

    print(f"Total rows in summary: {len(summary_rows)}")
    print(f"Already processed rows: {len(processed_rows)}")
    print(f"Rows to process: {len(rows_to_process)}")

    try:
        # Process rows
        for row in tqdm(rows_to_process, desc="Processing rows", unit="row"):
            task_name, task_id, case_id, question_id, text_prompt, stitched_image_path = row

            for i in range(1, 4):  # Call API 3 times
                gemini_response, score, explanation = get_gemini_result_with_retries(text_prompt, stitched_image_path)
                if score is None:  # If retries failed, save progress and exit
                    save_progress(processed_rows, eval_results_csv_path, summary_headers)
                    print(f"Retries failed for case: {stitched_image_path}. Progress saved to {eval_results_csv_path}")
                    sys.exit(1)

                # Append result, score, and explanation for this call
                row.extend([gemini_response, score, explanation])

            processed_rows.append(row)
    except KeyboardInterrupt:
        print("Process interrupted. Saving progress...")
        save_progress(processed_rows, eval_results_csv_path, summary_headers)
        sys.exit(1)

    # Save final results
    save_progress(processed_rows, eval_results_csv_path, summary_headers)
    print(f"Updated CSV file with Gemini results saved to {eval_results_csv_path}")

if __name__ == "__main__":
    main()