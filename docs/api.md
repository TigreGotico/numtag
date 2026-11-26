# API reference

<!-- agent-hint
covers: Every public name of the package with its signature, fields and defaults.
source: numtag/__init__.py:__all__, numtag/tagger.py, numtag/mention.py, numtag/vague.py:tag_vague_quantities, numtag/roman.py
generated: no
verify: sed '/^\x60\x60\x60/d' docs/api.md | python -m doctest -o NORMALIZE_WHITESPACE /dev/stdin
see: getting-started.md, values.md
-->

The package `numtag` exports nineteen names: `tag_numbers`, `NumberMention`, `Part`, `Role`, `Kind`, `Form`, `Reason`, `Scale`, `is_canonical_value`, `ARTICLE_CONFIDENCE`, `UnsupportedLanguageError`, `tag_vague_quantities`, `VagueQuantity`, `VagueKind`, `revision`, `spell`, `Spelling`, `SpellingReason` and `SpokenForm`. This page describes each of them. Every other module is internal.

```python
>>> import numtag
>>> sorted(numtag.__all__)
['ARTICLE_CONFIDENCE', 'Form', 'Kind', 'NumberMention', 'Part', 'Reason', 'Role', 'Scale', 'Spelling', 'SpellingReason', 'SpokenForm', 'UnsupportedLanguageError', 'VagueKind', 'VagueQuantity', 'is_canonical_value', 'revision', 'spell', 'tag_numbers', 'tag_vague_quantities']
```

## tag_numbers

```text
tag_numbers(text: str, lang: str, *, scale: Scale | None = None) -> list[NumberMention]
```

`tag_numbers` returns every number in `text` as a list of `NumberMention` objects. The list is in reading order, and no two mentions overlap.

| Argument | Meaning |
|---|---|
| `text` | The text to read. numtag never changes it. |
| `lang` | A language tag. `pt-BR` reads Brazilian Portuguese and every other `pt` tag reads European Portuguese. `fr-BE`, `fr-CH` and `ca-ES-valencia` read their own lexicons. Every other `fr` tag reads `fr-FR`, and `no` reads Norwegian Bokmål. Every other tag reads the lexicon of its primary subtag: `de-AT` reads `de`. The README lists the lexicons. The tag may use `-` or `_`, in any case. |
| `scale` | Optional, keyword only. `Scale.LONG`, `Scale.SHORT`, `"long"` or `"short"`. It replaces the default scale of the language. Read [number-scale.md](number-scale.md). |

`tag_numbers` raises `UnsupportedLanguageError` for a language with no lexicon. It is a subclass of `ValueError`, so a caller can catch it alone and skip the text, or catch `ValueError` for every bad argument. A `scale` that is not a scale raises a plain `ValueError`. An empty value reads the default scale.

```python
>>> from numtag import UnsupportedLanguageError, tag_numbers, Scale
>>> try:
...     tag_numbers("二", "ja")
... except UnsupportedLanguageError as error:
...     print(error)
no lexicon for language 'ja'
>>> tag_numbers("one", "en", scale="medium")
Traceback (most recent call last):
  ...
ValueError: 'medium' is not a valid Scale
>>> tag_numbers("one billion", "en", scale="")[0].number_scale
<Scale.SHORT: 'short'>
```

At each position, numtag takes the longest number that its grammar can read, from left to right. A number never crosses punctuation other than a hyphen ("twenty-one"). In Portuguese and English, one exception holds: a comma after a scale word can join two classes of one number. Read [rulings.md](rulings.md).

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
| `lang` | `str` or `None` | Keyword only, left out of equality and of the representation. The name of the lexicon that read the mention ("pt-PT" for a "pt" call). `spoken` uses it |

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

A mention checks its own fields when it is made. It raises `ValueError` in these cases. The span does not fit the text, or the value is not canonical. `number_scale` is not a `Scale` or `None`, or `reasons` is not a frozenset of `Reason`. A part is not inside the mention or not in reading order.

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

The mention value is the one exact answer. A caller does not add up the parts. A part value is the number that its words name alone. The half of "um milhão e meio" has the value 0.5, and the mention has 1500000. Deep time divides the mention value by the value of the last scale part:

