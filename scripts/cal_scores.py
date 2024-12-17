import csv
import argparse
from collections import defaultdict

# Task ID categories
CATEGORIES = {
    "T2I": {"24", "26", "28"},
    "I2I": {"63", "72"},
    "Is2I": {"64", "65", "73"},
    "T2Is": {"14", "15", "16", "17"},
    "Is2Is": {"44", "45", "46", "49"},
}

def process_csv(file_path):
    """Process the CSV file to calculate scores according to the specified rules."""
    # Step 1: Validate CSV file structure
    with open(file_path, mode="r", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        headers = next(reader)
        rows = list(reader)
    
    if len(rows) != 306:
        raise ValueError("The CSV file does not contain 306 rows of results.")
    
    missing_scores_rows = []
    for i, row in enumerate(rows, start=2):  # Start counting from 2 to include the header line
        if not (row[7].isdigit() and row[10].isdigit() and row[13].isdigit()):  # Check scores
            missing_scores_rows.append(i)
    
    if missing_scores_rows:
        raise ValueError(f"Some rows are missing scores. Rows with issues: {missing_scores_rows}")
    
    # Step 2: Group by task_id and case_id
    case_scores = defaultdict(lambda: [[], [], []])  # { (task_id, case_id): [[scores1], [scores2], [scores3]] }
    task_names = {}  # Map task_id to task_name
    for row in rows:
        task_name, task_id, case_id = row[0], row[1], row[2]
        question_id = int(row[3])
        scores = [int(row[7]), int(row[10]), int(row[13])]  # Extract scores from 3 API calls
        case_scores[(task_id, case_id)][0].append((question_id, scores[0]))
        case_scores[(task_id, case_id)][1].append((question_id, scores[1]))
        case_scores[(task_id, case_id)][2].append((question_id, scores[2]))
        task_names[task_id] = task_name  # Store task_name for each task_id
    
    # Step 2: Process each case
    case_results = defaultdict(list)  # { task_id: [case_scores] }
    for (task_id, case_id), score_lists in case_scores.items():
        case_final_scores = []
        for api_index, scores in enumerate(score_lists):
            # Sort by question_id
            scores.sort(key=lambda x: x[0])
            # Apply scoring rules
            final_scores = [score for _, score in scores]
            if final_scores[0] == 0 or final_scores[1] == 0:  # Question 1 and 2 not full score
                final_scores[2:] = [0] * 4
            elif final_scores[2] == 0 or final_scores[3] == 0:  # Question 3 and 4 not full score
                final_scores[4:] = [0] * 2
            case_final_scores.append(sum(final_scores) / 6)  # Average score for the API call
        case_results[task_id].append(sum(case_final_scores) / 3)  # Average score across 3 API calls
    
    # Step 4: Calculate task-level scores
    task_results = {}
    for task_id, scores in case_results.items():
        task_average = sum(scores) / len(scores)
        task_results[task_id] = (task_average / 6) * 100  # Convert to percentage
    
    # Step 5: Calculate category-level scores
    category_results = {category: [] for category in CATEGORIES}
    for task_id, score in task_results.items():
        for category, task_ids in CATEGORIES.items():
            if task_id in task_ids:
                category_results[category].append(score)
                break

    category_averages = {}
    for category, scores in category_results.items():
        if scores:
            category_averages[category] = sum(scores) / len(scores)
        else:
            category_averages[category] = 0.0

    overall_average = sum(category_averages.values()) / len(category_averages)

    # Print the results
    print("Task Scores (Percentage):")
    for task_id, score in sorted(task_results.items()):
        task_name = task_names[task_id]
        print(f"Task {task_id} ({task_name}): {score:.2f}")

    print("\nCategory Scores (Percentage):")
    for category, average in category_averages.items():
        print(f"{category}: {average:.2f}")
    
    print(f"\nOverall Average Score: {overall_average:.2f}")

def main():
    """Main function to process the CSV file."""
    parser = argparse.ArgumentParser(description="Process a CSV file to calculate task scores.")
    parser.add_argument("csv_path", type=str, help="Path to the input CSV file.")
    args = parser.parse_args()
    
    try:
        process_csv(args.csv_path)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()