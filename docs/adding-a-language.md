# Adding a language

A language in numtag is one JSON lexicon file, a gold corpus of real sentences, and tests. The grammar engine is shared. This guide gives the lexicon format, the source rule, the gold format and the gates that a new language must pass.

## Find the sources first

Every word and every setting needs a source that you have read. Use the sources in this order of trust:

1. A national dictionary or grammar of the language.
2. The CLDR RBNF spellout rules, which list the number words of each language.
3. Wiktionary.

ovos-number-parser (`numbers_<lang>.py` and its tests) and the number modules of chronologia are leads and test harnesses, not authorities. They have known bugs. A rule from them needs an outside source too.

## The lexicon file

The file is `numtag/lexicon/<lang>.json`. The file name is the lexicon name: `tag_numbers` reads the primary subtag of a language tag ("de" for "de-AT") and loads `<primary>.json`. A region with a file of its own loads that file: `pt-BR` loads `pt-BR.json` and `fr-BE` loads `fr-BE.json`. `BASE_LEXICON` in `numtag/tagger.py` names the file for every other tag of a language with regional files: `pt` loads `pt-PT.json` and `fr` loads `fr-FR.json`. It also maps `no` to `nb.json`. A new language with regional files needs an entry there.

The file is a JSON object with these keys:

| Key | Content |
|---|---|
| `extends` | Optional. The name of a base lexicon. The file then holds only what differs from the base. |
| `settings` | An object. Each key is a setting, and each value is an object with `value` and `source`. |
| `words` | An object. Each key is a word list, and each value is an object with `value` (a list of words) and `source`. |
| `entries` | A list of word entries. Each entry has `word`, `role` and `source`, and more keys by role. |

A file with `extends` takes every setting, word list and entry of its base. Its own settings and word lists replace those of the base. Its own entry replaces the base entry with the same word and role. `pt-BR.json` is a full example: it extends `pt-PT` and changes two settings.

The loader reads every setting and every word list below. A file that leaves one out raises `KeyError` when it loads. The `scale` setting is read only when the call passes no `scale`, so load a new file with no `scale` argument as well as in both scales. An empty list is a valid value, and it needs a source too.

### Settings

| Setting | Type | Meaning |
|---|---|---|
| `scale` | `"long"` or `"short"` | The default scale of the language |
| `group_mark` | string | The mark that groups digits: "." in pt, "," in en |
| `decimal_mark` | string | The mark before the decimals: "," in pt, "." in en |
| `space_groups` | bool | A single space groups digits ("1 000 000") |
| `plural_scale_needs_count` | bool | A plural scale word with no count is no number ("milhões de pessoas") |
| `scale_noun_agrees` | bool | A singular scale noun takes only the count one ("um milhão", not "cem mil e um milhão") |
| `joiner_tens_units` | `"required"`, `"optional"` or `"never"` | The joiner between tens and units ("vinte e um", "twenty-one") |
| `joiner_after_hundred` | the same | The joiner after the hundreds ("cento e vinte", "one hundred and twenty") |
| `joiner_between_groups` | the same | The joiner between two classes ("mil e duzentos") |
| `joiner_before_last_group` | the same | The joiner before a last group below a hundred or a round hundred. Where it is required, "mil duzentos" is two numbers. |
| `joiner_before_round_hundred` | bool | A round hundred may follow the joiner after a thousand, so "mil e quinhentos" counts a larger scale noun |
| `comma_between_classes` | bool | A comma after a scale word may link two classes of one number |
| `ordinal_style` | `"every_word"` or `"last_word"` | Every word of an ordinal is ordinal ("vigésimo primeiro"), or only the last ("twenty-first") |

Two optional settings tune Roman numerals. `roman_pronoun_letters` (default false) is true where "I" is a pronoun: a series noun before a single letter then counts only in title case ("Part I", not "the part I like"). `roman_title_case_cue` (default true) is false where every noun is in title case, as in German: a title-case word before a numeral is then no cue.

### Word lists