```python
>>> m = tag_numbers("Há sessenta e seis milhões de anos.", "pt-PT")[0]
>>> [(p.role.value, p.text, p.value) for p in m.parts]
[('count', 'sessenta e seis', '66'), ('scale', 'milhões', '1000000')]
```

These rules decide the parts:

1. Every word of a mention is in exactly one part. Spaces, hyphens, the slash of a digit fraction and the comma between classes are in no part.
2. A count below the next scale word is one count part, with the joiners inside it: "sessenta e seis", "two hundred", "vigésimo primeiro".
3. A digit string is one part, with its group marks, its decimal mark and its sign: "1.234,5", "-5", "21st".
   A digit fraction is a count and a denominator: "3/4" is the count "3" and the denominator "4".
4. An article that the grammar reads as one is a count with the value 1: "a" in "a quarter", and in "a half" alone, which is the count "a" and the denominator "half". Any other article, ordinal prefix, ending or particle is in the part that it introduces or ends: "a half" in "one and a half", "a dozen" after "half", "doze avos".
5. An ordinal has no role of its own, because the mention kind says ORDINAL. "six thousand two hundredth" is the count "six", the scale "thousand" and the count "two hundredth" (200).
6. A word that holds two parts is one part. The dual "ألفين" (two thousand) is one scale part with the value 1000, and "ثلثان" (two thirds) is one denominator part with the value 3.
7. Inside a compound word, the parts follow its sub-words: "dreihunderttausend" is the count "dreihundert" and the scale "tausend". Where two sub-words share a letter (Swedish "ettusen"), the two parts overlap by that letter.

The parts are flat, and they do not show the scope of a collective: "dois mil e duas dúzias" and "dois mil e duas centenas" have the same roles. Two parts compare equal when all their fields are equal.

```python
>>> [(p.role.value, p.text, p.value) for p in tag_numbers("one point two million", "en")[0].parts]
[('count', 'one', '1'), ('decimal_mark', 'point', None), ('decimals', 'two', '0.2'), ('scale', 'million', '1000000')]
```

A part checks its own fields when it is made. It raises `ValueError` in three cases. The span does not fit the text, the value is not canonical, or a role that names no number has a value.

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
| `Role.HALF` | `"half"` | "meia", "meio", "einhalb", "a half" in "one and a half" | 0.5 |
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
| `Form.ROMAN` | `"roman"` | "XIV", "Ⅻ" |

A minus word before digits does not change the form.

```python
>>> [(m.text, m.value, m.form.value) for m in tag_numbers("menos 5 e 2 milhões", "pt-PT")]
[('menos 5', '-5', 'digits'), ('2 milhões', '2000000', 'mixed')]
```

## Roman numerals

A Roman numeral is a mention with `Form.ROMAN`. Its value is a digit string, as for any other mention. The numeral is one count part. numtag reads a numeral only where no number word or digit string stands. So pt "MIL" and fr "DIX" keep their word reading.

```python
>>> [(m.text, m.value, m.kind.value) for m in tag_numbers("Luís XIV morreu em 1715.", "pt-PT")]
[('XIV', '14', 'ordinal'), ('1715', '1715', 'cardinal')]
>>> [(m.text, m.value, m.kind.value, m.confidence) for m in tag_numbers("see page XXI", "en")]
[('XXI', '21', 'cardinal', 0.4)]
>>> tag_numbers("Can I play the CD?", "en")
[]
```

The numeral must be well formed: 1 to 3999 in the standard subtractive form, all in upper case or all in lower case. "IIII", "IC" and "Xiv" are no numeral. The Unicode Roman numeral characters U+2160 to U+2188 are always numerals, and their value comes from the Unicode Standard.

A cue makes the numeral a sure ordinal:

| Cue | Example |
|---|---|
| A series noun before the numeral (`roman_series_noun`) | "século XIX", "World War II", "capítulo xii" |
| A series noun after a numeral that is no word | "the XXI century" |
| A title-case word before an upper-case numeral that is no word | "Luís XIV", "Edition XIV" |
| A regnal title (`roman_title`), then a name | "King Henry I", "D. João I", "Papst Benedikt XVI" |
| A cued numeral before it in a list, after a comma or a joiner, for a numeral that is no word | "séculos XI, XII e XIII" |

