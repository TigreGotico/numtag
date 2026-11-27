# The lexicon format

<!-- agent-hint
covers: The format of a lexicon JSON file, versions 1, 2 and 3: every key with its type, its default and what the engine does with it, and the version, schema and revision rules.
source: numtag/lexicon/__init__.py:load, numtag/lexicon/__init__.py:revision, numtag/lexicon.schema.json, tests/test_lexicon_format.py
generated: no
verify: for k in $(grep -oP '^ +"\K[a-z_]+(?=": \{"properties")' numtag/lexicon.schema.json); do grep -qF "$k" docs/lexicon-format.md || exit 1; done
see: adding-a-language.md, design.md
-->

A lexicon is one JSON file that holds the words and the settings of one language. This page defines the formats of versions 1, 2 and 3 for a person who writes a second interpreter of it, in another language or on another runtime. It gives every key with its type, its default and what the engine does with it. The file `numtag/lexicon.schema.json` holds the same keys as a JSON Schema. [adding-a-language.md](adding-a-language.md) tells how to write a lexicon and where its sources come from.

The engine has no code for a language. A language that needs new behaviour gets a new key or a new role here, and the format version goes up in the same change.

## The file

A file is a JSON object with these keys.

| Key | Content |
|---|---|
| `format_version` | The integer `1`, `2` or `3`. Required. Only versions 2 and 3 hold `writer`. Only version 3 holds the keys that this page marks as version 3. |
| `extends` | The name of a base lexicon. Optional. |
| `settings` | An object. Each key is a setting, and each value is `{"value": ..., "source": ...}`. |
| `words` | An object. Each key is a word list, and each value is `{"value": [...], "source": ...}`. |
| `inflection` | An object. Each key is the name of a class of suffixes. Optional. |
| `entries` | A list of word entries. |
| `writer` | An object that tells how to write a number as words. Optional. Version 2 only. Read [The writer block](#the-writer-block). |

A file with no `extends` holds `settings`, `words` and `entries`. It holds every setting and word list that this page marks as required. A file with `extends` holds only what differs from its base. It gets the `writer` block of its base, merged key by key with its own. A `writer` of `null` drops the writer of the base, for a lexicon that its base writer does not speak.

### Version and refusal

The loader reads `format_version` first. It reads versions 1, 2 and 3. It refuses a file with another version, or with none, and the error names the lexicon and the version. It also refuses a key that it does not read, and the error names the key and the place: the lexicon, a section, a setting, a word list, an inflection class or an entry. An entry holds only the keys that the loader reads for its role, so a key of another role is refused too.

A change to this format that adds a key, a role or a value, or that changes what a key does, raises the version, changes this page and changes the schema in the same commit. A file stays at version 1 until it gets a `writer` block, and then it moves to version 2, so the revision of a lexicon with no writer never changes. A file that holds a key of version 3 moves to version 3. The loader refuses a `writer` block in a version 1 file, and a key of version 3 in a version 1 or 2 file. The error names the key and the place.

Version 3 adds the settings `roman_ordinal_suffix` and `group_mark_forms` and the entry keys `after` and `cased` of the role `ordinal_suffix`. These are all the changes of version 3; a file that holds none of them reads the same under version 2.

### Base lexicons

The loader reads the base first, then the file. A setting or a word list of the file replaces the one of the base. An inflection class of the file replaces the class with the same name. An entry replaces the entry of the base with the same `word` and `role`, and an entry with no match goes at the end of the list. The base can have a base of its own. The loader checks the version and the keys of each file on its own.

### Revision

`numtag.revision(lang)` returns the revision of the lexicon that a language tag reads: the sha256, as 64 lower-case hex digits, of the document that the loader reads. The document is the file, or, for a file with `extends`, the merged document with the keys `format_version`, `settings`, `words`, `inflection`, `entries` and, when a file of the chain has one, `writer`. The merged `format_version` is the highest version of the chain. It is written as canonical JSON: sorted keys, `,` and `:` with no spaces, non-ASCII characters as UTF-8. The revision changes when any word, setting or source changes, and when the base of the lexicon changes. A consumer that records which rules it ran with adds the revision to its own.

## Settings

A setting holds a `value` and a `source`. A setting with no default is required in a file with no `extends`. A setting with a default may be left out, and the engine then uses the default.

| Setting | Type | Default | What the engine does | Example |
|---|---|---|---|---|
| `article_after_noun` | boolean | `false` | The article follows its noun ("etxe bat"), so it is weak after a word. | eu: `true` |
| `bare_hundred_after_scale` | boolean | `false` | A hundred word after a group of a hundred or more starts the next group ("tusind hundrede" is 1100). | de: `true` |
| `bare_noun_counts_one` | boolean | `false` | A singular collective or fraction noun alone counts one ("дюжина яиц"). | tr: `true` |
| `bidi_controls` | boolean | `false` | Directional marks and embedding controls read as spaces. | ar: `true` |
| `clitic_min_rest` | integer | `1` | The fewest letters that a word keeps after a prefix of `clitic_prefix` comes off. | ar: `3` |
| `clock_half` | boolean | `false` | A half right before a number names the half hour before that hour ("halb drei" is 2:30), so the half is no number of its own. | de: `true` |
| `comma_between_classes` | boolean | required | A comma after a scale word may link two classes of one number ("dois milhões, duzentos e trinta e seis mil"). | pt-PT: `true` |
| `compound_parts_by_role` | boolean | `false` | A compound splits only into words with a role inside a cardinal or an ordinal, and the joiners ("petin\|dvajset" is no split). | ru: `true` |
| `compound_shared_letter` | boolean | `false` | Two parts of a compound share a doubled letter ("ettusen" is "ett" and "tusen"). | sv: `true` |
| `compound_words` | boolean | `false` | Number words are written together as one word ("zweihundert", "kaksikymmentäviisi"). The tokenizer splits such a word into the chain of number words it is made of. | de: `true` |
| `decimal_fraction` | boolean | `false` | After a decimal marker, a numerator and a power-of-ten denominator give the decimals ("öt egész két tized" is 5.2). | hu: `true` |
| `decimal_fractions` | boolean | `false` | After a decimal marker, a fraction whose denominator is a power of ten gives the decimals ("две целых пять десятых"). | ru: `true` |
| `decimal_mark` | string | required | The mark before the decimals of a digit string. | pt-PT: `","` |
| `dot_ordinal` | boolean | `false` | A period right after a digit string makes it an ordinal when a lower-case word or a digit follows ("a 2. emelet"). | fi: `true` |
| `dotted_i` | boolean | `false` | The letters I and İ are two letters with the lower-case forms ı and i. | tr: `true` |
| `fold_marks` | `true` or `false` or `"unmarked"` | `false` | Combining marks belong to the word they follow and are ignored on lookup. `"unmarked"`: only a word written with no mark at all is read without marks (el "εκτός" stays apart from "έκτος"). | ar: `true` |
| `fraction_after_scale` | boolean | `false` | A fraction word after a scale word takes a part of it ("milioi erdi bat" is 500000, "hiru milioi laurden" 750000). | eu: `true` |
| `fraction_agreement` | boolean | `true` | A denominator after a numerator above one takes its plural form ("dois terços"). `false` where it keeps one form ("két harmad"). | hu: `false` |
| `fraction_of_scale` | boolean | `false` | A fraction before "de" and a scale noun takes that part of it ("um quarto de milhão" is 250000). | pt-PT: `true` |
| `glued_denominator_alone` | boolean | `false` | With `glued_denominators`: the glued part word with no number before it is one part of the product ("háromszázad" is 1/300). `false` where it names no number. | de: `true` |
| `glued_denominator_alone_ambiguous` | boolean | `false` | With `glued_denominator_alone`: the lone reading has a second meaning, the count of parts, and has the confidence of a homograph. | de: `true` |
| `glued_denominators` | boolean | `false` | A count glued to the part word of a hundred or more multiplies it, as it multiplies the scale word ("kétszázad" is 1/200, as "kétszáz" is 200). | de: `true` |
| `group_mark_forms` | string | `""` | Version 3. Other characters that group digits as `group_mark` does, and read as it ("1’234" is "1'234"). | fr-CH: `"’"` |
| `group_mark` | string | required | The mark that groups the digits of a digit string. A mark other than "." or "," also stands between digits. It joins digits only before a group of exactly three: "9'58" is 9 and 58. | pt-PT: `"."` |
| `half_of_scale` | boolean | `false` | A half after any scale word is half of that scale ("אלף וחצי" is 1500). | ar: `true` |
| `hundred_counts_below_thousand` | boolean | `false` | A hundred multiplier takes no count of a thousand or more ("dvou tisíc sta" is 2100). | ru: `true` |
| `inflection_position` | `"every"` or `"last"` | `"every"` | Where a suffix of an `inflection` class closes the number. `every`: on any word of a number. `last`: only on the last word, so a form with a suffix ends the number. | hu: `"last"` |
| `inverted_tens` | `null` or `"required"` or `"optional"` or `"never"` | none | A unit, then the joiner as this policy says, then a round ten, all parts of one compound word ("petindvajset", "pětadvacet"). `null` reads no such compound. | cs: `"optional"` |
| `joiner_after_decimal_marker` | `"required"` or `"optional"` or `"never"` | `"never"` | Where the joiner may stand after a decimal marker ("две цяло и пет"). | ru: `"optional"` |
| `joiner_after_hundred` | `"required"` or `"optional"` or `"never"` | required | The same, after the hundreds ("cento e vinte", "one hundred and twenty"). | pt-PT: `"required"` |
| `joiner_before_half` | `"required"` or `"optional"` or `"never"` | `"required"` | Where the joiner may stand before a half or a fraction after a whole ("dua setengah", "two and a half"). | id: `"never"` |
| `joiner_before_last_group` | `"required"` or `"optional"` or `"never"` | required | The same, before a last group below a hundred or a round hundred. Where it is `required`, "mil duzentos" is two numbers. | pt-PT: `"required"` |
| `joiner_before_round_hundred` | boolean | required | A round hundred may follow the joiner after a thousand, so "mil e quinhentos" counts a larger scale noun. | pt-PT: `true` |
| `joiner_between_groups` | `"required"` or `"optional"` or `"never"` | required | The same, between two classes of one number ("mil e duzentos"). | pt-PT: `"optional"` |
| `joiner_tens_units` | `"required"` or `"optional"` or `"never"` | required | Where the joiner word stands between a ten and a unit ("vinte e um", "twenty-one"). `required`, `optional` or `never`. | pt-PT: `"required"` |
| `joiner_thousand_hundreds` | boolean | `false` | With `joiner_thousand_one_only`: the joiner also stands between the thousands and a group of hundreds ("mil y quinientos"), except after a range cue, where it joins the two limits. | es: `true` |
| `joiner_thousand_one_only` | boolean | `false` | The joiner between two groups stands only between a thousand and a one ("mil y una"). Before any other group the parts are two numbers. | es: `true` |
| `joiner_unit_ten` | `"required"` or `"optional"` or `"never"` | `"required"` | The joiner between a unit and the ten after it ("und" in "einundzwanzig"). | de: `"required"` |
| `kept_marks` | string | `""` | Marks that are part of a letter and stay when `fold_marks` removes the others (the hamza of ar "أ"). | ar: `"ٕٓٔ"` |
| `letter_folds` | object | `{}` | Letters that read as another letter on lookup. Each key is replaced by its value (fa "ي" as "ی"). | ar: `{"ى": "ي", "ة": "ه", "ـ": "", "ٱ": "ا"}` |
| `native_digits` | object or null | none | The digits and digit marks of the script. `digits` lists runs of ten digits, from zero up, each read as the ASCII digit. `decimal_mark` and `group_mark` are the native marks, read as the `decimal_mark` and `group_mark` settings. `null` reads ASCII digits only. | ar: `{"digits": ["٠١٢٣٤٥٦٧٨٩", "۰۱۲۳۴۵۶۷۸۹"], "decimal_mark": "٫", "group_mark": "٬"}` |
| `one_before_ordinal_scale_is_fraction` | boolean | `true` | A count of one before an ordinal scale word makes a fraction ("um milésimo"). | de: `false` |
| `ordinal_form_part_takes_no_digits` | boolean | `false` | A plural part word that is also a plural ordinal form takes no count in digits: "3 пятых класса" is three fifth-grade classes. A fraction in digits is written "3/5". | ru: `true` |
| `ordinal_joiner_by_place` | boolean | `false` | The joiner before an ordinal word stands where it stands before the cardinal word in that place, and none stands before a scale ordinal: "tjue og tredje" is 20 and 3rd, "hundre og femte" is 105th. | de: `true` |
| `ordinal_style` | `"every_word"` or `"first_word"` or `"last_word"` or `"tail_words"` | required | Which words of a multi-word ordinal are ordinal. `every_word`: each ("vigésimo primeiro"). `last_word`: only the last ("twenty-first"). `first_word`: the first ordinal unit, then a teen word or the joiner and a cardinal ten (ar "الحادي عشر"). `tail_words`: every word after the cardinal part (cs "dva tisíce dvacátý třetí"). | pt-PT: `"every_word"` |
| `ordinal_suffix_marks` | list of strings | `["", "."]` | The marks that may stand between digits and an ordinal suffix ("." in "1.º"). The marks of `ordinal_suffix_mark` join this list. | nl, fr-FR: `[""]` |
| `part_after_joiner_needs_article` | boolean | `false` | A part word after the joiner takes an article: "six and a quarter", never "six and quarter". "forty and eighth" is 40 and 8th. | en: `true` |
| `part_glued_to_whole` | boolean | `false` | A fraction below one, with its own count, glued to the whole number before it adds to it ("zweieinviertel" is 2.25). | de: `true` |
| `percent_phrase_is_no_number` | boolean | `false` | A percent phrase names the percent sign with no number before it too: "tanto por ciento" holds no 100. | es: `true` |
| `period_ordinal_free_digits` | integer | `0` | With `period_ordinals`: a number of at most this many digits needs no cue ("3. Platz"). | de: `3` |
| `period_ordinal_lowercase` | boolean | `false` | With `period_ordinals`: a lower-case word after the period is a cue ("17. mai"). | da: `true` |
| `period_ordinals` | boolean | `false` | A period after digits makes an ordinal ("am 3. Mai") when a cue shows it: a word of `period_ordinal_before` before the digits, with `period_ordinal_lowercase` any lower-case word after the period, or a number of at most `period_ordinal_free_digits` digits. | de: `true` |
| `plural_scale_needs_count` | boolean | required | A plural scale word with no count names no number ("milhões de pessoas"). | pt-PT: `true` |
| `point_decimal` | boolean | `false` | An hour and minutes written with a point are a decimal unless a clock word stands beside them. Elsewhere only an hour of "0" is one. | es: `true` |
| `roman_ordinal_suffix` | boolean | `false` | Version 3. An ordinal suffix of the language in lower case, glued to an upper-case Roman numeral, makes the word one ordinal ("XIXe", "Ier"). The suffix keeps its `after` and `cased` limits, a single letter is I, V or X, and a numeral in `roman_word` takes no suffix ("MMe"). A single-letter numeral with a suffix is sure only with a cue: a series noun before or after it, a title-case name before it or a regnal title and a name. With no cue it has the confidence of a homograph ("Ire"). A whole word in `roman_word` ("Xe") reads only with a series noun or a regnal cue. | fr-FR: `true` |
| `roman_pronoun_letters` | boolean | `false` | "I" is a pronoun. A series noun before a single letter or a numeral that is also a word then counts only in title case ("Part I", not "the part I like"). | en: `true` |
| `roman_title_case_cue` | boolean | `true` | A title-case word before a Roman numeral below 100 is a cue ("Luís XIV"). A numeral of 100 or more after it is no ordinal ("Total MDCC"). `false` where every noun is in title case ("Größe XIV"). | de: `false` |
| `scale` | `"long"` or `"short"` | required | The scale of a scale word when the call names none: `short` makes a billion 10^9, `long` makes it 10^12. A call's `scale` argument overrides it. | pt-PT: `"long"` |
| `scale_noun_agrees` | boolean | required | A singular scale noun takes only the count one ("um milhão", never "cem mil e um milhão"). | pt-PT: `true` |
| `small_multiplier_starts_group` | boolean | `false` | A hundred or ten multiplier after a group of thousands starts the next group and counts no group ("bin yüz" is 1100, not 100000). | fi: `true` |
| `space_groups` | boolean | required | A single space also groups the digits of a digit string ("1 000 000"). | pt-PT: `true` |
| `ten_joins_unit_ordinal` | boolean | `true` | A unit ordinal after "ten" adds to it ("ten fifth" is 15th). Where the teen ordinals are words of their own, it does not ("zehn dritte"). | en: `false` |
| `tens_order` | `"ten_unit"` or `"unit_ten"` or `"both"` | `"ten_unit"` | The order of a ten and a unit: `ten_unit` ("twenty-one"), `unit_ten` ("einundzwanzig") or `both` (nb "tjueen" and "enogtjue"). | de: `"unit_ten"` |
| `unit_ten_one_word` | boolean | `false` | A unit before the ten is one written word with it: "zwei und vierzig" is two numbers. | de: `true` |
| `word_chars` | string | `""` | Characters that stand inside a word and are dropped on lookup (the zero-width non-joiner of fa). | fa: `"‌"` |

The `joiner_*` settings and `inverted_tens` take `required`, `optional` or `never`. `required` means the joiner word must stand there, `optional` that it may, and `never` that it may not.

## Word lists

A word list holds a `value`, a list of strings, and a `source`. Every list may be empty, and an empty list still needs a source. A list with a default may be left out, and the default is the empty list. The engine folds each word as the `fold_marks`, `kept_marks`, `letter_folds` and `word_chars` settings say, and it looks words up in that folded form. A phrase of several words is one string with spaces.

| List | Required | What the engine does | Example |
|---|---|---|---|
| `abbreviation` | yes | Number words that a period makes an abbreviation ("3 dez. 2025"). | pt-PT: `["dez"]` |
| `and_a_half` | no | A word that adds a half to the number before it ("einhalb" in "zweieinhalb"). | de: `["einhalb"]` |
| `article_needs_noun` | no | An article that alone at the end of a clause is no numeral ("Er lud mich ein."). | de: `["ein", "eines"]` |
| `article_one` | yes | Articles that also mean one ("um", "a"). | pt-PT: `["um", "uma"]` |
| `class_noun` | yes | A singular noun that names a class after a collective ("milhar"). | pt-PT: `["milhar"]` |
| `clitic_prefix` | no | A prefix glued to a number word that is no part of the number: an article or a preposition (ar "ال" in "الثالث"). | ar: `["ال", "بال", "لل"]` |
| `clock_abbreviation` | no | A clock word that is an abbreviation, so its period joins it to the digits after it ("kl. 14.30"). It is also a `clock_before` word. | fi: `["klo"]` |
| `clock_after` | no | A word after an hour and minutes written with a point, with the same effect ("14.30 Uhr"). | pt-PT: `["h"]` |
| `clock_before` | no | A word before an hour and minutes written with a point, which then read as a time and no number ("um 14.30"). | pt-PT: `["às", "à"]` |
| `count_of` | no | A word between a count and its scale word ("de" in "douăzeci de mii"). | ro: `["de"]` |
| `date_month` | no | Month names before which the period after digits ends the year of a date ("2008. február"). | hu: `["január", "február", "március"]` |
| `decimal_marker` | yes | The words that start the fraction part ("vírgula", "point"). | pt-PT: `["vírgula", "virgula"]` |
| `denominator_particle` | yes | A particle after a denominator (pt "avos"). | pt-PT: `["avos"]` |
| `digit_suffix_mark` | no | Marks that glue a case ending to a digit string ("5-öt", "5'te"). | fi: `[":"]` |
| `fraction_of` | yes | The word between a fraction and a collective ("de", "of"). | pt-PT: `["de"]` |
| `fraction_over` | no | A word between a numerator and a denominator cardinal, as "a/b" is read aloud (eu "zati"). | eu: `["zati"]` |
| `half_unit` | yes | Units of measure that a half before them halves ("meio quilo"). | pt-PT: `["quilo", "quilograma", "grama"]` |
| `joiner` | yes | The word that joins parts of a number ("e", "and"). | pt-PT: `["e"]` |
| `joiner_prefix` | no | A prefix glued to a number word that is the joiner (ar "و" in "وعشرون"). | ar: `["و"]` |
| `lone_decimal_mark` | yes | Marks that make the digits after them decimals at the start of a number (".5"). | pt-PT: `[",", "."]` |
| `minus` | yes | The words that make a number negative. | pt-PT: `["menos"]` |
| `minus_idioms` | yes | Phrases where a minus word is no sign ("pelo menos"). | pt-PT: `["pelo menos", "ao menos", "mais ou menos"]` |
| `negative_particle` | no | Particles after which the word for one means "not a single" and counts nothing (ru "ни одного"). | ru: `["ни"]` |
| `noun_after_count` | no | A number word that, right after a sure cardinal, is the noun that the cardinal counts (hu "öt hét"). | hu: `["hét"]` |
| `number_name` | no | Names that start with a number word and hold no number (fa Tuesday). | de: `["ein paar"]` |
| `number_noun` | no | Nouns that name a number, so the article word after them is the number ("o número um"). | pt-PT: `["número", "numero"]` |
| `of` | yes | The word after which a plural noun multiplies a scale noun ("de"). | pt-PT: `["de"]` |
| `one_after_noun` | no | A word after a noun that counts one of it (eu "bat" in "milioi bat"). | eu: `["bat"]` |
| `ordinal_article` | no | The word before an ordinal that needs an article (ro "a" in "a noua"). | en: `["the"]` |
| `ordinal_particle` | no | A word that makes the cardinal after it an ordinal ("wis sin"). | kab: `["wis", "tis", "wiss"]` |
| `ordinal_suffix_mark` | no | Marks that may stand between digits and an ordinal suffix. They join the `ordinal_suffix_marks` setting. | ru: `["-"]` |
| `part_noun` | no | A noun that makes the ordinal before it a fraction ("a décima parte"). | pt-PT: `["parte", "partes"]` |
| `partitive` | no | A word after an article and a word that is both a denominator and an ordinal that keeps the fraction ("um quinto do bolo"). Any other word there makes the ordinal. An empty list always reads the fraction. | pt-PT: `["de", "do", "da"]` |
| `percent_before` | no | Percent words that stand before the number (tr "yüzde"). The number after one is the amount, with no homograph score. | tr: `["yüzde"]` |
| `percent_phrase` | no | Phrases whose last word is the percent sign after a number ("per cent"). | fr-FR: `["pour cent"]` |
| `period_ordinal_before` | no | A word before digits that makes their period an ordinal mark ("zum 1000. Mal"). | de: `["der", "die", "das"]` |
| `range_cue` | yes | The words that open a range ("entre", "between"). The joiner after one joins the two limits. | pt-PT: `["entre"]` |
| `roman_lower_word` | no | Roman numerals that are a word only in lower case, so the upper-case numeral reads as usual (pt "vi"). | pt-PT: `["vi"]` |
| `roman_series_noun` | no | Nouns that mark a place in a series, so a Roman numeral beside them is an ordinal ("século"). | pt-PT: `["século", "séculos", "capítulo"]` |
| `roman_title` | no | Regnal titles before a name that a numeral follows ("rei"). | pt-PT: `["rei", "rainha", "papa"]` |
| `roman_word` | no | Roman numerals that are also a word or a common abbreviation, which read only after a strong cue ("CD", "MIX"). | pt-PT: `["cd", "cv", "cc"]` |
| `vague_clitic` | no | A clitic that may stand between a vague quantifier and the scale word ("je" in "nekoliko je tisuća"). | hr: `["sam", "si", "je"]` |
| `word_apostrophe` | no | Marks that join letters into one word ("п'ять"). | uk: `["'", "’"]` |

## Inflection classes

A language that inflects its numbers lists classes of suffixes. A class is an object with these keys. An entry names classes in `stems`.

| Key | Type | Default | What the engine does | Example |
|---|---|---|---|---|
| `value` | list of strings | required | The suffixes of the class. `""` is the bare stem. | fi: `["n", "ksi", "ssa"]` |
| `source` | string | required | The quote and the page that give the suffixes. No reading depends on it. | fi |
| `ordinal` | boolean | `false` | The forms that the class makes are ordinal. | tr: class `tr.ü.ord.c` |
| `fraction_case` | boolean | `false` | The forms name the parts of a fraction when a count follows (tr "üçte bir" is one third). | tr: class `tr.ü.loc.kc` |

Each stem of an entry joins each suffix of each class that it names, and each joined form is one more form of the entry. With `inflection_position` set to `last`, a form made with a non-empty suffix closes the number.

## Entries

An entry is an object with `word`, `role` and `source`. The role decides which other keys the loader reads.

| Roles | Value key | Meaning |
|---|---|---|
| `unit`, `ten`, `hundred` | value | A whole number below a thousand: "dois" is "2", "vinte" is "20", "cem" is "100". |
| `teen` | value | Adds ten to the unit before it (fi "yksi" "toista"). |
| `teen_suffix` | value | Adds its value to the unit before it (id "dua belas" is 12). |
| `collective` | value | A group: "dúzia" is "12". |
| `article_collective` | value | A collective that only the article counts (en "a couple", never "one couple"). |
| `denominator` | value or scale_of | A part word: "terço" is "3". |
| `ordinal` | value | The position: "primeiro" is "1". |
| `fraction` | value | A fraction as a string ("3/2"). |
| `decimal_zero` | value | The word for zero after a decimal marker. |
| `value_word` | value | A whole number on its own, also one that is not whole (fi "puolitoista" is 3/2). |
| `unit_and_half` | value | The value and a half (el "δυόμισι"). |
| `rational` | value | A number that is no whole number (ru "полтора" is 3/2). |
| `hundred_multiplier`, `scale_numeral`, `scale_noun`, `ten_multiplier` | value or rank | A power of ten: "mil" is 3. A `ten_multiplier` counts tens (fi "kaksi" "kymmentä"). |
| `ordinal_scale` | value | An ordinal scale word. `value` is the cardinal scale word that it names ("milésimo" names "mil"). |
| `half` | none | The word for a half ("meio"). |
| `ordinal_ending`, `ordinal_prefix`, `denominator_prefix` | none | A piece that makes the cardinal before it an ordinal, the cardinal after it an ordinal, or the cardinal after it a denominator. |
| `ordinal_suffix` | none | A suffix after digits ("º", "st"). It reads only `word`, `role`, `source`, `gender`, `after` and `cased`. |
| `vague_quantifier` | none | A word that states an amount with no exact number ("several"). It reads only `word`, `role`, `source` and `ambiguous`. |

The loader reads an entry that holds `scale_of` after all other entries, because it takes its power of ten from that scale word. It reads `ordinal_scale` entries after all other entries for the same reason.

A scale role holds `value`, the exponent of ten, or `rank`. When both are present, `value` wins.

Every role that makes forms (all but `ordinal_suffix` and `vague_quantifier`) reads `stems`, `excluded_forms`, `ambiguous_forms`, `weak_forms`, `ordinal`, `final`, `gender`, `plural`, `ambiguous` and `part`. The roles that give a value read more keys. The table below names each key, its type, its default and its effect.

| Key | Type | Default | What the engine does | Example |
|---|---|---|---|---|
| `word` | string | required | The surface form. One entry can hold more forms through `stems`. | pt-PT: `{"word": "zero", "role": "unit"}` |
| `role` | string | required | What the word does. The role decides which other keys the loader reads. | pt-PT: `{"word": "zero", "role": "unit"}` |
| `source` | string | required | The quote and the page that give the word. No reading depends on it. | none |
| `value` | string or integer | required for a value role | A digit string for a value role, and a power of ten for a scale role. For `ordinal_scale`, the cardinal scale word that it names. | pt-PT: `{"word": "zero", "role": "unit", "value": "0"}` |
| `rank` | integer | none | On a `scale_noun` of the -illion series: the place in the series. The power of ten is 3 × rank + 3 in the short scale and 6 × rank in the long scale. | pt-PT: `{"word": "milhão", "role": "scale_noun", "rank": 1}` |
| `scale_of` | string | none | On a `denominator`: the scale word whose power of ten is the denominator ("billionth" has `scale_of` "billion"). The entry reads no `value`. It reads the keys that make forms and the facts: `gender`, `plural`, `ambiguous` and `part`. | en: `{"word": "billionth", "role": "denominator", "scale_of": "billion"}` |
| `stems` | object | none | Each key is a stem. Each value lists inflection classes. The stem joins each suffix of its classes into one more form of the entry. | fi: `{"word": "nolla", "role": "unit", "stems": {"nolla": ["fi.weak.a", "fi.essive.a", "fi.illative.a", "fi.partitive.a"]}}` |
| `excluded_forms` | list of strings | none | Forms that `stems` makes and that are no form of the entry. | tr: `{"word": "yüz", "role": "hundred", "excluded_forms": ["yüzde"]}` |
| `ambiguous_forms` | list of strings | none | Forms of the entry that have a common meaning that is no number. They read as `ambiguous`. | fi: `{"word": "nolla", "role": "unit", "ambiguous_forms": ["nollaa"]}` |
| `weak_forms` | list of strings | none | The forms that the keys `weak_at_end`, `joined_count`, `weak_after` and `weak_before` apply to. Without it they apply to every form. | hu: `{"word": "hat", "role": "unit", "weak_forms": ["hat"]}` |
| `gender` | `masculine`, `feminine` or `neuter` | none | The gender that the form shows. | pt-PT: `{"word": "um", "role": "unit", "gender": "masculine"}` |
| `plural` | boolean | `false` | The form is plural ("dúzias", "milhões"). | pt-PT: `{"word": "milhares", "role": "scale_noun", "plural": true}` |
| `ambiguous` | boolean | `false` | The word has a common meaning that is no number. A number that rests on it gets the confidence 0.4. | pt-PT: `{"word": "meio", "role": "half", "ambiguous": true}` |
| `part` | boolean | `false` | The word is read only as a piece of a longer word that the tokenizer splits ("vent" in "ventuno"). | it: `{"word": "tré", "role": "unit", "part": true}` |
| `ordinal` | boolean | `false` | The form names a place in a sequence ("viides"). A number whose last word is ordinal is an ordinal. | fi: `{"word": "nollas", "role": "unit", "ordinal": true}` |
| `final` | boolean | `false` | A case ending or a suffix closes the number ("beşte"): no word of the number follows the form. | hu: `{"word": "első", "role": "unit", "final": true}` |
| `addend` | boolean | `false` | A cardinal may follow the collective after the joiner ("four score and seven"). | en: `{"word": "score", "role": "collective", "addend": true}` |
| `bound` | boolean | `false` | The form stands only before the rest of the number ("cento e um"). | pt-PT: `{"word": "cento", "role": "hundred", "bound": true}` |
| `takes_unit` | boolean | `false` | A ten that takes a unit after it although it is not a round ten from twenty up ("on beş"). | tr: `{"word": "on", "role": "ten", "takes_unit": true}` |
| `takes_units` | list of strings | `[]` | A ten that takes only these units after it, past the joiner: "diez y seis" is 16, and "diez y uno" is no number. | es: `{"word": "diez", "role": "ten", "takes_units": ["6", "7", "8", "9"]}` |
| `case` | list of strings | `[]` | The grammatical cases that the form stands in. A ten with no nominative form takes only a unit that shares a case with it. | ru: `{"word": "один", "role": "unit", "case": ["accusative", "nominative"]}` |
| `ordinal_unit` | boolean | `false` | A teen that also follows the ordinal form of its unit (fi "yhdes" "toista" is 11th). | fi: `{"word": "toista", "role": "teen", "ordinal_unit": true}` |
| `numerator` | string | `""` | A denominator that stands alone as this numerator over it (ar "ربع" is 1/4). | ar: `{"word": "ثلث", "role": "denominator", "numerator": "1"}` |
| `weak_alone` | boolean | `false` | A denominator that also names one part alone, with no count and no article, at the confidence of a homograph (eu "laurden"). | eu: `{"word": "heren", "role": "denominator", "weak_alone": true}` |
| `invariant` | boolean | `false` | A denominator with one form for every numerator (fa "سوم" in "دو سوم"). | fr-FR: `{"word": "tiers", "role": "denominator", "invariant": true}` |
| `cardinal` | string | `""` | On a `denominator`: the cardinal word that it ends in when its last word takes a suffix (eu "hamarren" has "hamar"). | eu: `{"word": "bosten", "role": "denominator", "cardinal": "bost"}` |
| `teens` | boolean | `false` | A ten that takes a number from ten to nineteen after it, as well as a unit ("soixante-dix" is 70). | fr-FR: `{"word": "soixante", "role": "ten", "teens": true}` |
| `after_article` | boolean | `false` | An ordinal read only after an ordinal article ("a noua", not "noua clădire"). | mt: `{"word": "ħames", "role": "ordinal", "after_article": true}` |
| `weak_at_end` | boolean | `false` | A word with a common meaning that ends a phrase, as an adjective after its noun (fr "neuf"). It is weak when no word follows it. | hu: `{"word": "hat", "role": "unit", "weak_at_end": true}` |
| `joined_count` | boolean | `false` | With `weak_at_end`: a joiner that a number follows does not end the clause (hu "hat és hét"). | hu: `{"word": "hat", "role": "unit", "joined_count": true}` |
| `weak_after` | list of strings | `[]` | Words before which the word is weak (hu "nem hat"). | hu: `{"word": "hat", "role": "unit", "weak_after": ["nem"]}` |
| `weak_before` | list of strings | `[]` | Words after which the word is weak (hu "hat rám"). | hu: `{"word": "hat", "role": "unit", "weak_before": ["rám", "rád", "rá", "ránk", "rátok", "rájuk"]}` |
| `standalone` | boolean | `false` | An ordinal that is never the last word of a longer ordinal: fr "premier". Only a hyphen joins it to a number before it. | fr-FR: `{"word": "premier", "role": "ordinal", "standalone": true}` |
| `number_after` | list of strings | `[]` | Words after which the word has only its number reading (ca "les nou" is nine o'clock). | hu: `{"word": "hat", "role": "unit", "number_after": ["kérek", "kérem", "kérünk", "kérjük", "kérj", "legyen", "állíts", "állítsd", "állítsa", "tegyél", "tedd", "tegye"]}` |
| `count` | string | `""` | On a scale word: the count that the form holds. The dual ar "ألفان" is 2 × 10^3. | ar: `{"word": "ألفان", "role": "scale_numeral", "count": "2"}` |
| `after` | list of digit strings | none | Version 3. On an `ordinal_suffix`: the only numbers that the suffix follows. fr "er" lists "1", so "1er" is the 1st and "3er" is 3 and a word. Without it, the suffix follows any number. | fr-FR: `{"word": "er", "role": "ordinal_suffix", "after": ["1"]}` |
| `cased` | boolean | `false` | Version 3. On an `ordinal_suffix`: the suffix reads only in the case that `word` writes. fr "d" reads in "2d" and not in "2D", two dimensions. Without it, the suffix reads in any case ("1ST"). | fr-FR: `{"word": "d", "role": "ordinal_suffix", "after": ["2"], "cased": true}` |
| `counted` | boolean | `false` | A plural multiplier that a count takes, in words or in digits below a thousand (he "מאות"). | ru: `{"word": "сотни", "role": "hundred_multiplier", "counted": true}` |

A role that gives a value (`unit`, `ten`, `hundred`, `collective`, `article_collective`, `denominator`, `ordinal`, `fraction`, `decimal_zero`, `value_word`, `unit_and_half`, `rational`, `teen`, `teen_suffix`) reads `value`, `addend`, `bound`, `takes_unit`, `takes_units`, `case`, `ordinal_unit`, `numerator`, `weak_alone`, `invariant`, `cardinal`, `teens`, `after_article`, `weak_at_end`, `joined_count`, `weak_after`, `weak_before`, `standalone` and `number_after`. A scale role reads `value`, `rank`, `count` and `counted`. `half` reads `bound`. `ordinal_scale` reads `value` and `after_article`. A mark role reads no key besides those that make forms.

## The writer block

A `writer` block makes the lexicon write numbers as words. `numtag.spell` runs it. The block holds rule sets that follow the text syntax of rule-based number formatting in ICU, the form of the CLDR files `common/rbnf/<lang>.xml`, and it says which rule set speaks each form. The rules of a lexicon come from CLDR where CLDR has them and carry a `source`. The CLDR data is under the Unicode License v3 (`LICENSE-CLDR`).

A script writes the writer block of a language, and a test checks that the file holds what the script writes. Do not edit a written block by hand. Change the script and run it: `python scripts/writer_pt.py pt-PT` writes the block into `numtag/lexicon/pt-PT.json`. `python scripts/allow_list.py pt-PT` writes the allow-list entries of the language in `tests/golden/onp-writers-allow.json`. `--check` compares and changes nothing.

| Key | Content |
|---|---|
| `source` | The quote and the file that give the rule sets. Required. |
| `rulesets` | An object. Each key is the name of a rule set, and each value is `{"source": ..., "rules": [...]}`. Required. |
| `forms` | An object. Each key is a form: `cardinal`, `ordinal` or `year`. Required, and it holds `cardinal`. |
| `decimal` | `{"word": ..., "places": ..., "read": ..., "source": ...}`. Required. The word between the whole part and the decimals, and the count of decimals that a reading keeps when the caller names none. `read` is `digits` (the default: one word for each decimal) or `number` (the decimals as one number, after a zero word for each leading zero). A `decimals` argument of `spell` replaces it. |
| `scientific` | `{"times": ..., "source": ...}`. Optional. The words between the mantissa and the exponent: "kali sepuluh pangkat". A lexicon with no `scientific` has no exponent reading. |
| `fraction` | Optional. How a fraction "n/m" reads. See below. |
| `plural` | Optional. A list of `{"category": ..., "mod10": [...], "not_mod100": [...], "source": ...}`: the CLDR plural categories of whole numbers. A number is in the first category whose `mod10` holds its last digit and whose `not_mod100` misses its last two digits. Every other number is `other`. ru: one is `mod10` [1], `not_mod100` [11]. |

### Rules

A rule is an object with `value`, `text`, and optionally `radix` and `source`. The `value` is a base value as a whole number with no leading zero, or `-x` for the rule that reads a negative number. The `text` is the rule text. The loader refuses at once any other key and any other `value`, such as `x.x`, `Inf` or `010`.

The interpreter reads a whole number in a rule set like this. It picks the rule with the largest base value that is not above the number. The divisor is the radix (10 when the rule has none) raised to the largest exponent that keeps the divisor not above the base value. The quotient and the remainder of the number by the divisor fill the slots of the rule text. A rule set holds no rule for a number below its smallest base value, so it has a rule for 0, or the form sets a `minimum` that keeps the number out.

| Text | Meaning |
|---|---|
| `←←` | The quotient, read by the same rule set |
| `←%name←` | The quotient, read by the rule set `name` |
| `→→` | The remainder, read by the same rule set. In a `-x` rule it is the number with no sign |
| `→%name→` | The remainder, read by the rule set `name` |
| `=%name=` | The whole number, read by the rule set `name` |
| `[...]` | Text that stays out when the remainder is 0 |
| `[a\|b]` | `a` when the remainder is not 0, else `b`: "[тысяча →%o→\|тысячный]". This is no part of the ICU syntax |
| `$(cardinal,one{...}few{...}other{...})$` | The word of the plural category of the quotient, or the `other` word when the category has none: "тысяча", "тысячи", "тысяч" |
| any other character | Itself |

The soft hyphen U+00AD is dropped from the words, runs of spaces become one space, and the ends are trimmed. The writer of a lexicon is built on the first `spell` call for it, and it refuses then a rule text that holds any of the characters `$ # < >` outside a `$(cardinal,...)$`, which belong to other parts of the ICU syntax that this version does not read, a quotient or remainder slot that names no `%` rule set, and a call to a rule set that the block lacks. The error names the rule set and the rule. A leading apostrophe is no part of this version and reads as text.

### Forms

A form has `variants`, a list of `{"ruleset": ..., "reason": ..., "source": ...}`. The list is in rank order: the first is the default reading. A `reason` is one of `standard`, `no_conjunction`, `year_pairs`, `plain`, `counting`, `variant_spelling` or `strong`. Two variants with the same words count once. A difference of region or standard is no variant: it is another lexicon.

A form can also hold `gender`, an object from `masculine`, `feminine` or `neuter` to a list of variants, and `case`, an object from a case name to a list of variants or to a `gender` object. A case with a `gender` object needs a gender: a call with no gender, or with a gender that the case does not list, raises `ValueError`. A call that names a gender that the form does not list reads the `variants`. A call that names a case that the form does not list raises `ValueError`, and the message names the cases that the form has. A case takes the place of the gender. A form can hold `scale`, an object from `short` or `long` to a form with the same keys apart from `scale`. A call reads the form of the scale it names, or of the lexicon's `scale` setting when it names none. A form with no entry for that scale reads as itself. The `ordinal` form can hold `minimum`, a digit string: a call for a number below it, for a negative number or for a number with decimals raises `ValueError`. A form or a form of a scale can hold `maximum`, a digit string, for a lexicon with no scale word past that number. An ordinal above it raises `ValueError`. A cardinal above it reads the `scientific` form, or raises `ValueError` when the lexicon has no `scientific` form. The `year` form is optional: a lexicon with no `year` reads the cardinal. The form `digits` of `numtag.spell` uses the cardinal rule set for each digit.

### Decimals, negatives and size

A negative number reads with the `-x` rule of the rule set. A negative ordinal reads the same way when the ordinal rule set has a `-x` rule, and raises `ValueError` when it has none. A `decimal` word of `null` means the language has no decimal word, and a number with decimals raises `ValueError`. Otherwise a number with decimals reads as the whole part, the `decimal` word and one cardinal for each of the first `places` digits of the rounded decimals. The rounding goes half away from zero to `places` decimals. With `places` of 0 or less, a value under one half reads as 0. A value that would round to 0 at `places` decimals reads up to its first digit that is not 0, and the rounding goes to that digit.

With `scientific` set, a number with a mantissa and an exponent other than 0 reads as the mantissa, the `times` words and the exponent, each with the minus word where it is negative. The mantissa keeps `places` decimals, rounded half away from zero. A whole number of more than 15 digits reads the same way when its reading in the rule set repeats a word that is no digit word, and the lexicon has `scientific`.

### Fractions

The `fraction` object holds `limit`, `named`, `denominator`, `single` and `source`, and optionally `mixed`, `mixed_named` and `plural`. `mixed_named` maps a denominator to the words that follow a whole part (kab "yiwen d wezgen"), where `named` holds the word with no whole part ("azgen"). A fraction "n/m" with a denominator from 2 to `limit` reads as a mixed number: the whole part, if it is not 0, then the rest. A fraction with a rest of 0 reads as in the last case below. When `named` holds the denominator, its word follows the whole part and the numerator is left out. For another denominator the rest is the cardinal of the numerator and the `denominator` text, where `{cardinal}` stands for the cardinal of the denominator. The text `single` stands for a numerator of 1 with no whole part, and `{denominator}` stands for the denominator text. Every other fraction reads as the cardinal of the numerator and the ordinal of the denominator. A negative fraction starts with the minus word. A denominator of 0 raises `ZeroDivisionError`.

A `fraction` of `null` means the language has no fraction words, and a fraction raises `ValueError`.

With `"mixed": false` a fraction reads no whole part. It reads as the cardinal of the numerator and the word of the denominator. That word is the `named` word of the denominator, or the ordinal of the denominator when the ordinal is one word (20, 300, 1000), and it takes the `plural` ending after a numerator other than 1. Every other denominator reads as the `denominator` text. When that text holds `{numerator}`, the text is the whole reading, with the cardinal of the numerator in that place: in ro, `"{numerator} pe {cardinal}"` reads 3/25 as "trei pe douăzeci și cinci". A denominator of 1 raises `ValueError`, because the form has no word for it. So 2/3 reads "dois terços", 3/20 "três vigésimos", 5/11 "cinco onze avos" and 1/10000 "um dez mil avos".

Two optional keys change the `"mixed": false` reading. `ruleset` names a rule set that spells each denominator that `named` does not hold, with the `plural` ending after a numerator other than 1: in es, 3/56 reads "tres cincuentaiseisavos". With a `ruleset`, a `single` text that starts with `{denominator}` reads a numerator of 1 after the word of the part: in eu, `"{denominator} bat"` reads 1/3 as "heren bat". With a `ruleset`, a `denominator` text that holds `{numerator}` reads a fraction whose part is more than one word and whose numerator is not 1: in eu, `"{numerator} zati {cardinal}"` reads 13/47 as "hamahiru zati berrogeita zazpi". `numerator` names the rule set of the numerator, in place of the cardinal: in es, `cardinal-m` reads 21/50 as "veintiún cincuentavos". `plural` is a suffix ("s") or a map from a word ending to its plural ending: in it, `{"o": "i", "a": "e"}` reads 2/3 as "due terzi". With `"capitalise": true` the word of the denominator starts with a capital letter: in de, 2/3 reads "zwei Drittel".

```json
{"fraction": {"limit": 20, "named": {"2": "setengah"}, "denominator": "per{cardinal}", "single": "se{denominator}", "source": "..."}}
```

With this object, 1/4 reads "seperempat", 2/3 reads "dua pertiga" and 3/2 reads "satu setengah".

---
[← Adding a language](adding-a-language.md) · [Home](index.md) · [Design →](design.md)

