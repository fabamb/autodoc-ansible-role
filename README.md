# AutoDoc-Ansible-Role

Generate comprehensive README.md for Ansible roles by analyzing role structure and variables.

autodoc-role.py  is a Python script  that automates the process of generating a comprehensive README.md file for your Ansible roles. By analyzing the role structure, including meta, default and vars files, as well as the tasks' assert statements, the script extracts essential information such as role variables, default values, dependencies, and mandatory variables. The script also supports handling an optional example playbook file or generating one based on the mandatory variables found.

The script examines comments associated with default and mandatory variables to provide a detailed description for each variable. It identifies required variables based on asserts within tasks and constructs an example playbook using the provided example.yml file or, if not present, creates one using the mandatory variables. Furthermore, it utilizes the optional --clone-url parameter to specify the URL for cloning the role project in the usage instructions.

## Features

- Extracts role metadata from meta/main.yml, including role_name, description, author, dependencies, and platforms.
- Parses defaults/main.yml to gather default variables and their descriptions based on associated comments.
- Parses vars/main.yml to find required variables and their descriptions from associated comments.
- Analyzes assert statements in task files to determine actual required variables (when using "is defined").
- If present, uses content from example.yml for the example playbook; otherwise, constructs an example based on the identified required variables.
- Provides usage instructions using the clone-url parameter to indicate the URL to be used in the requirements.yml file.

## Usage

The script accepts the following optional parameters:

- --role-path: Path to the role directory.
- --output-path: Path to save the generated README.md file.
- --clone-url: URL for cloning the role project, used in the requirements.yml file.

### Example

```bash
python autodoc-role.py --role-path /path/to/your/ansible/role --output-path /path/to/save/README.md --clone-url https://github.com/user/repo.git
```

This command will analyze the specified Ansible role, generate a README.md file based on the role's content, and save it to the specified output path.

## Requirements

- Python 3.6 or higher
- PyYAML
- Jinja2
- Tabulate

## Installation

```bash
pip install pyyaml jinja2 tabulate
```

## Limitations

- The script assumes that the role follows the standard Ansible role directory structure.
- It relies on comments in defaults/main.yml and vars/main.yml to determine variable descriptions.
- Only handles assert statements that use "is defined" for required variable checks.

## License

This script is released under the [MIT License](https://opensource.org/licenses/MIT).

## author

Fabio Ambrosanio <fabio.ambrosanio@staff.aruba.it>
