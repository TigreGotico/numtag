# Bengali

<!-- agent-hint
covers: What numtag reads and writes in Bengali: the number words, the scale words and the sources for each.
source: numtag/lexicon/bn.json, tests/gold/bn.jsonl
generated: no
verify: python -c "from numtag import spell, tag_numbers; assert spell('21', 'bn')[0].text == 'একুশ'; assert tag_numbers('একুশ', 'bn')[0].value == '21'"
see: index.md, ../lexicon-format.md
-->

The `bn` lexicon reads Bengali numbers in the Bengali script and in Bengali digits. It also has a writer: `spell("21", "bn")` gives "একুশ".

## Words

| Class | Words | Source |
|---|---|---|
| 0 to 100 | one word for each number: "একুশ" is 21, "নিরানব্বই" is 99, "একশ" is 100 | Wiktionary, "Appendix:Bengali numerals", and Thompson, *Bengali* (2012), Appendix II |
| Hundreds | a count and "শ": "দুই শ" is 200 | Thompson: "200 du so" |
| Hundreds in one word | "একশো" to "নয়শো", "দুশো", "দুইশো": "সাতশো নিরানব্বই" is 799 | CLDR RBNF `bn`: "100: <<শো[ >>];", Thompson: "200 du so", Bangla Academy dictionary for "একশো" and "চারশো" |
| Classifiers | "-টা", "-টো", "-টে", "-টি", "-জন", "-খানা", "-খানি" on the last word of a number: "সাতচল্লিশটা" is 47, "দুটো" is 2 | Thompson, 5.2.5: "tais added to numbers with count nouns" |
| Scale words | "হাজার" (10^3), "লাখ" and "লক্ষ" (10^5), "কোটি" (10^7) | Wiktionary, and Thompson for হাজার and লাখ |
| Ordinals | "প্রথম" to "দশম", 1st to 10th | Wiktionary, and Thompson, "ordinal numbers" |
| Half | "অর্ধেক", "আধ" | Wiktionary, and Thompson: "adha/adh half" |

```python
>>> from numtag import tag_numbers
>>> [(m.text, m.value) for m in tag_numbers("বাজেট তিন কোটি পঞ্চাশ লাখ টাকা।", "bn")]
[('তিন কোটি পঞ্চাশ লাখ', '35000000')]
>>> [(m.text, m.value) for m in tag_numbers("মেলায় চারশো বিরাশিটি দোকান বসেছিল।", "bn")]
[('চারশো বিরাশিটি', '482')]
```

## Limits

- "একটা" and "একটি" also mark an indefinite noun ("a"), but they read as the number 1.
- Digits grouped in the Indian way ("১,০০,০০০") give no mention.
- The ordinals past 10 and the fraction words other than the half have no source and are not read.

---
[← Baltic languages](baltic.md) · [Home](../index.md) · [Hindi →](hi.md)
