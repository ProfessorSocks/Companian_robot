from pathlib import Path
import yaml


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent


# --------------------------------------------------
# TEXT FILES
# --------------------------------------------------

def load_text_prompt(relative_path):
    path = PROJECT_ROOT / relative_path

    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found:\n{path}"
        )

    return path.read_text(
        encoding="utf-8"
    )


# --------------------------------------------------
# YAML FILES
# --------------------------------------------------

def load_yaml_prompt(relative_path):
    path = PROJECT_ROOT / relative_path

    if not path.exists():
        raise FileNotFoundError(
            f"YAML file not found:\n{path}"
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return yaml.safe_load(file)


# --------------------------------------------------
# TEMPLATE RENDERING
# --------------------------------------------------

def render_prompt(
    template,
    **values,
):
    rendered = template

    for key, value in values.items():
        placeholder = (
            "{{"
            + key
            + "}}"
        )

        rendered = rendered.replace(
            placeholder,
            str(value),
        )

    return rendered