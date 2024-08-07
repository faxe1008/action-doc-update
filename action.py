#!/usr/bin/env python3
# Copyright (c) 2024 Fabian Blatz <fabianblatz@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

# standard library imports only here
import argparse
import json
import os
from pathlib import Path
import sys

# 3rd party imports go here
from github import Github, GithubException

NOTE = "\n\n*Note: This message is automatically posted and updated by the " \
       "Document Update GitHub Action.* "

_logging = 0

def log(s):
    if _logging:
        print(s, file=sys.stdout)

def die(s):
    print(f'ERROR: {s}', file=sys.stderr)
    sys.exit(1)

def is_doc_associated_file(path):
    return path.endswith(".rst")

def get_doc_path_from_repo_root(file_path):
    # Assuming the 'doc' folder is at the repository root, we extract the relative path
    doc_root = "doc/"
    if doc_root in file_path:
        # Split the path to get the part after the doc_root
        _, doc_relative_path = file_path.split(doc_root, 1)
        return doc_relative_path
    return None

def main():

    parser = argparse.ArgumentParser(
        description="GH Action script for documentation link publication",
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-m', '--message', action='store',
                        required=False,
                        help='Message to post.')

    parser.add_argument('-v', '--verbose-level', action='store',
                        type=int, default=0, choices=range(0, 2),
                        required=False, help='Verbosity level.')

    print(sys.argv)

    args = parser.parse_args()

    global _logging
    _logging = args.verbose_level

    message = args.message if args.message != 'none' else None

    # Retrieve main env vars
    action = os.environ.get('GITHUB_ACTION', None)
    workflow = os.environ.get('GITHUB_WORKFLOW', None)
    org_repo = os.environ.get('GITHUB_REPOSITORY', None)

    log(f'Running action {action} from workflow {workflow} in {org_repo}')

    evt_name = os.environ.get('GITHUB_EVENT_NAME', None)
    evt_path = os.environ.get('GITHUB_EVENT_PATH', None)
    workspace = os.environ.get('GITHUB_WORKSPACE', None)

    log(f'Event {evt_name} in {evt_path} and workspace {workspace}')

    token = os.environ.get('GITHUB_TOKEN', None)
    if not token:
        sys.exit('Github token not set in environment, please set the '
                 'GITHUB_TOKEN environment variable and retry.')

    if not ("pull_request" in evt_name):
        sys.exit(f'Invalid event {evt_name}')

    with open(evt_path, 'r') as f:
        evt = json.load(f)

    pr = evt['pull_request']

    gh = Github(token)

    gh_repo = gh.get_repo(org_repo)
    pr_number = int(pr['number'])
    gh_pr = gh_repo.get_pull(pr_number)

    # Collect links to documentation files and construct URLs pointing to the build location
    changed_doc_files = []
    for f in gh_pr.get_files():
        if is_doc_associated_file(f.filename):
            doc_relative_path = get_doc_path_from_repo_root(f.filename)
            if doc_relative_path:
                # Replace the .rst extension with .html
                doc_path_html = doc_relative_path.replace('.rst', '.html')
                # Construct the full URL
                doc_url = f"https://builds.zephyrproject.io/zephyr/pr/{str(pr_number)}/docs/{doc_path_html}"
                url_text = os.path.basename(f.filename)
                changed_doc_files.append((url_text, doc_url))

    if len(changed_doc_files) == 0:
        log(f'No documentation files changed by this Pull Request')
        sys.exit(0)

    strs = list()
    if message:
        strs.append(message)
    strs.append('The following documentation files have been modified in this Pull Request:\n')
    for (url_text, doc_url) in changed_doc_files:
        strs.append(f"- [{url_text}]({doc_url})")

    message = '\n'.join(strs) + NOTE

    comment = None
    for c in gh_pr.get_issue_comments():
        if NOTE in c.body:
            comment = c
            break

    if not comment:
        print('Creating comment')
        comment = gh_pr.create_issue_comment(message)
    else:
        print('Updating comment')
        comment.edit(message)

    sys.exit(0)

if __name__ == '__main__':
    main()