German writes every noun in title case, so in German a title-case word is no cue (setting `roman_title_case_cue`): "Größe XIV" is a cardinal with `Reason.HOMOGRAPH`. A capitalised word at the start of a sentence is a cue in the other languages, so "In MMXXIV we moved" reads a sure 2024.

A numeral next to a digit is part of a code, and gives no mention: "Mazda CX5", "3XL".

With no cue, an upper-case numeral is a cardinal with `Reason.HOMOGRAPH` ("XIV" alone, "page XXI"). A lower-case numeral with no cue reads only as a list item at the start of a line (pt "ii)", "(iv)"). It gives no mention elsewhere, because most lower-case numerals are words ("mi", "vi").

A single letter is a numeral only as I, V or X. L, C, D and M alone are labels ("Part D", "Vitamin C"), and give no mention.

A single letter or a numeral in the language's `roman_word` list ("CD", "MIX", "IV") is far more often a pronoun, an initial or a label. It reads only in upper case, and only after one of two cues:

- a series noun before it ("World War I", "Part I")
- a regnal title, then a name of one or two words on the same line: "King Henry I", "Queen Elizabeth I", "Pope John Paul I", "D. João I", "Papa Pio X". Only a one-letter title ends in a period ("D."), so "I met the King. Then I left." gives no mention.

A name alone, two names and a list are no cue. So these give no mention for the pronoun: "Can I get a math fact", "Play CD", "Give IV fluids" and "Henry I died". "tell John I am late", "I told Mary Jane I would come" and "After World War I, I moved" give none either. A capital letter before a name is an initial, not a numeral: "General D K Arya".

A word in the `roman_lower_word` list is a word only in lower case. So pt, es and it "vi" give no mention, and "Felipe VI" or "Paolo VI" read like any other numeral. All-caps text such as "EU VI UMA CENA" gives a cardinal with `Reason.HOMOGRAPH`, because an all-caps word is no title-case cue.

In English "I" is a pronoun, so a series noun before a single letter or a listed word counts only in title case (setting `roman_pronoun_letters`): "Part I" reads, "the part I like" and "which chapter I should read" do not. Other languages keep the lower-case noun: "século I", "siglo V".

numtag gives the value and the kind. How a numeral is said, "Luís XIV" as "catorze" or "D. João VI" as "sexto", is a rule of the speaking language and belongs to text2spoken.

## tag_vague_quantities

```text
tag_vague_quantities(text: str, lang: str) -> list[VagueQuantity]
```

`tag_vague_quantities` returns the words of `text` that state an amount but no exact number. The list is in reading order, and no two results overlap. `lang` works as in `tag_numbers`, and a language with no lexicon raises `UnsupportedLanguageError`. A language with no `vague_quantifier` entries returns an empty list. English, Portuguese, Croatian, Turkish, Dutch and German have entries.

A vague word never becomes a digit, so `tag_numbers` gives no mention for it. A count before a plural scale word makes an ordinary number, and no vague quantity: "three million" is 3000000.

```python
>>> from numtag import tag_vague_quantities, VagueKind
>>> text = "Navios-tanque podem carregar desde várias centenas de toneladas."
>>> [(q.text, q.kind.value, q.scale, q.lower_bound) for q in tag_vague_quantities(text, "pt-PT")]
[('várias centenas', 'magnitude', '100', '200')]
>>> tag_numbers(text, "pt-PT")
[]
>>> tag_vague_quantities("It serves a region of three million people.", "en")
[]
```

There are two kinds of result.

