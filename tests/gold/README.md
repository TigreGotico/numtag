# Gold corpus

Each language has one file, `<lang>.jsonl`, with one JSON object per line:

```json
{"text": "comprou duas dúzias de ovos", "mentions": [{"start": 8, "end": 19, "value": "24", "kind": "cardinal"}], "source": "Priberam, dúzia: Conjunto de doze."}
```

- `text` is a natural sentence or phrase in that language.
- `mentions` lists every number in reading order. An empty list means the text holds no number.
- `start` and `end` are half-open character offsets, so `text[start:end]` is the number's exact words.
- `value` is a canonical digit string, as `numtag.is_canonical_value` defines it.
- `kind` is `cardinal`, `ordinal`, `fraction` or `decimal`.
- `source` says where the reading comes from: a dictionary or grammar quote, a maintainer ruling, or "arithmetic" when the value follows from the words by counting alone.

Every value is computed by hand or from a source, never read back from a parser. The engine never edits a gold file. A row the engine reads wrong stays in the file and lowers the score.