| List | Content | pt | en |
|---|---|---|---|
| `joiner` | The word that joins parts of a number | "e" | "and" |
| `decimal_marker` | The words that start the fraction part | "vírgula", "ponto" | "point" |
| `minus` | The words that make a number negative | "menos" | "minus", "negative" |
| `minus_idioms` | Phrases where a minus word is no sign | "pelo menos" | empty |
| `percent_phrase` | Phrases whose last word is the percent sign after a number | empty | empty |
| `negative_particle` | Particles after which the word for one means "not a single" and counts nothing (ru "ни одного") | empty | empty |
| `number_noun` | Nouns that name a number, so the article word after them is the number ("o número um") | "número" | empty |
| `number_name` | Names and set phrases that start with a number word and hold no number (fa "سه شنبه", Tuesday; ru "одно и то же", the same) | empty | empty |
| `article_one` | Articles that also mean one | "um", "uma" | "a", "an" |
| `of` | The word after which a plural noun multiplies a scale noun | "de" | empty |
| `fraction_of` | The word between a fraction and a collective | "de" | "of" |
| `denominator_particle` | A particle after a denominator | "avos" | empty |
| `class_noun` | A singular noun that names a class after a collective | "milhar" | empty |
| `half_unit` | Units of measure that a half before them halves | "quilo", "hora" | empty |
| `abbreviation` | Number words that a period makes an abbreviation | "dez" | empty |
| `lone_decimal_mark` | Marks that make the digits after them decimals at the start of a number | ",", "." | "." |
| `range_cue` | The word that opens a range | "entre" | "between" |
| `roman_series_noun` | Nouns that mark a place in a series, so a Roman numeral beside them is an ordinal | "século", "capítulo" | "century", "war" |
| `roman_title` | Regnal titles, before the name that a numeral follows | "rei", "d" | "king", "pope" |
| `roman_word` | Roman numerals that are also a word or a common abbreviation | "cd", "cv" | "cd", "mix" |
| `roman_lower_word` | Roman numerals that are a word only in lower case, so the upper-case numeral reads as usual | "vi" | empty |

### Entries

Each entry has a `word`, a `role` and a `source`. The role decides the other keys.

| Role | `value` | Example |
|---|---|---|
| `unit`, `ten`, `hundred` | the digit string of the word | "dois" is "2", "vinte" is "20", "cem" is "100" |
| `collective` | the digit string of the group | "dúzia" is "12" |
| `denominator` | the digit string of the denominator | "terço" is "3" |
| `ordinal` | the digit string of the position | "primeiro" is "1" |
| `hundred_multiplier`, `scale_numeral`, `scale_noun` | a power of ten, as an integer | "mil" is 3 |
| `scale_noun` of the -illion series | no `value`. `rank` gives the place in the series | "milhão" is rank 1, "bilião" rank 2 |
| `ordinal_scale` | the cardinal scale word that it names | "milésimo" names "mil" |
| `half` | none | "meio" |
| `ordinal_suffix` | none | "º", "st" |
| `vague_quantifier` | none | "nekoliko" |

A `vague_quantifier` entry is the one list per language of words that state an amount with no exact number, such as "nekoliko" or "several". It may carry `"ambiguous": true` where the word is also an ordinary noun or adverb. A scale word or collective right after such a word reads no number, so "nekoliko milijuna ljudi" holds no number. A word in between ends the effect.

These optional keys hold facts that the word form shows:

| Key | Meaning |
|---|---|
| `gender` | `"masculine"` or `"feminine"` |
| `plural` | `true` for a plural form ("dúzias", "milhões") |
| `ambiguous` | `true` when the word has a common meaning that is not a number. A number that rests on the word gets the confidence 0.4. |
| `weak_at_end` | `true` when the word has another meaning at the end of a clause, or before a joiner: fr "neuf" ("un manteau neuf"). The word gets the confidence 0.4 there. When the word is the whole text, it gets the full score. |
| `joined_count` | with `weak_at_end`: `true` when a joiner that digits or a cardinal word follow does not end the clause. hu "hat és hét" lists two numbers. fr "neuf" leaves it out, because an adjective also goes before "et deux chapeaux". An article, an ordinal or a word in `ambiguous_forms` after the joiner is no number here. |
| `weak_after`, `weak_before` | `weak_after` lists the words that come right before the word when it has another meaning, and `weak_before` the words that come right after it. hu "hat" has "nem" in `weak_after` ("nem hat") and "rám", "rá", "rájuk" in `weak_before` ("hat rám"). |
| `weak_forms` | the inflected forms that the three keys above apply to. Without it, they apply to every form. hu "hat" lists only "hat", so "hatkor" stays sure. |
| `number_after` | the words after which an `ambiguous` or weak word has only its number reading. hu "hat" lists request verbs ("kérek hat", "legyen hat"). Catalan "nou" ("new") lists "els" and "les": the adjective there is "nous" or "noves", so "a les nou" is nine o'clock. |
| `addend` | `true` when a cardinal may follow the collective after the joiner ("four score and seven") |
| `bound` | `true` for a form that stands only before the rest of the number ("cento" in "cento e um") |

A scale noun with a `rank` gets its power of ten from the scale: 10^(3 × rank + 3) in the short scale, 10^(6 × rank) in the long scale. A mention with such a word states its `number_scale`.

