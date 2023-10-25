import argparse
import os
from github import Github, UnknownObjectException

from common import extract_related_prs, get_syncwith_issue


def trigger_workflow_for_repo(g, repo, sha, workflow_name):
    prs = repo.get_pulls(state='open', head=sha)

    if prs.totalCount == 0:
        print(f"No open PRs found for SHA {sha} in {repo.full_name}. Skipping...")
        return

    for pr in prs:
        pr_branch = pr.head.ref

        try:
            workflow = repo.get_workflow(workflow_name)
            workflow.create_dispatch(ref=pr_branch, inputs={"sha": sha})

        except UnknownObjectException:
            print(f"Workflow {workflow_name} not found in {repo.full_name}. Skipping for PR {pr.number}.")


def trigger_workflows(g, repo_name, pr_number, workflow_ref, ignore_repos):
    current_repo = g.get_repo(repo_name)
    issue = get_syncwith_issue(g, current_repo.get_pull(pr_number).title)
    ralated_prs = extract_related_prs(g, issue)

    workflow_path = workflow_ref.split('@')[0].split('/', 2)[-1]

    for pr in ralated_prs:
        repo = pr.base.repo
        if repo.full_name in ignore_repos:
            print(f"Ignoring rerun for {repo.full_name}")
            continue
        print([wf.name for wf in repo.get_workflows()])
        target_workflow = next((wf for wf in repo.get_workflows() if wf.path == workflow_path), None)
        if target_workflow is None:
            print(f"Workflow {workflow_path} not found at {repo.full_name}, skipping")
            continue

        workflow = repo.get_workflow(target_workflow.id)
        runs = workflow.get_runs()

        latest_run = next((run for run in runs if run.head_sha == pr.get_commits().reversed[0].sha), None)
        latest_run.rerun()
        print(f"Workflow run {latest_run.id} for '{workflow_path}' at {repo.full_name}#{pr.number} has been rerun.")


def main():
    parser = argparse.ArgumentParser(description="Trigger workflows for related PRs")
    parser.add_argument("repo_name", help="Full name of the current repository, e.g., 'org/repo'")
    parser.add_argument("pr_number", type=int, help="Number of PR")
    parser.add_argument("workflow_ref", help="Reference to workflow (${{ github.workflow_ref }})")
    parser.add_argument('--ignore-repo', action='append', help='Repo to ignore')
    args = parser.parse_args()

    token = os.environ.get("CI_TOKEN")
    if not token:
        raise ValueError("GitHub access token not provided in the environment variable 'CI_TOKEN'.")

    g = Github(token)
    trigger_workflows(g, args.repo_name, args.pr_number, args.workflow_ref, ignore_repos=args.ignore_repo)


if __name__ == "__main__":
    main()
