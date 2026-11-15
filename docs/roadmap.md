# Roadmap

This page lists planned features. None of them is built. The API names on this page do not exist in the package, and no code may depend on them. Each feature comes as its own change, with tests and a documentation update.

```python
>>> import numtag
>>> from numtag import NumberMention, Kind, tag_numbers
>>> [hasattr(numtag, name) for name in ("Reading", "Ambiguity")]
[False, False]
>>> [name in NumberMention.__dataclass_fields__ for name in ("alternatives", "parts")]
[False, False]
>>> [kind.name for kind in Kind]
['CARDINAL', 'ORDINAL', 'FRACTION', 'DECIMAL']
```

## Alternative readings (planned)

At a few points the grammar has two well-formed readings of the same words. numtag returns one list of mentions, its first choice. The plan adds the other readings to each mention of such a stretch, with a reason. The first choice stays the same, so a caller that wants one answer still gets one.

| Planned name | Content |
|---|---|
| `NumberMention.alternatives` | A tuple of `Reading` objects, empty when there is no other reading. Keyword only, and not part of equality. |
| `Reading.mentions` | Another split of the same words, as a tuple of mentions |
| `Reading.reason` | An `Ambiguity` value |
| `Ambiguity.RANGE_SPLIT` | More than one split after "entre" or "between" |
| `Ambiguity.COMPOUND_OR_LIST` | One number or two: "cinco mil e sessenta e sete milhões" is 5067000000, or 5000 and 67000000 |
| `Ambiguity.HALF_JOIN` | "três e meia" is 3.5, or 3 and a half |

A mention with alternatives will get a lower confidence than one without. A date reader can then take "às três e meia" as the hour 3 and a half hour. numtag gives the first choice only:

```python
>>> [(m.text, m.value) for m in tag_numbers("Saímos às três e meia.", "pt-PT")]
[('três e meia', '3.5')]
```

## Named numbers (planned)

Some numbers have a name of their own. A named number with a finite value will be an ordinary CARDINAL mention: "googol" is 10^100, and "dois googols" is 2 × 10^100. A named constant with no finite digit string will get a new kind, `Kind.CONSTANT`. Its value will be the name of the constant ("pi", "e", "googolplex"), not digits. The value contract will then have a fourth form for this kind. A bare "pi" will get a low confidence, because the word has other meanings. The constant e will read only from a phrase that names it ("número de Euler", "Euler's number"), never from the letter alone. Each word needs a source in the lexicon.

"googol" is not in the lexicon, so numtag reads only the article before it:

```python
>>> [(m.text, m.value, m.confidence) for m in tag_numbers("um googol", "pt-PT")]
[('um', '1', 0.3)]
```

## Parts of a mention (planned)

`NumberMention.parts` will give the sub-spans of a mention, each with a role (count, scale, collective, joiner, half, fraction, minus, decimal mark) and a value. A clock reader needs the hour 3 and the half in "às três e meia". A date reader needs the quarter in "a quarter past four". The design decides whether parts nest.

## Digit groups and slash fractions (planned)

Digits in date and time formats will become separate DIGITS mentions: "3.5.2025" will give 3, 5 and 2025, and "15h30" will give 15 and 30. A slash fraction will be one FRACTION mention: "2/3" will be 2/3. numtag reads these forms as follows:

```python
>>> [(m.text, m.value) for m in tag_numbers("Em 3.5.2025, às 15h30, 2/3 da turma saiu.", "pt-PT")]
[('15', '15'), ('2', '2'), ('3', '3')]
```

## More languages (in progress)

Ports to these languages are in progress. They are not supported, and `tag_numbers` raises `ValueError` for each of them until its port merges. Each port adds lexicons with sourced entries, a gold corpus, and engine mechanisms that a lexicon setting switches on.

| Group | Languages |
|---|---|
| Germanic | de, nl, fy, da, sv, nb, nn |
| Slavic | ru, uk, bg, pl, cs, sk, sl, hr |
| Romance and others | fr, it, ro, eu, id |
| Iberian | es, gl, ca, ast, an, oc, mwl |
| Uralic and Turkic | fi, et, hu, tr, az |
| Greek, Semitic, Iranian and Berber | el, ar, he, fa, kab |

No native speaker has checked these ports. A shared compound splitter and a shared rule for period ordinals ("5.") will replace the separate versions in the ports.

## Open questions

These readings wait for a ruling. The table shows what numtag reads.

| Text | numtag reads | Question |
|---|---|---|
| "a million billion" | 1000000, and "billion" reads no number | Is it 10^15? |
| "one million, two hundred thousand" | 1000000 and 200000 | Should English link classes across a comma, as Portuguese does? |
| "dois mil meio" | 2000 and 0.5 | Is it 2000.5? No source gives that reading. |
| "meio milhões de pessoas" | 500000 | "meio" and a plural noun do not agree. Is it a number? |

```python
>>> [(m.text, m.value) for m in tag_numbers("a million billion", "en")]
[('a million', '1000000')]
>>> [(m.text, m.value) for m in tag_numbers("dois mil meio e meio milhões de pessoas", "pt-PT")]
[('dois mil', '2000'), ('meio', '0.5'), ('meio milhões', '500000')]
```

---
[← Benchmarks](benchmarks.md) · [Home](index.md)
