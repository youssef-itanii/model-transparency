import os
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

def post_comment(body):
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{PR_NUMBER}/comments'
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

def latest_coverage_comment_id():
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/comments'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }


    response = requests.get(url, headers=headers)
    if response.status_code == 200:
            comments = response.json()
            for comment in reversed(comments):
                if 'coverage' in comment['body'].lower() and PR_NUMBER in comment['issue_url']:
                    return comment['id']
            return None  # No coverage comment found
    else:
        print(f'Failed to fetch comments: {response.json()}')
        return None

def update_coverage_comment(id, body):
    url = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/comments/{id}'
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

def main():
    if(SHA == ""): return
    with open(FILE_PATH, 'r') as file:
        lines = file.readlines()
    perma_link = f'https://github.com/{REPO_OWNER}/{REPO_NAME}/blob/{SHA}'
    message = f"### Your code does not achieve 100 percent coverage on {OS} with python version {VERSION} \
            \n\n \
            Please attempt to implement tests to test the following:\n"
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
        
    comment_id = latest_coverage_comment_id()
    if(comment_id == None):
        post_comment(message)
    else:
        update_coverage_comment(comment_id, message)


if __name__ == '__main__':
    main()
