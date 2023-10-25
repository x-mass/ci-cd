import argparse
import os
import xml.etree.ElementTree as ET

from github import Github
from github.IssueComment import IssueComment


def parse_junit_xml(path):
    tree = ET.parse(path)
    root = tree.getroot()

    success_results = []
    failure_results = []
    os_type, compiler, build_type, _ = path.split(os.sep)[-4:]

    for testcase in root.findall('.//testcase'):
        name = testcase.get('name')
        classname = testcase.get('classname')
        failure = testcase.find('failure')

        full_test_name = f"{classname}/{name} ({os_type},{compiler},{build_type})"

        if failure is not None:
            failure_results.append(f"🔴 {full_test_name}")
        else:
            success_results.append(f"✅ {full_test_name}")

    return success_results, failure_results


def post_results_to_github(token, repo_name, pr_number, message):
    g = Github(token)
    repo = g.get_repo(repo_name)
    pull = repo.get_pull(pr_number)

    COMMENT_TAG = "## Tests Diff from Master"

    comments = pull.get_issue_comments()

    existing_comment: IssueComment = next((comment for comment in comments if COMMENT_TAG in comment.body), None)

    if existing_comment is not None:
        existing_comment.edit(message)
    else:
        pull.create_issue_comment(COMMENT_TAG + "\n" + message)


def main():
    parser = argparse.ArgumentParser(description="Parse JUnit results and post to GitHub PR")
    parser.add_argument('repo', type=str, help='GitHub repository in format "owner/repo"')
    parser.add_argument('pr_number', type=int, help='PR number inside GitHub repository')
    parser.add_argument('results_directory', type=str, help='Directory containing test result files')
    args = parser.parse_args()

    all_success_results = []
    all_failure_results = []

    for root, _, files in os.walk(args.results_directory):
        for file in files:
            if file.endswith(".xml"):
                success_results, failure_results = parse_junit_xml(os.path.join(root, file))
                all_success_results.extend(success_results)
                all_failure_results.extend(failure_results)

    message = ""
    if all_success_results:
        message += "<details><summary>New Successful Tests</summary>\n\n"
        message += '\n'.join(all_success_results)
        message += "\n</details>\n\n"

    if all_failure_results:
        message += "<details><summary>New Failed Tests</summary>\n\n"
        message += '\n'.join(all_failure_results)
        message += "\n</details>"

    token = os.environ['GITHUB_TOKEN']

    post_results_to_github(token, args.repo, args.pr_number, message)


if __name__ == "__main__":
    main()
