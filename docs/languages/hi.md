# Hindi

<!-- agent-hint: hi reader only. Sources are CLDR 49 RBNF hi, en.wikipedia "Indian numbering system" and hi.wikipedia «अंक», as the source fields of numtag/lexicon/hi.json give them. -->

The `hi` lexicon reads Hindi numbers in the Devanagari script and in Devanagari digits. It has no writer, so `spell(value, "hi")` raises `UnsupportedLanguageError`.

## Words

| Class | Words | Source |
|---|---|---|
| 0 to 99 | one word for each number: "इक्कीस" is 21 | CLDR 49 RBNF hi, %spellout-cardinal: "21: इक्कीस" |
| Hundreds | a count and "सौ": "दो सौ" is 200 | CLDR 49 RBNF hi, %spellout-cardinal: "100: << सौ[ >>]" |
| Scale words | "हज़ार" and "सहस्र" (10^3), "लाख" (10^5), "करोड़" (10^7), "अरब" (10^9), "खरब" (10^11) | CLDR 49 RBNF hi, en.wikipedia "Indian numbering system", hi.wikipedia «अंक» |
| Ordinals | "पहला", "दूसरा", "पाँचवाँ" and the masculine, oblique and feminine forms | CLDR 49 RBNF hi, %spellout-ordinal-masculine, -masculine-oblique and -feminine |
| Decimal and minus | "दशमलव", "ऋण" | CLDR 49 RBNF hi, %spellout-cardinal: "x.x: << दशमलव >>" and "-x: ऋण >>" |

```python
>>> from numtag import tag_numbers
>>> [(m.text, m.value) for m in tag_numbers("बजट तीन करोड़ पचास लाख रुपये है।", "hi")]
[('तीन करोड़ पचास लाख', '35000000')]
```

## Limits

- The lexicon has no fraction words, so "आधा" gives no mention.
- "अरब" and "खरब" also name places and peoples, so they give a mention only after a count: "सऊदी अरब" gives no mention, and "दो अरब" is 2000000000.
