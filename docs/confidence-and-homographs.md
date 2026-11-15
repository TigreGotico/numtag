# Confidence and homographs

Some number words have a second meaning. Portuguese "uma" is also the article "a", and "segundo" is also "according to". English "second" is also a unit of time. numtag tags these words and gives them a low confidence. The caller decides what to keep.

## The scores

The confidence is a fixed score in (0, 1]. It is not a probability. The same text and language always give the same score.

| Score | When |
|---|---|
| 1.0 | The words are a number for certain. |
| 0.4 | The number rests on a word with a common meaning that is not a number ("segundo", "quarto", "meio", "second", "half", "score"). |
| 0.3 | An article stands alone before a word that starts no number: Portuguese "um" or "uma" in "comprei uma casa". |

The gold corpus and its tests use 0.5 as the line between a weak mention and a clear number. A caller that wants only clear numbers keeps the mentions at 0.5 or above.

## Articles

In Portuguese, "um" and "uma" are both the number one and the indefinite article. Alone before a noun, the word gets 0.3. Inside a number, it is part of the number and the number gets the full score.

```python
>>> from numtag import tag_numbers
>>> def read(text, lang):
...     return [(m.text, m.value, m.confidence) for m in tag_numbers(text, lang)]
>>> read("Comprei uma casa.", "pt-PT")
[('uma', '1', 0.3)]
>>> read("Comprei uma dúzia de ovos.", "pt-PT")
[('uma dúzia', '12', 1.0)]
>>> read("Recebeu um milhão de euros.", "pt-PT")
[('um milhão', '1000000', 1.0)]
```

The low score needs a word after the article. An article before punctuation or at the end of the text keeps the full score, because no noun follows it. The same holds before digits. Before a word such as "ou", the article gets the low score, also when a number comes next.

```python
>>> read("Quantos filhos tens? Tenho um.", "pt-PT")
[('um', '1', 1.0)]
>>> read("Faltam uma ou duas semanas.", "pt-PT")
[('uma', '1', 0.3), ('duas', '2', 1.0)]
```

English "a" and "an" count one only before a word that takes a count: a multiplier, a collective, a fraction word or a half. Examples are "a hundred", "a dozen", "a third" and "a half". Alone, they are not a number, so numtag gives no mention.

```python
>>> read("I bought a house.", "en")
[]
>>> read("I bought a dozen eggs and a third of a pie.", "en")
[('a dozen', '12', 1.0), ('a third', '1/3', 1.0)]
```

## Words with a second meaning

A lexicon entry can carry `"ambiguous": true`. In Portuguese these are "meio", "meia", and "quarto" and "quartos" as a fraction. The ordinals "segundo", "quarto", "quinto" and "sexto" are ambiguous in every gender and number. In English they are "half", "second" and "score".

Such a word gives 0.4 when the number rests on it: the word alone, a fraction with it as the denominator, or an article with it as the collective. When other number words make the reading clear, the number gets 1.0.

```python
>>> read("Chegou em segundo lugar.", "pt-PT")
[('segundo', '2', 0.4)]
>>> read("Wait a second.", "en")
[('second', '2', 0.4)]
>>> read("Comeu três quartos do bolo.", "pt-PT")
[('três quartos', '0.75', 0.4)]
>>> read("A score of people came.", "en")
[('A score', '20', 0.4)]
>>> read("Ficou em vigésimo segundo lugar com um milhão e meio de votos.", "pt-PT")
[('vigésimo segundo', '22', 1.0), ('um milhão e meio', '1500000', 1.0)]
>>> read("Three score and ten years.", "en")
[('Three score and ten', '70', 1.0)]
```

The score does not tell which meaning is right. In "Chegou em segundo lugar" the word is the ordinal. In "Segundo o jornal" it means "according to". Both get 0.4, and the caller decides from the context.

## Readings that a low score marks

The gold corpus holds sentences where the word is not a number. numtag tags the word in most of them at 0.4, and a threshold of 0.5 drops these mentions. A collective with no count, as "score" in "The final score was seven.", gives no mention.

```python
>>> read("The final score was seven.", "en")
[('seven', '7', 1.0)]
```

```python
>>> read("Segundo o jornal, choveu muito.", "pt-PT")
[('Segundo', '2', 0.4)]
>>> read("Dormiu no quarto dos fundos.", "pt-PT")
[('quarto', '4', 0.4)]
>>> read("Está no meio da sala.", "pt-PT")
[('meio', '0.5', 0.4)]
>>> read("The error was one hundredth of a second.", "en")
[('one hundredth', '0.01', 1.0), ('second', '2', 0.4)]
```

A threshold also drops a real number when the weak word joins it. In "O apartamento tem três quartos e uma sala", "três quartos" means three bedrooms. numtag reads the fraction 0.75 at 0.4, and a threshold of 0.5 loses the count three.

```python
>>> read("O apartamento tem três quartos e uma sala.", "pt-PT")
[('três quartos', '0.75', 0.4), ('uma', '1', 0.3)]
```

## What a caller does with a low score

| Need | Action |
|---|---|
| Clear numbers only, for example to write digits | Keep the mentions with a confidence of 0.5 or above. |
| Every possible number, for example for a grammar that checks position | Keep all mentions, and let the grammar decide. A date grammar takes "uma" in "daqui a uma semana" as a count, because a count goes there. |
| A count after a known noun or verb | Keep the low mention when the slot needs a number, and drop it in other places. |

numtag gives one reading per stretch of words. A list of other readings, with a reason for each, is a planned feature. Read [roadmap.md](roadmap.md).

## Sources

The lexicon entry of each weak word cites its second meaning.

> Wiktionary, "second", noun: "A unit of time historically and commonly defined as a sixtieth of a minute".

> Wiktionary, "half", noun: "One of two usually roughly equal parts into which anything may be divided, or considered as divided".

> Dicio, "Meio-dia e meio ou meio-dia e meia": "A palavra meia é um numeral fracionário e se refere à metade de um todo, de uma unidade".

---
[← Number scale](number-scale.md) · [Home](index.md) · [Rulings →](rulings.md)
