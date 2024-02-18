# action-doc-update

This respository contains a GitHub action implemented in Python to automate
posting documentation links. 

It currently performs the following tasks:

- Parses the PR changes to detect if any file used for documentation is changed
- Constructs a message containing the link to the updated documentation
- Posts a message with the link to the updated docs

See [action.yml](action.yml) for a full list of options.
