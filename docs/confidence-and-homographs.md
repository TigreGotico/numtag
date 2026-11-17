# Confidence and homographs

Some number words have a second meaning. Portuguese "uma" is also the article "a", and "segundo" is also "according to". English "second" is also a unit of time. numtag tags these words and gives them a low confidence. The caller decides what to keep.

## The scores

The confidence is a fixed score in (0, 1]. It is not a probability. The same text and language always give the same score.

| Score | When |
|---|---|
| 1.0 | The words are a number for certain. |
| 0.4 | The number rests on a word with a common meaning that is not a number ("segundo", "quarto", "meio", "second", "half", "score"). |
| 0.3 | An article stands alone before its noun phrase: a word that starts no number, a number in digits, an ordinal or a lone word with a second meaning. Portuguese "um" or "uma" in "comprei uma casa". |

The gold corpus and its tests use 0.5 as the line between a weak mention and a clear number. A caller that wants only clear numbers keeps the mentions at 0.5 or above.

A weak mention also says why it is weak. Its `reasons` field holds `Reason.ARTICLE` for an article and `Reason.HOMOGRAPH` for a word with a second meaning. A sure number has no reasons. The scores can change in a release, and the reasons keep their meaning, so filter on the reason.

## Articles

In Portuguese, "um" and "uma" are both the number one and the indefinite article. Alone before a noun, the word gets 0.3. A hyphenated noun ("guarda-chuva") counts as a noun. An article that is the whole text, such as a line of a vocabulary file, also gets 0.3: no noun decides it. Inside a number, it is part of the number and the number gets the full score.

```python
>>> from numtag import tag_numbers
>>> def read(text, lang):
...     return [(m.text, m.value, m.confidence) for m in tag_numbers(text, lang)]
>>> read("Comprei uma casa.", "pt-PT")
[('uma', '1', 0.3)]
>>> read("Devo levar um guarda-chuva.", "pt-PT")
[('um', '1', 0.3)]
>>> read("um", "pt-PT")
[('um', '1', 0.3)]
>>> read("Comprei uma dúzia de ovos.", "pt-PT")
[('uma dúzia', '12', 1.0)]
>>> read("Recebeu um milhão de euros.", "pt-PT")
[('um milhão', '1000000', 1.0)]
```

The low score needs a word after the article. An article before punctuation or at the end of the text keeps the full score, because no noun follows it. Before a word such as "ou", the article gets the low score, also when a number comes next. Before a number in digits or an ordinal, the article also gets the low score: the number is part of its noun phrase, as in "un 20 por ciento" and "um segundo facto".

```python
>>> read("Quantos filhos tens? Tenho um.", "pt-PT")
[('um', '1', 1.0)]
>>> read("Faltam uma ou duas semanas.", "pt-PT")
[('uma', '1', 0.3), ('duas', '2', 1.0)]
>>> read("Baja el brillo a un 20 por ciento.", "es")
[('un', '1', 0.3), ('20', '20', 1.0)]
>>> read("Dá-me um segundo facto.", "pt-PT")
[('um', '1', 0.3), ('segundo', '2', 0.4)]
```

> DPD "uno, una" 1.1: "Como determinante, toma la forma un ante sustantivos masculinos, los preceda inmediatamente o no"; 2.2: "Es incorrecta la apócope de uno y sus compuestos cuando no van antepuestos a un sustantivo"

Before a lone word with a second meaning, the article also gets the low score. Catalan "nou" is nine and "new", and "un nou enregistrament" is "a new recording". The word keeps its own score 0.4.

```python
>>> read("Inicia un nou enregistrament.", "ca")
[('un', '1', 0.3), ('nou', '9', 0.4)]
```

English "a" and "an" count one only before a word that takes a count: a multiplier, a collective, a fraction word or a half. Examples are "a hundred", "a dozen", "a third" and "a half". Alone, they are not a number, so numtag gives no mention.

```python
>>> read("I bought a house.", "en")
[]
>>> read("I bought a dozen eggs and a third of a pie.", "en")
[('a dozen', '12', 1.0), ('a third', '1/3', 1.0)]
```

German and Spanish count with a form that is not the article: "eins" and "uno". A lone article at the end of a clause is the article or a pronoun, so "ein", "eines", "un" and "una" get the low score there. The counting form keeps the full score.

```python
>>> read("Muéstrame una.", "es")
[('una', '1', 0.3)]
>>> read("Quedó uno.", "es")
[('uno', '1', 1.0)]
>>> read("Er lud mich ein.", "de")
[('ein', '1', 0.3)]
```

