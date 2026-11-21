# Number scale

<!-- agent-hint
covers: Long and short scale: the scale argument, the lexicon default and the number_scale field.
source: numtag/tagger.py:tag_numbers, numtag/lexicon/__init__.py:load, the scale setting of each lexicon
generated: no
verify: sed '/^\x60\x60\x60/d' docs/number-scale.md | python -m doctest -o NORMALIZE_WHITESPACE /dev/stdin
see: values.md, languages/pt.md
-->

Large scale words have two values. In the short scale, a billion is a thousand millions (10^9). In the long scale, a billion is a million millions (10^12). numtag reads each language in its own scale by default. Every mention states the scale when its value depends on it.

## The default scale per language

| `lang` | Default | Example | Value |
|---|---|---|---|
| European Portuguese | long | "um bilião" | 10^12 |
| `pt-BR` | short | "um bilhão" | 10^9 |
| English | short | "one billion" | 10^9 |

```python
>>> from numtag import tag_numbers, Scale
>>> def read(text, lang, **options):
...     return [(m.value, m.number_scale) for m in tag_numbers(text, lang, **options)]
>>> read("um bilião", "pt-PT")
[('1000000000000', <Scale.LONG: 'long'>)]
>>> read("um bilhão", "pt-BR")
[('1000000000', <Scale.SHORT: 'short'>)]
>>> read("one billion", "en")
[('1000000000', <Scale.SHORT: 'short'>)]
```

The pt-BR lexicon is the European Portuguese lexicon with the short scale, and with no space between digit groups. Both read both spellings, "bilião" and "bilhão". The scale alone decides the value.

```python
>>> read("um bilhão", "pt-PT")
[('1000000000000', <Scale.LONG: 'long'>)]
```

## The scale argument

The keyword argument `scale` replaces the default scale. It takes `Scale.LONG`, `Scale.SHORT`, `"long"` or `"short"`.

```python
>>> read("one billion", "en", scale=Scale.LONG)
[('1000000000000', <Scale.LONG: 'long'>)]
>>> read("um bilião", "pt-PT", scale="short")
[('1000000000', <Scale.SHORT: 'short'>)]
```

## When number_scale is set

`number_scale` is set only when the value depends on the scale. That is the case when the words hold "bilião", "bilhão", "billion", "trilião", "trillion" or a larger scale word, also after digits. It is `None` when both scales give the same value: "mil", "milhão", "million", "a thousand million", digits alone, and every smaller number.

```python
>>> read("2 biliões", "pt-PT")
[('2000000000000', <Scale.LONG: 'long'>)]
>>> read("um milhão", "pt-PT")
[('1000000', None)]
>>> read("a thousand million", "en")
[('1000000000', None)]
>>> read("1000000000000", "en")
[('1000000000000', None)]
```

The mention always states the scale it used. A caller never needs to know that "bilião" is 10^12 in Portugal and "bilhão" is 10^9 in Brazil. When `number_scale` is `None`, the value is the same in both scales.

## The -illion words

"milhão" and "million" are the -illion words of rank 1, and "bilião" and "billion" of rank 2. The word of a rank is 10^(3 × rank + 3) in the short scale and 10^(6 × rank) in the long scale. Rank 1 gives 10^6 in both scales, so "milhão" and "million" set no `number_scale`. The lexicons hold the -illion words of ranks 1 to 20 and of rank 100 ("centilião", "centillion").

> Wikipedia, "Long and short scales": "For the same magnitude name (n-illion), the value is 10^3n+3 in the short scale but 10^6n in the long scale for positive integers n".

```python
>>> [(len(m.value) - 1, m.number_scale.value) for m in tag_numbers("um centilião", "pt-PT")]
[(600, 'long')]
>>> [(len(m.value) - 1, m.number_scale.value) for m in tag_numbers("one centillion", "en")]
[(303, 'short')]
```

The sources of the default scales are in [languages/pt.md](languages/pt.md) and [languages/en.md](languages/en.md).

---
[← Values](values.md) · [Home](index.md) · [Confidence and homographs →](confidence-and-homographs.md)
