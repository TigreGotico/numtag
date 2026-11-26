# Bengali

<!-- agent-hint: bn reader only. Sources are Thompson 2012 (romanised) and the Wiktionary numeral appendix (script). -->

The `bn` lexicon reads Bengali numbers in the Bengali script and in Bengali digits. It has no writer, so `spell(value, "bn")` raises `UnsupportedLanguageError`.

## Words

| Class | Words | Source |
|---|---|---|
| 0 to 100 | one word for each number: "একুশ" is 21, "নিরানব্বই" is 99, "একশ" is 100 | Wiktionary, "Appendix:Bengali numerals", and Thompson, *Bengali* (2012), Appendix II |
| Hundreds | a count and "শ": "দুই শ" is 200 | Thompson: "200 du so" |
| Scale words | "হাজার" (10^3), "লাখ" and "লক্ষ" (10^5), "কোটি" (10^7) | Wiktionary, and Thompson for হাজার and লাখ |
| Ordinals | "প্রথম" to "দশম", 1st to 10th | Wiktionary, and Thompson, "ordinal numbers" |
| Half | "অর্ধেক", "আধ" | Wiktionary, and Thompson: "adha/adh half" |

```python
>>> from numtag import tag_numbers
>>> [(m.text, m.value) for m in tag_numbers("বাজেট তিন কোটি পঞ্চাশ লাখ টাকা।", "bn")]
[('তিন কোটি পঞ্চাশ লাখ', '35000000')]
```

## Limits

- A number with a classifier glued to it ("একুশটি", "দুটো") gives no mention.
- Digits grouped in the Indian way ("১,০০,০০০") give no mention.
- The ordinals past 10 and the fraction words other than the half have no source and are not read.