| Kind | Words | `scale` | `lower_bound` |
|---|---|---|---|
| `VagueKind.MAGNITUDE` | a plural scale word with no count: "millions", "dozens", "milhares", "dezenas" | the scale word: "1000000", "12" | two of the scale: "2000000", "24" |
| `VagueKind.MAGNITUDE` | a vague word and the scale words after it: "several million", "a few dozen", "muitos mil milhões" | the product of the scale words: "1000000", "12", "1000000000" | two of the scale when one plural scale word follows ("alguns milhares"), else `None` |
| `VagueKind.AMOUNT` | a vague word alone: "many", "several", "a few", "umpteen", "muitos", "alguns" | `None` | `None` |

```python
>>> text = "Benthic landers have deployment durations from a few days to several years."
>>> [(q.text, q.kind.value) for q in tag_vague_quantities(text, "en")]
[('a few', 'amount'), ('several', 'amount')]
>>> [(q.text, q.scale, q.lower_bound) for q in tag_vague_quantities("Several million years ago.", "en")]
[('Several million', '1000000', None)]
```

A word that is also an ordinary noun, adjective or adverb gets a low confidence and `Reason.HOMOGRAPH`, as in `tag_numbers`. "a lot" also names an area of land, and "bastante" also means "enough". A scale word after the vague word makes the quantity reading clear.

```python
>>> [(q.text, q.confidence, sorted(q.reasons)) for q in tag_vague_quantities("O ciclismo é um esporte bastante popular.", "pt-BR")]
[('bastante', 0.4, [<Reason.HOMOGRAPH: 'homograph'>])]
```

Fixed counts are no vague quantity. "half a dozen" and "meia dúzia" have a value, so `tag_numbers` reads them.

## VagueQuantity

A `VagueQuantity` is a frozen dataclass.

| Field | Type | Meaning |
|---|---|---|
| `char_span` | `tuple[int, int]` | The half-open character range of the words, as in `NumberMention` |
| `text` | `str` | The exact words |
| `kind` | `VagueKind` | `MAGNITUDE` or `AMOUNT` |
| `scale` | `str` or `None` | The digit string of the scale of a magnitude, a positive whole number |
| `lower_bound` | `str` or `None` | Two of the scale, when the scale word is plural |
| `confidence` | `float` | A fixed score from 0 to 1, not part of equality |
| `reasons` | `frozenset[Reason]` | Keyword only, not part of equality. Why the confidence is low |

A `VagueQuantity` checks its fields when it is made. It raises `ValueError` in these cases. The span does not fit the text. An amount has a scale or a bound, or a magnitude has no scale. A scale or bound is not a positive whole digit string, or the bound is below the scale. The confidence is not a number from 0 to 1.

```python
>>> from numtag import VagueQuantity
>>> VagueQuantity((0, 7), "several", VagueKind.AMOUNT, "100")
Traceback (most recent call last):
  ...
ValueError: an amount takes no scale and no lower bound
```

## VagueKind

`VagueKind` is a string enum with two members: `VagueKind.MAGNITUDE` (`"magnitude"`) and `VagueKind.AMOUNT` (`"amount"`).

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

## spell

```text
spell(value: str, lang: str, *, form=SpokenForm.CARDINAL, gender=None, case=None, scale=None, places=None, scientific=False, decimals=None) -> tuple[Spelling, ...]
```

