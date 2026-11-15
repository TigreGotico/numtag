# Gold corpus

Each language has one file, `<lang>.jsonl`, with one JSON object per line:

```json
{"text": "comprou duas dúzias de ovos", "mentions": [{"start": 8, "end": 19, "value": "24", "kind": "cardinal"}], "source": "Priberam, dúzia: Conjunto de doze."}
```

- `text` is a natural sentence or phrase in that language.
- `mentions` lists every number in reading order. An empty list means the text holds no number.
- `start` and `end` are half-open character offsets, so `text[start:end]` is the number's exact words.
  A span never starts or ends with a space, a punctuation mark or a symbol, so "às 7," gives "7" and "€10" gives "10". The one exception is a minus sign before digits ("-5").
- `value` is a canonical digit string, as `numtag.is_canonical_value` defines it.
- `kind` is `cardinal`, `ordinal`, `fraction` or `decimal`. A whole value is `cardinal`, or `ordinal` when it names a position. This is also true when the words hold a decimal mark or a half ("2,5 milhões", "um milhão e meio"). A value that is not whole is `decimal` when the words use a decimal mark ("dois vírgula cinco", "2.5"). It is `fraction` when they use a fraction word ("três quartos", "mil e meio").
- `low_confidence` is optional. When it is present, it is `true`, and the engine must report that mention with a confidence below 0.5. It marks a word that is also an article, as "uma" in "comprei uma casa". Each row decides it. An article that counts a number noun is part of that number and is not a separate mention: "uma dúzia" is one mention, 12, and "a dozen" is one mention, 12. English "a" before a noun that is not a number word is not a number, so it is not a mention.
- A mention with no `low_confidence` flag is a number for certain: the engine reports it with confidence 0.5 or above.
- `source` says where the reading comes from: a dictionary or grammar quote, a maintainer ruling, or "arithmetic" when the value follows from the words by counting alone.

`check_gold.py` checks every file against this format and prints the number of rows it read and passed.

Every value is computed by hand or from a source, never read back from a parser. The engine never edits a gold file. A row the engine reads wrong stays in the file and lowers the score.
