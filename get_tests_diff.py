import os
import argparse
import xml.etree.ElementTree as ET
from shutil import copy2


def parse_xml(file_path):
    if not os.path.exists(file_path):
        return None
    tree = ET.parse(file_path)
    return tree.getroot()


def is_passed(testcase):
    for child in testcase:
        if child.tag in ['failure', 'error']:
            return False
    return True


def process_single_file(src_file, comparator_file, output_file, ignore_modified=False):
    src_root = parse_xml(src_file)
    comparator_root = parse_xml(comparator_file)

    if comparator_root is None:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        copy2(src_file, output_file)
        return

    modified_root = ET.Element("testsuite")

    failures = 0
    for testcase in src_root.findall('.//testcase'):
        name = testcase.get('name')
        comparator_testcase = comparator_root.find(f".//testcase[@name='{name}']")

        if comparator_testcase is None:
            modified_root.append(testcase)
            if not is_passed(testcase):
                failures += 1
        else:
            src_status = is_passed(testcase)
            comparator_status = is_passed(comparator_testcase)

            if ignore_modified and src_status != comparator_status:
                continue

            if src_status != comparator_status:
                modified_root.append(testcase)
                if not src_status:
                    failures += 1

    if len(modified_root) > 0:
        modified_root.set('tests', str(len(modified_root.findall('testcase'))))
        modified_root.set('failures', str(failures))

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        tree = ET.ElementTree(modified_root)
        tree.write(output_file)


def process_files(src_folder, comparator_folder, output_folder, ignore_modified=False):
    for root, _, files in os.walk(src_folder):
        for file in files:
            if file.endswith('.xml'):
                src_file = os.path.join(root, file)
                relative_path = os.path.relpath(src_file, src_folder)
                comparator_file = os.path.join(comparator_folder, relative_path)
                output_file = os.path.join(output_folder, relative_path)

                process_single_file(src_file, comparator_file, output_file, ignore_modified)


def main():
    parser = argparse.ArgumentParser(description='Compare JUnit test results.')
    parser.add_argument('current_results', type=str, help='Path to the current test results.')
    parser.add_argument('prev_results', type=str, help='Path to the previous test results.')
    parser.add_argument('output_path', type=str, help='Path to the output directory.')
    args = parser.parse_args()

    current_results = args.current_results
    prev_results = args.prev_results
    output_path = args.output_path

    modified_or_added_folder = os.path.join(output_path, 'modified_or_added')
    removed_folder = os.path.join(output_path, 'removed')

    os.makedirs(modified_or_added_folder, exist_ok=True)
    os.makedirs(removed_folder, exist_ok=True)

    # Process modifications or additions
    process_files(current_results, prev_results, modified_or_added_folder)

    # Process removals
    process_files(prev_results, current_results, removed_folder, ignore_modified=True)


if __name__ == '__main__':
    main()
