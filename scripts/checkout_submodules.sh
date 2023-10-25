#!/bin/bash

# The first argument is a JSON string with the submodule paths and SHAs.
# Example of JSON argument: '{"org/repo1": "sha1", "org/repo2": "sha2"}'

submodules_json="$1"

# Validate the JSON input
if ! jq empty <<< "$submodules_json" ; then
    echo "Invalid JSON input."
    exit 1
fi

# Parse the JSON input into an associative array
declare -A submodules
while IFS="=" read -r key value; do
    submodules["$key"]="$value"
done < <(echo "$submodules_json" | jq -r "to_entries|map(\"\(.key)=\(.value|tostring)\")|.[]")

# Iterate over the submodule paths defined in the .gitmodules file
while read -r submodule_path; do
    submodule_name=$(basename "$(dirname "$submodule_path")")/$(basename "$submodule_path")
    sha="${submodules[$submodule_name]}"

    if [[ -z "$sha" ]]; then
        echo "No SHA specified for submodule $submodule_path ($submodule_name), skipping."
    else
        echo "Checking out submodule $submodule_path ($submodule_name) to SHA $sha."
        git -C "$submodule_path" checkout "$sha" || {
            echo "Failed to checkout submodule $submodule_path ($submodule_name) to SHA $sha."
            exit 1
        }
    fi
done < <(git config --file .gitmodules --get-regexp path | awk '{ print $2 }')

echo "Submodule checkout complete."