Two entries from `pt-PT.json`:

```json
{"word": "mil", "role": "scale_numeral", "value": 3, "source": "Priberam, \"mil\": \"quantificador numeral cardinal\", \"Dez vezes cem.\"; Squarisi, Correio Braziliense: \"O numeral mil, por não ser substantivo, recebe tratamento diferente\". Priberam, \"mil\": \"ele tem mil e uma artimanhas\": the whole cardinal counts the noun after it."}
```

```json
{"word": "dúzia", "role": "collective", "value": "12", "source": "Priberam, \"dezena\": \"Grupo de dez.\"; \"dúzia\": \"Conjunto de doze.\"; \"centena\": \"Conjunto de 100 elementos.\"."}
```

A setting from `en.json`:

```json
{"range_cue": {"value": ["between"], "source": "Wiktionary, \"between\", sense 1: \"In the position or interval that separates (two things), or intermediate in quantity or degree\", as in \"somewhere between forty and fifty dollars\". The \"and\" joins the two limits, so it ends the first number where the words split into two numbers, the first smaller."}}
```

## The source rule

Every `source` field quotes, word for word, a page that you opened and read. Name the work and the entry or page, then give the quote in double quotes. A short note after the quote may say what follows from it.

A quote written from memory is not a source. A paraphrase is not a quote. When no outside source decides a rule, the field says so with the words "structural, no external source", and states the reason. A decision by the project maintainer is a "maintainer ruling", and the field quotes the ruling.

Before a lexicon merges, the reviewer checks every source field against the cited pages. The repository holds no tool for this check: a language port runs it from its own audit tooling. The reviewer saves a copy of each page and looks for each quoted piece of four characters or more on it, after normalising case, white space and quote marks. A field passes when every quote is on its page. The review reports the count of fields in and the count held.

## Gold rows

The gold corpus is `tests/gold/<lang>.jsonl`, one JSON object per line. [tests/gold/README.md](../tests/gold/README.md) gives the full format.

```json
{"text": "comprou duas dúzias de ovos", "mentions": [{"start": 8, "end": 19, "value": "24", "kind": "cardinal"}], "source": "Priberam, \"dúzia\", sense 1: \"Conjunto de doze.\""}
```

This row is line 191 of `tests/gold/pt-PT.jsonl`. A gold row is a real, natural sentence of the language, with a source. Each value comes from hand arithmetic or a quoted source, never from a run of numtag or ovos-number-parser. Each rule of the language has gold rows that show it in real sentences. A bare phrase in a unit test does not count as the test of a rule.

A new language needs at least 150 rows. Cover the cardinals 0 to 20, the tens, the hundreds, the thousands, the millions and the scale of the language. Also cover the ordinals, and the fractions and decimals that the language writes in words. Add digits with the marks of the language and two numbers in one sentence. Add a number word that is also an article or a noun.

Check the format of each file. The checker prints the rows in and the rows out, and the two counts must be equal.

```bash
python tests/gold/check_gold.py
```

```text
en.jsonl: 420 in, 420 out
pt-BR.jsonl: 456 in, 456 out
pt-PT.jsonl: 458 in, 458 out
```

Add the decimal marks of the language to `DECIMAL_MARKS` in `tests/gold/check_gold.py`, so that the checker can tell a decimal from a fraction.

## The gates

A new language passes these gates before it merges.

| Gate | Pass condition |
|---|---|
| Lexicon load | `tests/test_lexicon.py` lists the new file, and the file loads in both scales. Every entry and setting has a source. |
| Gold score | The language has a floor in `tests/gold_floor.json`, and `tests/test_gold.py` reaches it. The missed rows go to `tests/.gold-report/<lang>.txt`. |
| Other languages | The gold scores and grammar tests of every other language do not change. |
| Grammar tests | Each hard rule of the language has a test. Each test fails before the change and passes after it. |
| Mutation | For each new engine mechanism, one mutation of the engine makes the tests fail. Run it with `PYTHONDONTWRITEBYTECODE=1`, and run a control without the mutation. |
| Quote check | The reviewer finds every quote of every source field on a saved copy of the cited page. |
| Docs | `tests/test_docs.py` passes. |

## Engine features

Some languages need an engine feature that Portuguese and English do not use. Examples are inverted tens ("einundzwanzig"), vigesimal counting ("quatre-vingts"), compound words ("kaksikymmentä"), case forms, a script other than Latin, or native digits. Add the feature to the engine as a general mechanism. A lexicon setting switches it on, and the default is off. The outputs of the languages that do not set it must not change.

---
[← English](languages/en.md) · [Home](index.md) · [Design →](design.md)
