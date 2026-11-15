# numtag

numtag finds every number in a text. For each number it gives the exact words, their character offsets, the value and the kind.

```python
from numtag import tag_numbers

tag_numbers("comprou duas dúzias de ovos e um milhão de euros", "pt-PT")
# [NumberMention(char_span=(8, 19), text='duas dúzias', value='24', kind=Kind.CARDINAL, ...),
#  NumberMention(char_span=(30, 39), text='um milhão', value='1000000', kind=Kind.CARDINAL, ...)]
```

A value is a digit string with no limit on its length: "24", "-2.5" or "1/3". numtag never converts a value to `int` or `float`, so no rounding changes a digit. Convert it with `int()`, `decimal.Decimal()` or `fractions.Fraction()` when you need a number.

The language rules are data files in `numtag/lexicon/`, one per language, with the source of each rule in the file.
