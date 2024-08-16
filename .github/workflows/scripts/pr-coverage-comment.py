import os
import sys
import requests

# Set up constants
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = "model-transparency"
PR_NUMBER = os.getenv('PR_NUMBER')
FILE_PATH = 'data.txt'
SHA = os.getenv('COMMIT_SHA')
VERSION = os.getenv('VERSION')
OS = os.getenv('OS')
URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

def post_coverage_comment(body):
    url = f'{URL}/issues/{PR_NUMBER}/comments'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'body': body,
        'issue_number': PR_NUMBER,

    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f'Posted comment: {data}')
    else:
        print(f'Failed to post comment: {response.json()}')

def get_latest_coverage_comment_id():
    url = f'{URL}/issues/{PR_NUMBER}/comments'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    print(f"PR NUMBER {PR_NUMBER}")

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
            comments = response.json()
            for comment in comments:
                if 'coverage' in comment['body'].lower() and OS in comment['body'].lower() and VERSION in comment['body']:
                    return comment['id']
            return None  # No coverage comment found
    else:
        print(f'Failed to fetch comments: {response.json()}')
        return None

def update_coverage_comment(id, body):
    url = f'{URL}/issues/comments/{id}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    data = {
        'body': body
    }
    response = requests.patch(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f'Successfully updated comment: {response.json()}')
    else:
        print(f'Failed to update comment: {response.json()}')
def parse_coverage(file_path):
    with open(file_path, 'r') as file:
        data = []
        for line in file:
            data.append(line.replace('\n', ''))
        
    return data
def construct_comment(total_coverage_data):
    """
    Constructs a formatted Markdown message for GitHub comments based on coverage data.

    Args:
        total_coverage_data (list): A list containing coverage statistics [total_statements, total_misses, total_coverage].
    Returns:
        str: A formatted Markdown message.
    """
    header = "## Coverage Report\n"
    
    # Information about the operating system and Python version
    system_info = (
        f"**Operating System:** {OS}\n"
        f"**Python Version:** {VERSION}\n\n"
    )
    
    # If coverage data is provided, include it in the message
    coverage_data = ""
    if total_coverage_data:
        coverage_data = (
            "### Coverage Statistics\n\n"
            "| Metric            | Value           |\n"
            "|-------------------|-----------------|\n"
            f"| **Total Statements** | {total_coverage_data[0]}       |\n"
            f"| **Total Misses**     | {total_coverage_data[1]}       |\n"
            f"| **Total Coverage**   | {total_coverage_data[2]}     |\n\n"
        )
    # Construct the full message
    return header + system_info + coverage_data
    
def main(total_coverage_data):
    if(SHA == ""): return
    with open(FILE_PATH, 'r') as file:
        lines = file.readlines()
    perma_link = f'https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/{SHA}'
    message = construct_comment(total_coverage_data)
    for line in lines:
        parts = line.replace(',', '').strip().split(' ')
        if len(parts) != 2:
            print(f'Invalid line format: {line.strip()}')
            continue
        file_path,range_str = parts
        if not file_path or not range_str:
            print(f'File path or range is missing in line: {line.strip()}')
            continue
        file_path = file_path.replace("\\", "/")


        if '-' in range_str:
            # Handle range
            try:
                start_line, end_line = map(int, range_str.split('-'))
                message += f'{perma_link}/{file_path}#L{start_line}-L{end_line}'

            except ValueError:
                print(f'Invalid range format: {range_str}')
        else:
            # Handle single line
            try:
                line_number = int(range_str)
                message+= f'{perma_link}/{file_path}#L{line_number}'

            except ValueError:
                print(f'Invalid line number format: {range_str}')
        message += "\n---\n"
        
    comment_id = get_latest_coverage_comment_id()
    if(comment_id == None):
        post_coverage_comment(message)
    else:
        update_coverage_comment(comment_id, message)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python parse_coverage.py <coverage_report_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    total_coverage_data = parse_coverage(file_path)
    main(total_coverage_data)
