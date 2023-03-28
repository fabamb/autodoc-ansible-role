import os
import yaml
import re
import argparse
import os
import sys
from tabulate import tabulate
from jinja2 import Environment, FileSystemLoader
from jinja2 import Template

TEMPLATE = """

# {{ meta_info['galaxy_info']['role_name'] }}

- [1. Description](#description)
- [2. Environments](#environments)
- [3. Requirements](#requirements)
- [4. Dependencies](#dependencies)
- [5. Variables](#variables)
- [6. Procedure](#procedure)
- [7. Usage](#usage)
  - [7.1. Example Playbook](#example-playbook)
- [8. Known problems and limitations](#known-problems-and-limitations)
- [9. Author Information](#9-author-information)

## 1. Description

{{ meta_info['galaxy_info']['description'] }}

## 2. Environments

{% if platforms | length > 0 -%}
This role has been tested as per following table

{{ tabulate(platforms, headers={'name': 'Name', 'versions': 'Versions', 'comments': 'Comments'}, tablefmt='pipe', showindex=False) }}
{% else -%}
None
{% endif %}

## 3. Requirements

<!-- If the role has any pre-requisites that are not covered by Ansible itself or the role's functionality, mention them here. -->
None

## 4. Dependencies

{% if meta_info['dependencies'] | length > 0 -%}
{% for dependency in meta_info['dependencies'] -%}
- {{ dependency }}
{% endfor %}
{% else -%}
None
{% endif %}

## 5. Variables

### 5.1 Mandatory variables

{% if mandatory_vars_table | length > 0 -%}
The following table lists the mandatory_vars_table variables for this role, along with a description.

{{ tabulate(mandatory_vars_table, headers='keys', tablefmt='pipe', showindex=False) }}
{% else -%}
None
{% endif %}

### 5.2 Default variables

{% if default_vars_table | length > 0 -%}
The following table lists the configurable variables for this role, along with their default values and a description.

{{ tabulate(default_vars_table, headers='keys', tablefmt='pipe', showindex=False) }}
{% else -%}
None
{% endif %}

## 6. Procedure

Before using the role, add the following lines to your requirements.yaml and run the command `ansible-galaxy -r requirements.yml {{ meta_info['galaxy_info']['role_name'] }}

```yaml
- name: {{ meta_info['galaxy_info']['role_name'] }}
{%- if clone_url %}
  src: git+{{ clone_url }}
{%- else %}
  src: git+https://github.com/user/{{ meta_info['galaxy_info']['role_name'] }}.git
{%- endif %}
  type: git

```

## 7. Usage

### 7.1 Example Playbook

```yaml
{%- if example_content -%}
{{ example_content }}
{%- else %}
- hosts: servers
  roles:
    - role: {{ meta_info['galaxy_info']['role_name'] }}
{%- if mandatory_vars_table | length > 0 %}
      vars:      
{%- for var in mandatory_vars_table %}
        - {{ var["Name"] }}: <{{ var["Name"] }}>
{%- endfor %}
{%- endif %}
{%- endif %}
```

## 8. Known problems and limitations

<!--  This section can be used to explain some knowing problems and limitation of this implementation. It's can be usefull to avoid that someone open issue for something that maintainer already know. -->
None

## 9. Author Information

{{ meta_info['galaxy_info']['author'] }}
"""

def check_role_structure(role_path):
    required_dirs_and_files = {
        'defaults': ['main.yml'],
        'files': [],
        'handlers': [],
        'meta': ['main.yml'],
        'tasks': [],
        'templates': [],
        'vars': ['main.yml']
    }
    for directory, required_files in required_dirs_and_files.items():
        dir_path = os.path.join(role_path, directory)
        if not os.path.isdir(dir_path):
            print(f"Error: The {directory} directory is missing in the role path: {role_path}")
            return False
        
        for required_file in required_files:
            file_path = os.path.join(dir_path, required_file)
            if not os.path.isfile(file_path):
                print(f"Error: The required file {required_file} is missing in the {directory} directory: {file_path}")
                return False

    return True

def check_meta_info(meta_info):
    required_fields = ['role_name', 'author', 'description']

    if 'galaxy_info' not in meta_info:
        print("Error: 'galaxy_info' is missing in meta/main.yml")
        return False

    galaxy_info = meta_info['galaxy_info']

    for field in required_fields:
        if field not in galaxy_info:
            print(f"Error: '{field}' is missing in 'galaxy_info' in meta/main.yml")
            return False
        if not galaxy_info[field]:
            print(f"Error: '{field}' in 'galaxy_info' in meta/main.yml is empty")
            return False

    return True

