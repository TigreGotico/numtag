# API reference

The package `numtag` exports eleven names: `tag_numbers`, `NumberMention`, `Part`, `Role`, `Kind`, `Form`, `Reason`, `Scale`, `is_canonical_value`, `ARTICLE_CONFIDENCE` and `UnsupportedLanguageError`. This page describes each of them. Every other module is internal.

```python
>>> import numtag
>>> sorted(numtag.__all__)
['ARTICLE_CONFIDENCE', 'Form', 'Kind', 'NumberMention', 'Part', 'Reason', 'Role', 'Scale', 'UnsupportedLanguageError', 'is_canonical_value', 'tag_numbers']
```

## tag_numbers

```text
tag_numbers(text: str, lang: str, *, scale: Scale | None = None) -> list[NumberMention]
```

`tag_numbers` returns every number in `text` as a list of `NumberMention` objects. The list is in reading order, and no two mentions overlap.

| Argument | Meaning |
|---|---|
| `text` | The text to read. numtag never changes it. |
| `lang` | A language tag. `pt-BR` reads Brazilian Portuguese and every other `pt` tag reads European Portuguese. `fr-BE` and `fr-CH` read their own lexicons, every other `fr` tag reads `fr-FR`, and `no` reads Norwegian Bokmål. Every other tag reads the lexicon of its primary subtag: `de-AT` reads `de`. The README lists the lexicons. The tag may use `-` or `_`, in any case. |
| `scale` | Optional, keyword only. `Scale.LONG`, `Scale.SHORT`, `"long"` or `"short"`. It replaces the default scale of the language. Read [number-scale.md](number-scale.md). |

`tag_numbers` raises `UnsupportedLanguageError` for a language with no lexicon. It is a subclass of `ValueError`, so a caller can catch it alone and skip the text, or catch `ValueError` for every bad argument. A `scale` that is not a scale raises a plain `ValueError`. An empty value reads the default scale.

```python
>>> from numtag import UnsupportedLanguageError, tag_numbers, Scale
>>> try:
...     tag_numbers("दो", "hi")
... except UnsupportedLanguageError as error:
...     print(error)
no lexicon for language 'hi'
>>> tag_numbers("one", "en", scale="medium")
Traceback (most recent call last):
  ...
ValueError: 'medium' is not a valid Scale
>>> tag_numbers("one billion", "en", scale="")[0].number_scale
<Scale.SHORT: 'short'>
```