> DPD "uno, una" 2.2: "Es incorrecta la apócope de uno y sus compuestos cuando no van antepuestos a un sustantivo"

## Words with a second meaning

A lexicon entry can carry `"ambiguous": true`. In Portuguese these are "meio", "meia", and "quarto" and "quartos" as a fraction. The ordinals "segundo", "quarto", "quinto" and "sexto" are ambiguous in every gender and number. In English they are "half", "second" and "score". In French, "premier" is also "prime" and "original" in every gender and number. In Italian, "primo" is also "prime", and "prima" is also "before".

Such a word gives 0.4 when the number rests on it: the word alone, a fraction with it as the denominator, or an article with it as the collective. When other number words make the reading clear, the number gets 1.0.

```python
>>> read("Chegou em segundo lugar.", "pt-PT")
[('segundo', '2', 0.4)]
>>> read("Wait a second.", "en")
[('second', '2', 0.4)]
>>> read("Chiamami prima di cena.", "it")
[('prima', '1', 0.4)]
>>> read("Comeu três quartos do bolo.", "pt-PT")
[('três quartos', '0.75', 0.4)]
>>> read("A score of people came.", "en")
[('A score', '20', 0.4)]
>>> read("Ficou em vigésimo segundo lugar com um milhão e meio de votos.", "pt-PT")
[('vigésimo segundo', '22', 1.0), ('um milhão e meio', '1500000', 1.0)]
>>> read("Three score and ten years.", "en")
[('Three score and ten', '70', 1.0)]
```

A word before the homograph can also make the reading clear when it agrees only with the number. In Catalan, the adjective "nou" ("new") is "noves" after "les" and "nous" after "els", so "a les nou" is nine o'clock. After "el", "nou" can also be "the new one".

```python
>>> read("Avisa'm a les nou del matí.", "ca")
[('nou', '9', 1.0)]
>>> read("Ha arribat el nou.", "ca")
[('nou', '9', 0.4)]
```

A word next to the homograph can also make the other meaning likely. Hungarian "hat" is six and the verb "to take effect". The verb ends a clause ("A gyógyszer nem hat."), follows "nem" ("not"), and stands before the -ra pronoun of what it acts on ("hat rám"). There "hat" gives 0.4. Before a noun, "hat" counts the noun. The case form "hatkor" ("at six") is no verb form.

The cues look only at the words next to "hat". After "nem", "hat" gives 0.4 also before a noun: "nem hat perc" ("not six minutes"). A joiner after "hat" ends the clause when no number follows it: "hat és működik" gives 0.4, and "hat és hét" stays sure. The value stays 6, and the caller decides.

Right after a request verb, "hat" is no verb, because a finite verb does not follow another finite verb in one clause. So it is six: "kérek hat", "legyen hat", "állítsd hat". A word that is weak only at the end of a clause is sure when it is the whole text with no punctuation, because a one-word text with no punctuation is a spoken answer: "hat", fr "neuf" and ro "nouă" give the full score alone. With a full stop ("Hat.") or inside a clause, they give 0.4.

```python
>>> read("A gyógyszer nem hat.", "hu")
[('hat', '6', 0.4)]
>>> read("Ez a zene hat rám.", "hu")
[('hat', '6', 0.4)]
>>> read("Hat perc múlva indulunk.", "hu")
[('Hat', '6', 1.0)]
```

A whole number before the joiner and a minus word also make the reading clear.

```python
>>> read("Faltam três e um quarto.", "pt-PT")
[('três e um quarto', '3.25', 1.0)]
>>> read("Temperatuur oli miinus viis kraadi.", "et")
[('miinus viis', '-5', 1.0)]
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

Digits before a denominator count its parts: "3 quarters" is 0.75 and "2 terços" is 2/3. An ambiguous denominator takes no digits, because a fraction in digits is written "3/4". So "3 quartos" keeps the count three, and "quartos" stands alone at 0.4.

```python
>>> read("O apartamento tem 3 quartos e uma sala.", "pt-PT")
[('3', '3', 1.0), ('quartos', '4', 0.4), ('uma', '1', 0.3)]
>>> read("Comeu 2 terços do bolo.", "pt-PT")
[('2 terços', '2/3', 1.0)]
```

## What a caller does with a low score

| Need | Action |
|---|---|
| Clear numbers only, for example to write digits | Keep the mentions with a confidence of 0.5 or above. |
| Every number except the articles | Drop the mentions with `Reason.ARTICLE` in their `reasons`. |
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
