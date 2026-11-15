# Design

numtag has one reader. It turns a text into tokens, splits the tokens into runs, parses the longest number at each position of a run, and computes each value with arithmetic on digit strings. This page describes each step and the principles behind it.

## Principles

| Principle | What it means in the code |
|---|---|
| One reader | Every number goes through the same grammar. A caller that wants another view, such as the text with digits, builds it from the mentions. |
| A number is a mention | Each mention holds the exact words, their character span, an exact value and a kind. |
| A value is a digit string | numtag builds each value by arithmetic on strings of digits. No value passes through `int`, `float`, `Decimal` or `Fraction` inside the package. |
| The grammar decides where a number ends | A number ends where no rule takes the next word. "twenty one twenty" is 21 and 20, because "twenty" cannot follow a unit. |
| Language facts are data | Each language is one JSON lexicon. Each word and setting carries the source of its rule. |
| Reader only | numtag does not write numbers as words. |
| Deterministic | The same text, language and scale always give the same mentions, with the same scores. |

## The steps

### 1. Tokens

The tokenizer (`numtag/tokenize.py`) splits the text into words and digit strings. Each token keeps its character offsets and the text between it and the token before it. Punctuation is never a token. It shows only in these gaps.

A digit string keeps its group and decimal marks ("1.000.000,5"). A minus sign belongs to it only at the start of a word, so "-5" is negative and "5-7" is two numbers. These tokens are dropped:

| Case | Example | Reason |
|---|---|---|
| Digits glued to the end of a word | "mp3" | part of a name |
| A digit run with a digit outside 0-9 | "٣" | numtag reads ASCII digits only |
| A listed word with a period and no sentence end after it | "dez." in "3 dez. 2025" | an abbreviation |
| The words of a hyphenated compound with a word that is not a number word | "segunda-feira" | one noun |

```python
>>> from numtag import tag_numbers
>>> def read(text, lang="pt-PT"):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read("Ouviu o mp3 três vezes na segunda-feira, de 5-7 de março.")
[('três', '3'), ('5', '5'), ('7', '7')]
```

A word glued to digits is an ordinal suffix when the lexicon lists it: "1.º", "2.ª", "21st".

### 2. Runs

A run is a stretch of tokens with only spaces or hyphens between them. A number never crosses punctuation, so each run is parsed on its own. In Portuguese one exception holds: a comma after a scale word and before a number word links two classes of one number.

```python
>>> read("Vieram três, quatro e cinco.")
[('três', '3'), ('quatro', '4'), ('cinco', '5')]
>>> read("Custou dois milhões, duzentos e trinta e seis mil euros.")
[('dois milhões, duzentos e trinta e seis mil', '2236000')]
```

### 3. Lexicon

The loader (`numtag/lexicon/__init__.py`) reads the JSON file of the language, applies `extends`, and builds an index from each word to its readings. One word can have more than one reading: "quarto" is a denominator and an ordinal. The loader keeps one lexicon per language and scale in memory after the first call.

### 4. Grammar

The grammar (`numtag/grammar.py`) is one engine with per-language settings. At a token position, each rule returns every way that it can read a number that starts there, as parses that record where they end.

```text
number      := minus? (cardinal tail? | half-group | fraction | ordinal | digits-ordinal)
cardinal    := group (joiner? group)*            group scales strictly descending
group       := count? multiplier | small | small-decimal | digits
multiplier  := scale-word
count       := small | small-decimal | digits | cardinal of thousands   ("mil e quinhentos" milhões)
small       := hundreds (joiner tens-units)? | tens-units      below 1000
tail        := collective-tail | of-tail | half-tail | fraction-tail | decimal-tail
             | half-collective-tail                              "cem e meia dúzia"
```

The settings of the lexicon decide where a joiner is required, optional or never, whether a scale noun agrees with its count, and whether every word of an ordinal is ordinal. The grammar has no language name in it.

### 5. The choice of reading

The tagger (`numtag/tagger.py`) walks each run from left to right. At each position it keeps the longest parse, makes a mention, and goes on after its end. Two rules can end the first number earlier:

| Rule | Example |
|---|---|
| After a range cue, the first number ends at a joiner that splits the words into two numbers, the first smaller. | "entre cem mil e um milhão" is 100000 and 1000000 |
| Where the same words split into two numbers at more than one joiner, the split with the fewest significant digits wins, then the longest first number. | "mil milhões e mil e quinhentos milhões" is 10^9 and 1500000000 |

[rulings.md](rulings.md) gives the sources and more examples.

The tagger then fills the other fields. The kind comes from the parse and the value, and the form from the tokens. The gender comes from the last word that shows one. The confidence comes from the article and ambiguity rules, and the number scale from the scale words.

### 6. Values

`numtag/digits.py` does the arithmetic. A magnitude is a string of ASCII digits. A `Rational` is a sign, a numerator and a denominator, each a magnitude. The module adds, subtracts, multiplies, divides with a remainder and finds the greatest common divisor, digit by digit. A scale word appends zeros: "três centenas de milhões" appends six zeros to 300 and never multiplies two large numbers.

`Rational.canonical` writes the value string. It reduces a fraction to lowest terms and writes a fraction whose denominator divides a power of ten as a decimal.

The tests of `digits.py` compare each operation with Python's own `int` and `Fraction` on random inputs, up to 1000 digits long. Only the tests use those types.

## Time

The time to tag a text grows in a straight line with its length. The split search after a joiner stops at the end of the longest reading. So a run of number words with no joiner ("um um um") stays linear. `tests/test_growth.py` reads each test text at n and at 8n copies, and fails when the time grows more than 12 times.

## Determinism

numtag holds no model and no random state. The output depends only on the text, the language and the scale. The confidence is a fixed score from rules, not a probability. Two mentions compare equal when all fields but the confidence are equal, so a test can compare readings without a score.

---
[← Adding a language](adding-a-language.md) · [Home](index.md) · [Benchmarks →](benchmarks.md)