At each position, numtag takes the longest number that its grammar can read, from left to right. A number never crosses punctuation other than a hyphen ("twenty-one"), with one exception: in Portuguese a comma after a scale word can join two classes of one number. Read [rulings.md](rulings.md).

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
| `reasons` | `frozenset[Reason]` | Keyword only. Why the confidence is low. Empty for a sure number |
| `parts` | `tuple[Part, ...]` | Keyword only. The pieces of the mention in reading order. Read [Part](#part). |

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

A mention checks its own fields when it is made. It raises `ValueError` when the span does not fit the text, when the value is not canonical, when `number_scale` is not a `Scale` or `None`, when `reasons` is not a frozenset of `Reason`, or when a part is not inside the mention or not in reading order.

```python
>>> from numtag import NumberMention, Kind, Form
>>> NumberMention((0, 3), "two", "2.0", Kind.CARDINAL, Form.WORDS)
Traceback (most recent call last):
  ...
ValueError: value '2.0' is not a canonical digit string
```

Two mentions are equal when all their fields are equal, except `confidence`, `reasons` and `parts`. Equality ignores them, so a test can compare readings without fixing a score. `number_scale` is part of equality.

```python
>>> a = NumberMention((0, 3), "two", "2", Kind.CARDINAL, Form.WORDS, confidence=1.0)
>>> b = NumberMention((0, 3), "two", "2", Kind.CARDINAL, Form.WORDS, confidence=0.3)
>>> a == b
True
```

## Part

A `Part` is a frozen dataclass. It is one piece of a mention: a word or a phrase with one role. `tag_numbers` always fills `NumberMention.parts`, in reading order. A clock reads the hour and the half of "às três e meia" from them:

```python
>>> tag_numbers("às três e meia", "pt-PT")[0].parts
(Part(role=<Role.COUNT: 'count'>, char_span=(3, 7), text='três', value='3'), Part(role=<Role.JOINER: 'joiner'>, char_span=(8, 9), text='e', value=None), Part(role=<Role.HALF: 'half'>, char_span=(10, 14), text='meia', value='0.5'))
```

| Field | Type | Meaning |
|---|---|---|
| `role` | `Role` | What the piece does in the number |
| `char_span` | `tuple[int, int]` | The character range in the original text, as the mention's `char_span` |
| `text` | `str` | The exact words: `text[start:end]` of the original text |
| `value` | `str` or `None` | The canonical value of the words of the part alone. `None` for a joiner, "of", a minus word or a decimal mark |

The mention value is the one exact answer. A caller does not add up the parts. A part value is the number that its words name alone: the half of "um milhão e meio" has the value 0.5, and the mention has 1500000. Deep time divides the mention value by the value of the last scale part:

```python
>>> m = tag_numbers("Há sessenta e seis milhões de anos.", "pt-PT")[0]
>>> [(p.role.value, p.text, p.value) for p in m.parts]
[('count', 'sessenta e seis', '66'), ('scale', 'milhões', '1000000')]
```

These rules decide the parts:

1. Every word of a mention is in exactly one part. Spaces, hyphens and the comma between classes are in no part.
2. A count below the next scale word is one count part, with the joiners inside it: "sessenta e seis", "two hundred", "vigésimo primeiro".
3. A digit string is one part, with its group marks, its decimal mark and its sign: "1.234,5", "-5", "21st".
4. An article that the grammar reads as one is a count with the value 1: "a" in "a quarter". Any other article, ordinal prefix, ending or particle is in the part that it introduces or ends: "a half", "a dozen" after "half", "doze avos".
5. An ordinal has no role of its own, because the mention kind says ORDINAL. "six thousand two hundredth" is the count "six", the scale "thousand" and the count "two hundredth" (200).
6. A word that holds two parts is one part. The dual "ألفين" (two thousand) is one scale part with the value 1000, and "ثلثان" (two thirds) is one denominator part with the value 3.
7. Inside a compound word, the parts follow its sub-words: "dreihunderttausend" is the count "dreihundert" and the scale "tausend". Where two sub-words share a letter (Swedish "ettusen"), the two parts overlap by that letter.

The parts are flat, and they do not show the scope of a collective: "dois mil e duas dúzias" and "dois mil e duas centenas" have the same roles. Two parts compare equal when all their fields are equal.

```python
>>> [(p.role.value, p.text, p.value) for p in tag_numbers("one point two million", "en")[0].parts]
[('count', 'one', '1'), ('decimal_mark', 'point', None), ('decimals', 'two', '0.2'), ('scale', 'million', '1000000')]
```

A part checks its own fields when it is made. It raises `ValueError` when the span does not fit the text, when the value is not canonical, or when a role that names no number has a value.

```python
>>> from numtag import Part, Role
>>> Part(Role.JOINER, (0, 1), "e", "1")
Traceback (most recent call last):
  ...
ValueError: a joiner part takes no value
```

## Role

`Role` is a string enum. It says what a part does in the number.

| Member | Value | Example | Part value |
|---|---|---|---|
| `Role.COUNT` | `"count"` | "três", "sessenta e seis", "2,5", "a" in "a dozen" | Its number |
| `Role.SCALE` | `"scale"` | "mil", "milhões", "million", "thousandth" | Its power of ten, in the scale that `number_scale` states |
| `Role.COLLECTIVE` | `"collective"` | "dúzias", "dezena", "a dozen" after "half" | Its size: 12, 10 |
| `Role.OF` | `"of"` | "de" in "duas dúzias de milhar" | None |
| `Role.JOINER` | `"joiner"` | "e", "and" between two parts | None |
| `Role.HALF` | `"half"` | "meia", "meio", "half", "a half" | 0.5 |
| `Role.DENOMINATOR` | `"denominator"` | "terços", "quarter", "doze avos" | The whole number below the line: 3, 4, 12 |
| `Role.MINUS` | `"minus"` | "menos", "minus" | None |
| `Role.DECIMAL_MARK` | `"decimal_mark"` | "vírgula", "point" | None |
| `Role.DECIMALS` | `"decimals"` | "zero cinco" after "vírgula" | The fraction it adds: 0.05 |
| `Role.MANTISSA`, `Role.TIMES`, `Role.BASE`, `Role.EXPONENT` | | Scientific notation ("6.02e-23") | Reserved. numtag gives no part with these roles |

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

## Reason

`Reason` is a string enum. It says why a mention is not sure. Filter on the reason, and rank by the confidence: the scores can change in any release, and the reasons keep their meaning.

| Member | Value | When |
|---|---|---|
| `Reason.ARTICLE` | `"article"` | The word is also an article or an indefinite pronoun, and no number reading needs it: "comprei uma casa", "muéstrame una" |
| `Reason.HOMOGRAPH` | `"homograph"` | The word has a common sense that is no number, and the words around it do not decide: "segunda", "second", "nou" |

```python
>>> from numtag import Reason
>>> [(m.text, sorted(m.reasons)) for m in tag_numbers("Dá-me um segundo facto.", "pt-PT")]
[('um', [<Reason.ARTICLE: 'article'>]), ('segundo', [<Reason.HOMOGRAPH: 'homograph'>])]
>>> [m.value for m in tag_numbers("Comprei uma casa e dois carros.", "pt-PT") if Reason.ARTICLE not in m.reasons]
['2']
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

## ARTICLE_CONFIDENCE

`ARTICLE_CONFIDENCE` is the float score that a mention gets when its word is an article and not a number: 0.3. Test `Reason.ARTICLE in mention.reasons` instead. `ARTICLE_CONFIDENCE` stays for one stable release.

```python
>>> from numtag import ARTICLE_CONFIDENCE
>>> [m.confidence == ARTICLE_CONFIDENCE for m in tag_numbers("Comprei uma casa e dois carros.", "pt-PT")]
[True, False]
```

Read [confidence-and-homographs.md](confidence-and-homographs.md).

---
[← Getting started](getting-started.md) · [Home](index.md) · [Values →](values.md)
