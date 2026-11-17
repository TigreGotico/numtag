# English

numtag reads every `en` tag (`en`, `en-US`, `en-GB`, `en-AU`) with one lexicon, `numtag/lexicon/en.json`. English reads in the short scale: "billion" is 10^9.

```python
>>> from numtag import tag_numbers
>>> def read(text, lang="en"):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read("The company is worth two billion dollars.")
[('two billion', '2000000000')]
>>> read("The company is worth two billion pounds.", "en-GB")
[('two billion', '2000000000')]
```

> Wikipedia, "Long and short scales": "Use of the short scale is found in most English-speaking and Arabic-speaking countries"; Wikipedia, "English numerals": the short scale is "always used in American English and almost always in British English".

Pass `scale="long"` to read an older British text in the long scale. Read [../number-scale.md](../number-scale.md).

## What the lexicon reads

| Role | Entries | Examples |
|---|---|---|
| unit | 10 | "zero" to "nine" |
| ten | 18 | "ten" to "nineteen", "twenty" to "ninety" |
| hundred multiplier | 2 | "hundred", "hundreds" |
| scale noun | 46 | "thousand", "million", "billion", up to "centillion" |
| collective | 4 | "dozen", "score" and their plurals |
| half | 1 | "half" |
| denominator | 50 | "half", "third", "quarter", "tenth", "hundredth" and their plurals |
| ordinal | 27 | "first" to "twentieth", the round tens to "ninetieth" |
| ordinal scale | 5 | "hundredth", "thousandth", "millionth", "billionth", "trillionth" |
| ordinal suffix | 4 | "st", "nd", "rd", "th" |

The words are case-insensitive. Tens and units join with a hyphen or a space. Digits use "," to group and "." for decimals: "1,234,567.5".

```python
>>> read("Seventy-five or seventy five people paid 1,234,567.5 dollars.")
[('Seventy-five', '75'), ('seventy five', '75'), ('1,234,567.5', '1234567.5')]
>>> read("She was 21st, then the twenty-first, then the one hundred and first.")
[('21st', '21'), ('twenty-first', '21'), ('one hundred and first', '101')]
>>> read("Add a half cup, two fifths and three quarters.")
[('a half', '0.5'), ('two fifths', '0.4'), ('three quarters', '0.75')]
```

"twelve hundred" multiplies the hundred. "a" counts one before a word that takes a count.

```python
>>> read("It cost twelve hundred dollars, a hundred more than a dozen others.")
[('twelve hundred', '1200'), ('a hundred', '100'), ('a dozen', '12')]
```

## The settings

| Setting | Value | Source |
|---|---|---|
| `joiner_tens_units` | never | Wikipedia, "English numerals" |
| `joiner_after_hundred` | optional | CLDR 49 RBNF en; Wikipedia, "English numerals" |
| `joiner_between_groups` | optional | the same |
| `joiner_before_last_group` | optional | the same |
| `joiner_before_round_hundred` | false | CLDR 49 RBNF en %spellout-cardinal-verbose |
| `comma_between_classes` | true | Wikipedia, "English numerals"; CLDR 49 RBNF en |
| `plural_scale_needs_count` | true | Wiktionary, "million" |
| `scale_noun_agrees` | false | Wiktionary, "million", usage notes |
| `ordinal_style` | last_word | CLDR 49 RBNF en %spellout-ordinal |
| `ten_joins_unit_ordinal` | false | Wikipedia, "English numerals" |
| `part_after_joiner_needs_article` | true | Wikipedia, "English numerals" |

[../rulings.md](../rulings.md) quotes each source and shows each rule at work.

> CLDR 49 RBNF en %spellout-ordinal: "20: twent[y->>|ieth];", "100: <%spellout-numbering< hundred[ >>|th];".

In these rules the words before the last are cardinal. Only the last word of an ordinal is ordinal: "twenty-first", "one hundred and first".

A unit ordinal joins a ten from twenty up, with a hyphen or a space and no "and", as a unit does in a cardinal. So "ten fifth" is 10 and 5th, and "forty and first" is 40 and 1st.

```python
>>> read("The school sent ten fifth graders to the science fair.")
[('ten', '10'), ('fifth', '5')]
>>> read("He turned forty and first visited Japan that spring.")
[('forty', '40'), ('first', '1')]
```

> Wikipedia, "English numerals": "if a number is in the range 21 to 99, and the second digit is not zero, the number is typically written as two words separated by a hyphen".

> Wiktionary, "million", numeral sense 2: "(colloquial, hyperbolic) An unspecified very large number".

So a plural scale word with no count, as in "millions of people", names no number. With a count, as in "two million people", it does.

## Word lists

| List | Words | Use |
|---|---|---|
| `joiner` | "and" | joins the parts of a number |
| `decimal_marker` | "point" | starts the fraction part |
| `minus` | "minus", "negative" | makes the number negative |
| `article_one` | "a", "an" | counts one before a word that takes a count |
| `fraction_of` | "of" | "one third of a dozen" |
| `lone_decimal_mark` | "." | ".5" |
| `range_cue` | "between" | "between forty and fifty dollars" (source: Wiktionary, "between") |

The lists `minus_idioms`, `of`, `denominator_particle`, `class_noun`, `half_unit` and `abbreviation` are empty in English. Each empty list carries its source too.

```python
>>> read("It was minus forty, negative two, or between forty and fifty dollars.")
[('minus forty', '-40'), ('negative two', '-2'), ('forty', '40'), ('fifty', '50')]
>>> read("I ate one third of a dozen eggs.")
[('one third of a dozen', '4')]
```

## Year pairs

numtag reads "nineteen ninety nine" as two numbers, 19 and 99. A year grammar joins two adjacent cardinals into a year. That is a date rule, and it belongs to the caller.

```python
>>> read("She was born in nineteen ninety nine.")
[('nineteen', '19'), ('ninety nine', '99')]
```

## Known misreadings

The English gold corpus has 420 rows, and numtag reads 419 of them right. The miss is "second" as a time unit.

```python
>>> [(m.text, m.value, m.confidence) for m in tag_numbers("The error was one hundredth of a second.", "en")]
[('one hundredth', '0.01', 1.0), ('second', '2', 0.4)]
```

The gold row has one mention, 0.01. numtag also gives "second" as the ordinal 2, at the low score 0.4. Read [../confidence-and-homographs.md](../confidence-and-homographs.md).

---
[← Portuguese](pt.md) · [Home](../index.md) · [Adding a language →](../adding-a-language.md)
