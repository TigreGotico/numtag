# Consumer readings

Each file holds the readings that one consumer of numtag depends on. A consumer takes the latest numtag alpha, so a change in numtag changes its behaviour at once. `tests/test_consumers.py` reads every row the way that consumer reads it and compares the result with `reading`.

One JSON object per line:

```json
{"text": "volume à un pour cent", "lang": "fr-FR", "reading": "1", "source": "..."}
```

- `text` is the input the consumer passes to `tag_numbers`.
- `lang` is the language tag the consumer passes.
- `reading` is what the consumer computes from the mentions. Its shape depends on the consumer: a value string or `null` for a single number, a list of value strings, a list of `[text, value]` pairs, or a list of `[start, end, text, number]` entries with the JSON number that ovos-typed-slots-transformer writes into its slot.
- `source` says where the reading comes from: the consumer's own test, its golden utterances checked against ovos-number-parser, or a ruling.

When a numtag change alters a reading, the test fails. The pull request then changes the row and names the change that the consumer sees.
