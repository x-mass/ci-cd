import argparse
import json
import os

from github import Github

from common import extract_related_prs, get_syncwith_issue


def main():
    parser = argparse.ArgumentParser(description='Process SyncWith PRs')
    parser.add_argument('repo_name', help='Repository in format "Org/Repo"')
    parser.add_argument('pr_number', type=int, help='Pull request number')
    args = parser.parse_args()

    token = os.environ.get("CI_TOKEN")
    if not token:
        raise ValueError("GitHub personal access token not provided in the environment variable 'CI_TOKEN'.")

    g = Github(token)

    repo = g.get_repo(args.repo_name)
    pr = repo.get_pull(args.pr_number)

    issue = get_syncwith_issue(g, pr.title)

    output_data = {}
    linked_prs = extract_related_prs(g, issue)
    for linked_pr in linked_prs:
        pr_repo = linked_pr.head.repo
        output_data[pr_repo.full_name] = {
            "branch": linked_pr.head.ref,
            "pr_number": linked_pr.number,
            "sha": pr_repo.get_commits()[0].sha,
        }

    print(json.dumps(output_data))


if __name__ == "__main__":
    main()