def load_yaml_file(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def load_vars_file(file_path):
    variables = {}
    current_comment = None

    def get_type_name(value):
        if isinstance(value, str):
            return "string"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        else:
            return value.__class__.__name__

    # Load variables with yaml.safe_load
    with open(file_path, 'r') as f:
        yaml_variables = yaml.safe_load(f)

    # Extract comments
    with open(file_path, 'r') as f:
        lines = f.readlines()

    for i in range(len(lines)):
        stripped_line = lines[i].strip()

        if stripped_line.startswith('#'):
            temp_comment = stripped_line[1:].strip()
            if i + 1 < len(lines) and ':' in lines[i + 1].strip():
                current_comment = temp_comment
            else:
                current_comment = ""
        elif ':' in stripped_line:
            key, _ = [s.strip() for s in stripped_line.split(':', 1)]
            if key in yaml_variables:
                parsed_value = yaml_variables[key]
                variables[key] = {'value': parsed_value, 'type': get_type_name(parsed_value), 'description': current_comment, 'comments': ""}
                current_comment = ""

    return variables

def get_default_vars_table(default_vars):
    default_vars_table = []
    for var_name, var_info in default_vars.items():
        default_vars_table.append({"Name": var_name,
            "Type": var_info["type"],
            "Description": var_info["description"],
            "Value": var_info["value"],
            "Comments": var_info["comments"]
        })

    return default_vars_table

def find_mandatory_variables(tasks_file):
    mandatory_vars = set()

    def extract_vars_from_assert(assert_task):
        if "that" in assert_task:
            for condition in assert_task["that"]:
                is_defined_match = re.search(r'(\w+)\s+is\s+defined', condition)
                if is_defined_match:
                    var_name = is_defined_match.group(1)
                    mandatory_vars.add(var_name)

    with open(tasks_file, 'r') as f:
        tasks = yaml.safe_load(f)

    for task in tasks:
        if "block" in task:
            for block_task in task["block"]:
                if "ansible.builtin.assert" in block_task:
                    extract_vars_from_assert(block_task["ansible.builtin.assert"])
                elif "assert" in block_task:
                    extract_vars_from_assert(block_task["assert"])
        elif "ansible.builtin.assert" in task:
            extract_vars_from_assert(task["ansible.builtin.assert"])
        elif "assert" in task:
            extract_vars_from_assert(task["assert"])

    return mandatory_vars

def find_mandatory_variables_in_folder(folder):
    all_mandatory_vars = set()

    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith('.yml') or file.endswith('.yaml'):
                file_path = os.path.join(root, file)
                mandatory_vars = find_mandatory_variables(file_path)
                all_mandatory_vars.update(mandatory_vars)

    return all_mandatory_vars

def get_mandatory_vars_table(mandatory_vars, vars_file_path):
    mandatory_vars_file = load_vars_file(vars_file_path)
    mandatory_vars_table = []

    for var_name in mandatory_vars:
        if var_name in mandatory_vars_file:
            var_type = mandatory_vars_file[var_name]['type']
            var_description = mandatory_vars_file[var_name]['description']
            var_comments = mandatory_vars_file[var_name]['comments']
        else:
            var_type = ""
            var_description = ""
            var_comments = ""

        mandatory_vars_table.append({
            "Name": var_name,
            "Type": var_type,
            "Description": var_description,
            "Comments": var_comments,
        })

    return mandatory_vars_table

def get_example_content(example_file):
    if os.path.exists(example_file):
        with open(example_file, 'r') as file:
            example_content = file.read()
    else:
        example_content = None
    return example_content

def get_platforms_table(meta_info):
    platforms = meta_info.get('galaxy_info', {}).get('platforms', [])

    platforms_table = tabulate(
        platforms,
        headers={"name": "Name", "versions": "Versions", "comments": "Comments"},
        tablefmt="pipe",
        missingval=""
    )

    return platforms_table

def generate_readme(meta_info, platforms, default_vars_table, mandatory_vars_table, example_content, clone_url, output_path):
    if not output_path:
        output_path="README.md"

    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # env = Environment(loader=FileSystemLoader(script_dir))
    # template = env.get_template('readme.md.j2')
    
    template = Template(TEMPLATE)


    with open(output_path, 'w') as f:
        f.write(template.render(
            meta_info=meta_info, 
            platforms=platforms,
            default_vars_table=default_vars_table, 
            mandatory_vars_table=mandatory_vars_table, 
            example_content=example_content,
            clone_url=args.clone_url,
            tabulate=tabulate
        ))

def main(args):
    role_path = args.role_path
    output_path = args.output_path
    clone_url = args.clone_url

    if not check_role_structure(role_path):
        print("The Ansible role structure is not valid. Exiting.")
        sys.exit(1)

    meta_info = load_yaml_file(os.path.join(role_path, 'meta/main.yml'))
    if not check_meta_info(meta_info):
        sys.exit(1)

    default_vars = load_vars_file(os.path.join(role_path, 'defaults/main.yml'))
    default_vars_table = get_default_vars_table(default_vars)

    mandatory_vars = find_mandatory_variables_in_folder(os.path.join(role_path, 'tasks'))
    mandatory_vars = sorted(list(mandatory_vars))
    mandatory_vars_table = get_mandatory_vars_table(mandatory_vars, os.path.join(role_path, 'vars/main.yml'))

    example_content = get_example_content(os.path.join(role_path, 'example.yml'))    

    # platforms_table = get_platforms_table(meta_info)
    platforms = meta_info.get('galaxy_info', {}).get('platforms', [])

    generate_readme(
        meta_info=meta_info,
        platforms=platforms,
        default_vars_table=default_vars_table,
        mandatory_vars_table=mandatory_vars_table,
        example_content=example_content,
        clone_url=args.clone_url,
        output_path=output_path
    )

def parse_args():
    parser = argparse.ArgumentParser(description="Generate a README.md file for an Ansible role.")
    parser.add_argument('--role-path', '-r', default='.', help="The path to the Ansible role directory. Default: current directory")
    parser.add_argument('--clone-url', '-u', dest='clone_url', default=None, help='Url to clone the project.')
    parser.add_argument('--output', '-o', dest='output_path', help='Path to the output directory for the README.md file', default=None)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(args)
