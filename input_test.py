from input_xlsx import get_input_json

data = get_input_json(
    "input.xlsx",
    out="extracted.json",
    normalize_checkbox=True,
    exec_only=True,
)
