# API reference

The package `numtag` exports six names: `tag_numbers`, `NumberMention`, `Kind`, `Form`, `Scale` and `is_canonical_value`. This page describes each of them. Every other module is internal.

```python
>>> import numtag
>>> sorted(numtag.__all__)
['Form', 'Kind', 'NumberMention', 'Scale', 'is_canonical_value', 'tag_numbers']
```

## tag_numbers

```text
tag_numbers(text: str, lang: str, *, scale: Scale | None = None) -> list[NumberMention]
```

`tag_numbers` returns every number in `text` as a list of `NumberMention` objects. The list is in reading order, and no two mentions overlap.

| Argument | Meaning |
|---|---|
| `text` | The text to read. numtag never changes it. |
| `lang` | A language tag. `pt-BR` reads Brazilian Portuguese, every other `pt` tag reads European Portuguese, and every `en` tag reads English. The tag may use `-` or `_`, in any case. |
| `scale` | Optional, keyword only. `Scale.LONG`, `Scale.SHORT`, `"long"` or `"short"`. It replaces the default scale of the language. Read [number-scale.md](number-scale.md). |

`tag_numbers` raises `ValueError` for a language with no lexicon, and for a `scale` that is not a scale.

```python
>>> from numtag import tag_numbers, Scale
>>> tag_numbers("one", "en", scale="medium")
Traceback (most recent call last):
  ...
ValueError: 'medium' is not a valid Scale
```

At each position, numtag takes the longest number that its grammar can read, from left to right. A number never crosses punctuation, with one exception: in Portuguese a comma after a scale word can join two classes of one number. Read [rulings.md](rulings.md).

numtag loads the lexicon of a language on the first call for that language and scale, and keeps it in memory for later calls.

## NumberMention

A `NumberMention` is a frozen dataclass. It describes one number in the text.

| Field | Type | Meaning |
|---|---|---|
| `char_span` | `tuple[int, int]` | The half-open character range `(start, end)` of the words in the original text |
| `text` | `str` | The exact words: `text[start:end]` of the original text |
| `value` | `str` | The exact value as a canonical digit string. Read [values.md](values.md). |
| `kind` | `Kind` | Cardinal, ordinal, fraction or decimal |
| `form` | `Form` | Words, digits or both |
| `gender` | `str` or `None` | `"masculine"` or `"feminine"` when the words show it, else `None` |
| `confidence` | `float` | A fixed score in (0, 1] that the words are a number. Read [confidence-and-homographs.md](confidence-and-homographs.md). |
| `number_scale` | `Scale` or `None` | Keyword only. The scale that gave the value, set only when the value depends on the scale |

```python
>>> m = tag_numbers("Recebeu 2,5 milhões de euros.", "pt-PT")[0]
>>> m.char_span, m.text, m.value, m.kind, m.form, m.gender, m.confidence, m.number_scale
((8, 19), '2,5 milhões', '2500000', <Kind.CARDINAL: 'cardinal'>, <Form.MIXED: 'mixed'>, None, 1.0, None)
```

The gender comes from the last word of the number that shows one. Portuguese words show it ("duas", "duzentos", "primeira", "2.ª"). English words do not, so an English mention has no gender.

```python
>>> [(m.text, m.gender) for m in tag_numbers("duas dúzias e o 2.º lugar", "pt-PT")]
[('duas dúzias', 'feminine'), ('2.º', 'masculine')]
```

A mention checks its own fields when it is made. It raises `ValueError` when the span does not fit the text, when the value is not canonical, or when `number_scale` is not a `Scale` or `None`.

```python
>>> from numtag import NumberMention, Kind, Form
>>> NumberMention((0, 3), "two", "2.0", Kind.CARDINAL, Form.WORDS)
Traceback (most recent call last):
  ...
ValueError: value '2.0' is not a canonical digit string
```

Two mentions are equal when all their fields are equal, except `confidence`. Equality ignores the confidence, so a test can compare readings without fixing a score. `number_scale` is part of equality.

```python
>>> a = NumberMention((0, 3), "two", "2", Kind.CARDINAL, Form.WORDS, confidence=1.0)
>>> b = NumberMention((0, 3), "two", "2", Kind.CARDINAL, Form.WORDS, confidence=0.3)
>>> a == b
True
```

## Kind

`Kind` is a string enum. numtag sets it from the words and the value.

| Member | Value | When |
|---|---|---|
| `Kind.ORDINAL` | `"ordinal"` | The words name a position: "vigésimo primeiro", "2.º", "twenty-first", "3rd" |
| `Kind.CARDINAL` | `"cardinal"` | Any other whole value, also when the words hold a decimal mark or a half: "2,5 milhões", "um milhão e meio" |
| `Kind.DECIMAL` | `"decimal"` | A value that is not whole, written with a decimal mark: "dois vírgula cinco", "2.5" |
| `Kind.FRACTION` | `"fraction"` | A value that is not whole, written with a fraction word or a half: "três quartos", "mil e meio" |

The kind follows the words, and the form of the value follows the arithmetic. So a FRACTION can have a decimal value.

```python
>>> [(m.value, m.kind.value) for m in tag_numbers("dois milhões e quarto; cinco sextos; 2,5", "pt-PT")]
[('2000000.25', 'fraction'), ('5/6', 'fraction'), ('2.5', 'decimal')]
```

## Form

`Form` is a string enum. It tells how the number is written.

| Member | Value | Example |
|---|---|---|
| `Form.WORDS` | `"words"` | "dois milhões" |
| `Form.DIGITS` | `"digits"` | "2000000", "1.000.000", "21st" |
| `Form.MIXED` | `"mixed"` | "2 milhões" |

A minus word before digits does not change the form.

```python
>>> [(m.text, m.value, m.form.value) for m in tag_numbers("menos 5 e 2 milhões", "pt-PT")]
[('menos 5', '-5', 'digits'), ('2 milhões', '2000000', 'mixed')]
```

## Scale

`Scale` is a string enum with two members.

| Member | Value | Meaning |
|---|---|---|
| `Scale.SHORT` | `"short"` | A billion is a thousand millions (10^9) |
| `Scale.LONG` | `"long"` | A billion is a million millions (10^12) |

## is_canonical_value

`is_canonical_value(value: str) -> bool` is true when `value` has one of the three canonical forms. It checks the pattern only. A whole number has no leading zero and is not "-0". A decimal has no trailing zero. A fraction has no zero part. It does not check that a fraction is in lowest terms. The tagger's own arithmetic makes sure of that.

```python
>>> from numtag import is_canonical_value
>>> [is_canonical_value(v) for v in ("1200", "-2.5", "1/3", "007", "2.50", "-0")]
[True, True, True, False, False, False]
```

---
[← Getting started](getting-started.md) · [Home](index.md) · [Values →](values.md)