`spell` writes a number as words. It returns every accepted spelling of `value` in the language, best first. The first spelling is the default one. `value` is a canonical digit string ("21", "-2.5") or a fraction "n/m". `lang` works as in `tag_numbers`. A language whose lexicon has no `writer` block raises `UnsupportedLanguageError`. [lexicon-format.md](lexicon-format.md#the-writer-block) says what a block holds and how its rules run.

| Argument | Meaning |
|---|---|
| `form` | A `SpokenForm`: `CARDINAL` ("twenty-one"), `ORDINAL`, `YEAR` (the cardinal where the lexicon has no year rules) or `DIGITS` (each digit alone) |
| `gender` | `"masculine"`, `"feminine"` or `"neuter"`. It selects a reading where the lexicon lists one, and a lexicon that lists none ignores it |
| `case` | A case name that the lexicon lists. Any other case raises `ValueError` |
| `scale` | `Scale.SHORT` or `Scale.LONG`. A lexicon with no scale rules ignores it |
| `places` | The count of decimals read, rounded half away from zero. The default is the lexicon's |
| `scientific` | Read a large or small value as a mantissa and an exponent, where the lexicon has the words for it |
| `decimals` | `"digits"` reads one word for each decimal, and `"number"` reads the decimals as one number ("dois vírgula vinte e cinco"), with the trailing zeros as written ("1.80" reads "um vírgula oitenta"). Another value raises `ValueError`. The default is the lexicon's |

```python
>>> from numtag import SpokenForm, spell, tag_numbers
>>> [s.text for s in spell("21", "id")]
['dua puluh satu']
>>> spell("2.25", "ms")[0].text, spell("-1500", "id")[0].text
('dua koma dua lima', 'minus seribu lima ratus')
>>> spell("2", "id", form=SpokenForm.ORDINAL)[0].text, spell("1", "id", form=SpokenForm.ORDINAL)[0].text
('kedua', 'pertama')
>>> spell("21", "id", form=SpokenForm.DIGITS)[0].text
'dua satu'
>>> spell("2/3", "id")[0].text, spell("-1/4", "id")[0].text
('dua pertiga', 'minus seperempat')
>>> spell("1500000000", "ms", scientific=True)[0].text
'satu koma lima kali sepuluh pangkat sembilan'
```

An ordinal below its minimum raises `ValueError`, and so does a case that the lexicon lacks. A fraction with a denominator of 0 raises `ZeroDivisionError`.

```python
>>> spell("0", "id", form=SpokenForm.ORDINAL)
Traceback (most recent call last):
  ...
ValueError: ordinals must be whole numbers from 1
>>> spell("1", "id", case="genitive")
Traceback (most recent call last):
  ...
ValueError: id: no case 'genitive'; it has []
>>> spell("1", "en")
Traceback (most recent call last):
  ...
numtag.lexicon.UnsupportedLanguageError: no writer for language 'en'
```

## Spelling

A `Spelling` is a frozen dataclass of `text`, `reason` and `rank`. The `rank` is the place in the list of the lexicon, from 0. The `reason` is a `SpellingReason`: `standard`, `no_conjunction`, `year_pairs`, `plain`, `counting` or `variant_spelling`. A lexicon lists the spellings of a form in the order that its sources set, and numtag computes no score. A difference of region ("dezasseis" and "dezesseis") is a different lexicon and not a rank.

## NumberMention.spoken

```text
NumberMention.spoken(lang=None, *, form=None, gender=None, case=None, scale=None, places=None) -> tuple[Spelling, ...]
```

`spoken` writes the value of a mention as words. It calls `spell` with the value. `lang` defaults to the lexicon that read the mention. `form` defaults to the ordinal for an ordinal mention and to the cardinal for every other kind, and `gender` defaults to the gender of the mention. A digit mention gives its words, and a word mention gives the canonical words of its value. A fraction mention speaks as a fraction in lowest terms, also when its value is a finite decimal: "setengah" has the value 0.5 and speaks "setengah".

```python
>>> tag_numbers("dua puluh satu orang", "id")[0].spoken()[0].text
'dua puluh satu'
>>> tag_numbers("21 orang", "ms")[0].spoken()[0].text
'dua puluh satu'
>>> tag_numbers("kedua", "id")[0].spoken("ms", form=SpokenForm.CARDINAL)[0].text
'dua'
>>> [tag_numbers(text, "id")[0].spoken()[0].text for text in ("setengah", "tiga perempat")]
['setengah', 'tiga perempat']
```

## revision

```text
revision(lang: str) -> str
```

`revision` returns the revision of the lexicon that `lang` reads: the sha256, as 64 hex digits, of the canonical bytes of that lexicon after its base lexicon is merged in. `lang` works as in `tag_numbers`, and a language with no lexicon raises `UnsupportedLanguageError`. The revision changes when any word, setting or source of the lexicon or of its base changes. A package that records which rules it ran with adds the revision of each lexicon it read to its own. Read [lexicon-format.md](lexicon-format.md).

```python
>>> from numtag import revision
>>> len(revision("pt")), revision("pt") == revision("pt-PT"), revision("pt") == revision("pt-BR")
(64, True, False)
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
