# Getting started

<!-- agent-hint
covers: How to make the first call and do the common tasks: filter weak mentions, replace numbers with digits, convert values, choose a scale.
source: numtag/tagger.py:tag_numbers, numtag/mention.py
generated: no
verify: sed '/^\x60\x60\x60/d' docs/getting-started.md | python -m doctest -o NORMALIZE_WHITESPACE /dev/stdin
see: api.md, values.md, number-scale.md
-->

This guide shows the first call to numtag and the tasks that most callers need. Every example on this page runs as a test, so the output shown is the output that numtag gives.

## Install

numtag needs Python 3.11 or later. It has no dependencies.

```bash
uv pip install --prerelease=allow numtag
```

## The first call

Give `tag_numbers` a text and a language tag. It returns a list of mentions in reading order.

```python
>>> from numtag import tag_numbers
>>> mentions = tag_numbers("A viagem custou mil e duzentos euros.", "pt-PT")
>>> mentions
[NumberMention(char_span=(16, 30), text='mil e duzentos', value='1200', kind=<Kind.CARDINAL: 'cardinal'>, form=<Form.WORDS: 'words'>, gender='masculine', confidence=1.0, number_scale=None, reasons=frozenset(), parts=(Part(role=<Role.SCALE: 'scale'>, char_span=(16, 19), text='mil', value='1000'), Part(role=<Role.JOINER: 'joiner'>, char_span=(20, 21), text='e', value=None), Part(role=<Role.COUNT: 'count'>, char_span=(22, 30), text='duzentos', value='200')))]
```

A text with no number gives an empty list.

```python
>>> tag_numbers("Hoje está sol.", "pt-PT")
[]
```

A text can hold many numbers of different kinds and forms.

```python
>>> for m in tag_numbers("Ganhou o 2.º prémio: 2,5 milhões e três quartos de um bolo.", "pt-PT"):
...     print(m.text, "|", m.value, m.kind.value, m.form.value)
2.º | 2 ordinal digits
2,5 milhões | 2500000 cardinal mixed
três quartos | 0.75 fraction words
um | 1 cardinal words
```

The last mention, "um", is an article in this sentence. numtag gives it a low confidence. The next section shows how to drop it.

## Drop weak mentions

The confidence is a fixed score, not a probability. A number for certain scores 1.0. An article alone before a noun scores 0.3. A number that rests on a word with a common meaning that is not a number scores 0.4. Keep the mentions at 0.5 or above when you want only clear numbers.

```python
>>> text = "Comprei uma casa com dois andares."
>>> [(m.text, m.confidence) for m in tag_numbers(text, "pt-PT")]
[('uma', 0.3), ('dois', 1.0)]
>>> [m.text for m in tag_numbers(text, "pt-PT") if m.confidence >= 0.5]
['dois']
```

Read [confidence-and-homographs.md](confidence-and-homographs.md) for the full rules.

## Replace number words with digits

The span of each mention slices the original text. Build the output text from the pieces between the spans.

```python
>>> def to_digits(text, lang):
...     pieces, last = [], 0
...     for m in tag_numbers(text, lang):
...         if m.confidence < 0.5:
...             continue
...         start, end = m.char_span
...         pieces += [text[last:start], m.value]
...         last = end
...     return "".join(pieces + [text[last:]])
>>> to_digits("Plantámos mil e duzentos pinheiros e uma oliveira.", "pt-PT")
'Plantámos 1200 pinheiros e uma oliveira.'
>>> to_digits("She ran twenty-one kilometres in two and a half hours.", "en")
'She ran 21 kilometres in 2.5 hours.'
```

## Convert a value

A value is a string. Convert it at the point where your code needs a number. `fractions.Fraction` reads every value form, so it is the safe default.

```python
>>> from fractions import Fraction
>>> from decimal import Decimal
>>> [Fraction(m.value) for m in tag_numbers("one third and two point five", "en")]
[Fraction(1, 3), Fraction(5, 2)]
>>> Decimal(tag_numbers("one point two five", "en")[0].value)
Decimal('1.25')
>>> int(tag_numbers("um bilião", "pt-PT")[0].value)
1000000000000
```

Read [values.md](values.md) for the three forms and their rules.

## Choose the scale

Each language has a default scale. Pass `scale` to read the large scale words in the other scale. The mention states the scale that gave its value.

```python
>>> m = tag_numbers("one billion", "en", scale="long")[0]
>>> m.value, m.number_scale
('1000000000000', <Scale.LONG: 'long'>)
```

Read [number-scale.md](number-scale.md).

## Language tags

numtag reads `pt-BR` as Brazilian Portuguese and every other `pt` tag as European Portuguese. Every other tag reads the lexicon of its primary subtag. `fr-BE` and `fr-CH` have their own lexicons, and `no` reads Norwegian Bokmål. The README lists the lexicons. A tag may use `-` or `_`, in any case. A language with no lexicon raises `UnsupportedLanguageError`, a subclass of `ValueError`.

```python
>>> [m.value for m in tag_numbers("dois", "pt_AO")]
['2']
>>> tag_numbers("二", "ja")
Traceback (most recent call last):
  ...
numtag.lexicon.UnsupportedLanguageError: no lexicon for language 'ja'
```

## What numtag does not read

numtag reads numbers only. It gives the number of a unit, a percentage or a price, and leaves the unit, the sign or the currency outside the span. It gives each limit of a range as its own mention. A caller that reads dates, units or ranges builds them from the mentions.

```python
>>> [(m.text, m.value) for m in tag_numbers("Subiu 5% para dois ou três euros.", "pt-PT")]
[('5', '5'), ('dois', '2'), ('três', '3')]
```

---
[Home](index.md) · [API reference →](api.md)
