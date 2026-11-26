"""Put a writer block at the end of a lexicon file, one rule per line, and keep the rest of the file text."""
import json
import sys
from pathlib import Path


def _dump(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def render(text: str, block: dict) -> str:
    """The file text with ``block`` as its last key, ``writer``, in place of the writer it has."""
    head = text.split('\n  "writer": ', 1)[0].rstrip().rstrip(",")
    if text.split('\n  "writer": ', 1)[0] == text:
        head = text.rstrip()
        assert head.endswith("}")
        head = head[:-1].rstrip()
    lines = ['  "writer": {', f'    "source": {_dump(block["source"])},', '    "rulesets": {']
    names = list(block["rulesets"])
    for i, name in enumerate(names):
        rules = block["rulesets"][name]["rules"]
        lines.append(f'      {_dump(name)}: {{"source": {_dump(block["rulesets"][name]["source"])}, "rules": [')
        lines += [f"        {_dump(rule)}" + ("," if j < len(rules) - 1 else "") for j, rule in enumerate(rules)]
        lines.append("      ]}" + ("," if i < len(names) - 1 else ""))
    lines.append("    },")
    rest = [key for key in block if key not in ("source", "rulesets")]
    lines += [f"    {_dump(key)}: {_dump(block[key])}" + ("," if i < len(rest) - 1 else "") for i, key in enumerate(rest)]
    body = head + ",\n" + "\n".join(lines) + "\n  }\n}\n"
    return body.replace('"format_version": 1,', '"format_version": 2,', 1)


def splice(path: Path, block: dict, check: bool = False) -> None:
    """Write ``block`` into the lexicon at ``path``, or with ``check`` exit 1 when the file differs from it."""
    text = path.read_text(encoding="utf-8")
    new = render(text, block)
    assert json.loads(new)["writer"] == block
    if check:
        if new != text:
            sys.exit(f"{path}: the writer block differs from the generator")
        return
    path.write_text(new, encoding="utf-8")
