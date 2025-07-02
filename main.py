import os
from pathspec import PathSpec


# Inserts a value into a nested dictionary using a list of keys
def set_dict(dic: dict[str, dict | list[str]], keys: list[str], value: dict | list[str]) -> None:
    tmp = dic
    for key in keys[:-1]:
        tmp = tmp.setdefault(key, {})

    tmp[keys[-1]] = value


# Sorts dictionary entries so that directories come before file lists
def sort_as_type(item: tuple[any, any]) -> tuple[str, any]:
    type_str = str(type(item[1]))
    key = item[0]
    return type_str, key


# Recursively sorts nested dictionaries by type and key
def sort_dict(d: dict[str, dict | list[str]]) -> dict[str, dict | list[str]]:
    if not isinstance(d, dict):
        return d

    sorted_dict = {}
    for key, value in sorted(d.items(), key=sort_as_type):
        sorted_dict[key] = sort_dict(value)
    return sorted_dict


# Loads .gitignore rules as a PathSpec object
def load_gitignore_spec(base_path: str = ".") -> PathSpec:

    gitignore_content = []
    gitignore_path = os.path.join(base_path, ".gitignore")
    if os.path.exists(gitignore_path):

        with open(gitignore_path, "r", encoding="utf-8") as file:
            gitignore_content = file.read().splitlines()

    return PathSpec.from_lines("gitwildmatch", gitignore_content)


# Combines .gitignore rules with additional custom rules
def combine_spec(git_spec: PathSpec) -> PathSpec:
    add_rules = [".*", ".*/"]

    exception_rules = ["!.gitignore", "!.flake8"]

    all_spec = PathSpec.from_lines("gitwildmatch", add_rules + exception_rules)

    return all_spec + git_spec


# Builds a nested dictionary of all non-ignored files and folders
def find_not_ignored_files(path_spec: PathSpec, base_path: str = ".") -> dict[str, dict | list[str]]:

    to_tree_dict = {}

    dir_list = []
    level_before = -1

    for root, dirs, files in os.walk(base_path):
        level = root.replace(base_path, "").count(os.sep)
        not_ignore = []
        for name in dirs:
            rel_path = os.path.relpath(os.path.join(root, name), base_path)
            rel_path = rel_path.replace(os.sep, "/")
            if not path_spec.match_file(rel_path):
                not_ignore.append(name)

        dirs[:] = not_ignore

        if level > level_before:
            dir_list.append(str(os.path.basename(root)))
        elif level == level_before:
            dir_list = dir_list[:-1]
            dir_list.append(str(os.path.basename(root)))
        elif level < level_before:
            dir_list = dir_list[:-2]
            dir_list.append(str(os.path.basename(root)))

        level_before = level
        set_dict(to_tree_dict, dir_list, {})

        if files is not None:
            dir_list_copy = dir_list.copy()
            dir_list_copy.append("file_list")
            file_list = []
            for name in files:

                rel_path = os.path.relpath(os.path.join(root, name), base_path)
                rel_path = rel_path.replace(os.sep, "/")
                if not path_spec.match_file(rel_path):
                    file_list.append(name)

            set_dict(to_tree_dict, dir_list_copy, file_list)

    return to_tree_dict


# Converts the directory dictionary into a formatted ASCII tree list
def dir_to_list(d: dict[str, dict | list[str]] | list[str],
                dir_list: list[str] | None = None,
                step: int = -2) -> list[str]:
    if dir_list is None:
        dir_list = []
    if not isinstance(d, dict):
        if d:
            for line in d[:-1]:
                dir_list.append(f"{'│   ' * step}├── {line}\n")
            dir_list.append(f"{'│   ' * step}└── {d[-1:][0]}\n")
        step -= 1
        return dir_list

    tmp = {}
    step += 1
    for k, v in d.items():
        if isinstance(v, dict):
            if k == ".":
                path = os.path.dirname(os.path.abspath(__file__))
                main_dir = os.path.basename(path)
                dir_list.append(f"{main_dir}\n")
            else:
                dir_list.append(f"{'│   '*step}├── {k}\n")

        tmp[k] = dir_to_list(v, dir_list, step)

    return dir_list


# Creates or overwrites a Markdown file named dir.md with the tree view
def create_dir_md(d_list: list[str]) -> None:
    with open("dir.md", "w", encoding="utf-8") as md:
        md.write('<pre style="font-size:12px; font-family:Consolas;">')
        md.writelines(d_list)
        md.write("</pre>")


def main() -> None:
    print("Program started")
    spec = load_gitignore_spec()

    all_spec = combine_spec(spec)

    dir_dict = find_not_ignored_files(all_spec)

    dir_sort = sort_dict(dir_dict)

    dir_list = dir_to_list(dir_sort)

    create_dir_md(dir_list)

    print("Done, dir.md created :-)")


if __name__ == "__main__":
    main()
