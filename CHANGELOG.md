# Changelog

## [0.15.10a1](https://github.com/TigreGotico/numtag/tree/0.15.10a1) (2026-11-19)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.15.6a1...0.15.10a1)

**Merged pull requests:**

- fix: tr yuzde yuz reads 100 at full confidence [\#208](https://github.com/TigreGotico/numtag/pull/208) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- fix: read a number whose group marks mix spaces, and check every lexicon's marks [\#205](https://github.com/TigreGotico/numtag/pull/205) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- fix\(de\): "halb" before an hour is the half hour, no number [\#183](https://github.com/TigreGotico/numtag/pull/183) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- fix\(it,ca,oc\): a cardinal before a Latin unit ordinal makes no compound [\#182](https://github.com/TigreGotico/numtag/pull/182) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- fix\(fr, it, ro\): read "moins" after an hour, "quanto meno" and a lone point [\#175](https://github.com/TigreGotico/numtag/pull/175) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- perf: read each position once and cache the lookup forms [\#153](https://github.com/TigreGotico/numtag/pull/153) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- fix: read no word before the first token, and a marker word as a noun [\#152](https://github.com/TigreGotico/numtag/pull/152) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.15.6a1](https://github.com/TigreGotico/numtag/tree/0.15.6a1) (2026-11-18)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.15.5a1...0.15.6a1)

## [0.15.5a1](https://github.com/TigreGotico/numtag/tree/0.15.5a1) (2026-11-18)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.15.4a3...0.15.5a1)

**Merged pull requests:**

- fix\(gl\): read "mil e" and the next group as one number [\#154](https://github.com/TigreGotico/numtag/pull/154) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- fix\(nl\): read "anderhalve" as 1.5 [\#151](https://github.com/TigreGotico/numtag/pull/151) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.15.4a3](https://github.com/TigreGotico/numtag/tree/0.15.4a3) (2026-11-18)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.15.4a2...0.15.4a3)

## [0.15.4a2](https://github.com/TigreGotico/numtag/tree/0.15.4a2) (2026-11-18)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.15.4a1...0.15.4a2)

## [0.15.4a1](https://github.com/TigreGotico/numtag/tree/0.15.4a1) (2026-11-18)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.15.3a1...0.15.4a1)

**Merged pull requests:**

- fix: a marker word at the end leaves a first digit its count [\#135](https://github.com/TigreGotico/numtag/pull/135) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- Update astral-sh/setup-uv action to v10 [\#56](https://github.com/TigreGotico/numtag/pull/56) ([renovate[bot]](https://github.com/apps/renovate))
- Update actions/checkout action to v7 [\#55](https://github.com/TigreGotico/numtag/pull/55) ([renovate[bot]](https://github.com/apps/renovate))

## [0.15.3a1](https://github.com/TigreGotico/numtag/tree/0.15.3a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.15.2a1...0.15.3a1)

**Merged pull requests:**

- fix: read a fraction of a scale word as one number [\#113](https://github.com/TigreGotico/numtag/pull/113) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.15.2a1](https://github.com/TigreGotico/numtag/tree/0.15.2a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.15.1a1...0.15.2a1)

## [0.15.1a1](https://github.com/TigreGotico/numtag/tree/0.15.1a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.15.0a1...0.15.1a1)

**Merged pull requests:**

- fix\(en\): digits around a spoken "point" make one decimal [\#78](https://github.com/TigreGotico/numtag/pull/78) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- fix: digits before a denominator word count its parts [\#75](https://github.com/TigreGotico/numtag/pull/75) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.15.0a1](https://github.com/TigreGotico/numtag/tree/0.15.0a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.10a1...0.15.0a1)

**Merged pull requests:**

- feat: tag vague quantities in en and pt [\#110](https://github.com/TigreGotico/numtag/pull/110) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.10a1](https://github.com/TigreGotico/numtag/tree/0.14.10a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.9a1...0.14.10a1)

**Merged pull requests:**

- fix: follow CLDR 49.0.0 for the group mark of et, fi, hu, nb, nn and sv [\#126](https://github.com/TigreGotico/numtag/pull/126) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.9a1](https://github.com/TigreGotico/numtag/tree/0.14.9a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.8a1...0.14.9a1)

**Merged pull requests:**

- fix\(es\): read the older "mil y quinientos" as one number [\#109](https://github.com/TigreGotico/numtag/pull/109) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.8a1](https://github.com/TigreGotico/numtag/tree/0.14.8a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.7a1...0.14.8a1)

**Merged pull requests:**

- fix: a hundred after a vague scale word starts its own number [\#122](https://github.com/TigreGotico/numtag/pull/122) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.7a1](https://github.com/TigreGotico/numtag/tree/0.14.7a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.6a2...0.14.7a1)

**Merged pull requests:**

- fix\(hr\): digits and word decimals count a counted hundred noun [\#114](https://github.com/TigreGotico/numtag/pull/114) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.6a2](https://github.com/TigreGotico/numtag/tree/0.14.6a2) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.6a1...0.14.6a2)

**Merged pull requests:**

- docs\(tr\): the percent word comes before the number [\#91](https://github.com/TigreGotico/numtag/pull/91) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.6a1](https://github.com/TigreGotico/numtag/tree/0.14.6a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.5a1...0.14.6a1)

**Merged pull requests:**

- fix\(es\): "cien por cien" reads one mention of 100 [\#96](https://github.com/TigreGotico/numtag/pull/96) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.5a1](https://github.com/TigreGotico/numtag/tree/0.14.5a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.4a1...0.14.5a1)

**Merged pull requests:**

- fix\(eu\): read the fraction words of Euskaltzaindia rule 203 and a lone "laurden" [\#92](https://github.com/TigreGotico/numtag/pull/92) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.4a1](https://github.com/TigreGotico/numtag/tree/0.14.4a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.3a1...0.14.4a1)

**Merged pull requests:**

- fix\(tr\): a vague word before a scale word makes no number [\#90](https://github.com/TigreGotico/numtag/pull/90) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.3a1](https://github.com/TigreGotico/numtag/tree/0.14.3a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.2a1...0.14.3a1)

**Merged pull requests:**

- fix\(hr\): a count and "stotina" before a scale word make one number [\#89](https://github.com/TigreGotico/numtag/pull/89) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.2a1](https://github.com/TigreGotico/numtag/tree/0.14.2a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.1a1...0.14.2a1)

**Merged pull requests:**

- fix\(de\): a count glued to a part word names one denominator [\#84](https://github.com/TigreGotico/numtag/pull/84) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.1a1](https://github.com/TigreGotico/numtag/tree/0.14.1a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.14.0a1...0.14.1a1)

**Merged pull requests:**

- fix\(es\): "mil y una", "diez y seis" and "ciento" read as numbers [\#87](https://github.com/TigreGotico/numtag/pull/87) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.14.0a1](https://github.com/TigreGotico/numtag/tree/0.14.0a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.13.6a1...0.14.0a1)

**Merged pull requests:**

- feat: read a proper digit slash fraction as one fraction mention [\#72](https://github.com/TigreGotico/numtag/pull/72) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.13.6a1](https://github.com/TigreGotico/numtag/tree/0.13.6a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.13.5a1...0.13.6a1)

**Merged pull requests:**

- fix\(hr\): a word of vague quantity before a scale word makes no number [\#85](https://github.com/TigreGotico/numtag/pull/85) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.13.5a1](https://github.com/TigreGotico/numtag/tree/0.13.5a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.13.4a1...0.13.5a1)

## [0.13.4a1](https://github.com/TigreGotico/numtag/tree/0.13.4a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.13.3a1...0.13.4a1)

**Merged pull requests:**

- fix\(tr\): read a lone "çeyrek" as a quarter [\#88](https://github.com/TigreGotico/numtag/pull/88) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- fix\(eu\): read erdi, heren and laurden with the article -a [\#86](https://github.com/TigreGotico/numtag/pull/86) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.13.3a1](https://github.com/TigreGotico/numtag/tree/0.13.3a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.13.2a1...0.13.3a1)

**Merged pull requests:**

- fix\(hu\): a lone glued part word reads as the multiplier at the homograph score [\#83](https://github.com/TigreGotico/numtag/pull/83) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.13.2a1](https://github.com/TigreGotico/numtag/tree/0.13.2a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.13.1a1...0.13.2a1)

**Merged pull requests:**

- fix: a locale's own group mark before a point decimal reads as one number [\#82](https://github.com/TigreGotico/numtag/pull/82) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.13.1a1](https://github.com/TigreGotico/numtag/tree/0.13.1a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.13.0a1...0.13.1a1)

**Merged pull requests:**

- fix\(en\): name the -illion words of ranks 21 to 99 and 101 [\#80](https://github.com/TigreGotico/numtag/pull/80) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.13.0a1](https://github.com/TigreGotico/numtag/tree/0.13.0a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.16a1...0.13.0a1)

**Merged pull requests:**

- feat\(en\): read "googol" as 10^100 [\#79](https://github.com/TigreGotico/numtag/pull/79) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.16a1](https://github.com/TigreGotico/numtag/tree/0.12.16a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.15a1...0.12.16a1)

## [0.12.15a1](https://github.com/TigreGotico/numtag/tree/0.12.15a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.14a1...0.12.15a1)

**Merged pull requests:**

- fix\(en\): "oh", "o" and "nought" are the digit zero after "point" [\#73](https://github.com/TigreGotico/numtag/pull/73) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.14a1](https://github.com/TigreGotico/numtag/tree/0.12.14a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.13a1...0.12.14a1)

**Merged pull requests:**

- fix\(en\): "a billionth" and "a trillionth" are fractions [\#70](https://github.com/TigreGotico/numtag/pull/70) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- fix\(en\): digits before "and a half" count a scale word [\#67](https://github.com/TigreGotico/numtag/pull/67) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.13a1](https://github.com/TigreGotico/numtag/tree/0.12.13a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.12a1...0.12.13a1)

**Merged pull requests:**

- fix: a space group before a point decimal reads as one SI number [\#81](https://github.com/TigreGotico/numtag/pull/81) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.12a1](https://github.com/TigreGotico/numtag/tree/0.12.12a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.11a1...0.12.12a1)

**Merged pull requests:**

- fix: add the large scale names that ten lexicons lacked [\#77](https://github.com/TigreGotico/numtag/pull/77) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.11a1](https://github.com/TigreGotico/numtag/tree/0.12.11a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.10a1...0.12.11a1)

**Merged pull requests:**

- fix\(an,fi,gl,fa,fy\): add six attested word forms [\#74](https://github.com/TigreGotico/numtag/pull/74) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.10a1](https://github.com/TigreGotico/numtag/tree/0.12.10a1) (2026-11-17)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.9a1...0.12.10a1)

**Merged pull requests:**

- fix\(tagger\): a joiner prefix before a number is no part of its span [\#76](https://github.com/TigreGotico/numtag/pull/76) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.9a1](https://github.com/TigreGotico/numtag/tree/0.12.9a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.8a1...0.12.9a1)

**Merged pull requests:**

- fix: only a real space group before a point decimal keeps it unread [\#71](https://github.com/TigreGotico/numtag/pull/71) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.8a1](https://github.com/TigreGotico/numtag/tree/0.12.8a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.7a2...0.12.8a1)

**Merged pull requests:**

- fix\(hu\): a count glued to a part word of a hundred or more multiplies it [\#69](https://github.com/TigreGotico/numtag/pull/69) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.7a2](https://github.com/TigreGotico/numtag/tree/0.12.7a2) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.7a1...0.12.7a2)

**Merged pull requests:**

- docs: a lone "meio" before a plural scale noun keeps its own reading [\#68](https://github.com/TigreGotico/numtag/pull/68) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.7a1](https://github.com/TigreGotico/numtag/tree/0.12.7a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.6a1...0.12.7a1)

**Merged pull requests:**

- fix: a point that cannot group digits marks decimals [\#66](https://github.com/TigreGotico/numtag/pull/66) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.6a1](https://github.com/TigreGotico/numtag/tree/0.12.6a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.5a1...0.12.6a1)

**Merged pull requests:**

- fix\(hu\): "hat" after a request verb or alone is six [\#63](https://github.com/TigreGotico/numtag/pull/63) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.5a1](https://github.com/TigreGotico/numtag/tree/0.12.5a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.4a1...0.12.5a1)

**Merged pull requests:**

- fix: a plural scale noun takes no count of one or a half in words [\#65](https://github.com/TigreGotico/numtag/pull/65) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.4a1](https://github.com/TigreGotico/numtag/tree/0.12.4a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.3a1...0.12.4a1)

**Merged pull requests:**

- fix\(pt\): a comma links only a smaller class [\#64](https://github.com/TigreGotico/numtag/pull/64) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.3a1](https://github.com/TigreGotico/numtag/tree/0.12.3a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.2a1...0.12.3a1)

**Merged pull requests:**

- fix\(pt\): cite the corpus for the "a menos" idiom [\#62](https://github.com/TigreGotico/numtag/pull/62) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.2a1](https://github.com/TigreGotico/numtag/tree/0.12.2a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.1a1...0.12.2a1)

**Merged pull requests:**

- fix\(hu\): "hat" as a verb, "egybe" and "egytől egyig" are no sure number [\#61](https://github.com/TigreGotico/numtag/pull/61) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.1a1](https://github.com/TigreGotico/numtag/tree/0.12.1a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.12.0a1...0.12.1a1)

**Merged pull requests:**

- fix: a minus sign negates the whole number its digits start [\#60](https://github.com/TigreGotico/numtag/pull/60) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.12.0a1](https://github.com/TigreGotico/numtag/tree/0.12.0a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.11.0a1...0.12.0a1)

**Merged pull requests:**

- feat: Roman numerals [\#59](https://github.com/TigreGotico/numtag/pull/59) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.11.0a1](https://github.com/TigreGotico/numtag/tree/0.11.0a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.13a4...0.11.0a1)

**Merged pull requests:**

- feat: NumberMention.parts, the pieces of a number [\#58](https://github.com/TigreGotico/numtag/pull/58) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.13a4](https://github.com/TigreGotico/numtag/tree/0.10.13a4) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.13a3...0.10.13a4)

**Merged pull requests:**

- test: the readings ovos-typed-slots-transformer depends on [\#57](https://github.com/TigreGotico/numtag/pull/57) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.13a3](https://github.com/TigreGotico/numtag/tree/0.10.13a3) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.13a2...0.10.13a3)

**Merged pull requests:**

- ci: run each consumer's own suite against numtag dev [\#54](https://github.com/TigreGotico/numtag/pull/54) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.13a2](https://github.com/TigreGotico/numtag/tree/0.10.13a2) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.13a1...0.10.13a2)

**Merged pull requests:**

- test: the readings that numtag's consumers depend on [\#53](https://github.com/TigreGotico/numtag/pull/53) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.13a1](https://github.com/TigreGotico/numtag/tree/0.10.13a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.12a1...0.10.13a1)

**Merged pull requests:**

- fix\(ca, oc, fr, it\): "of" joined to the article is an of-word [\#52](https://github.com/TigreGotico/numtag/pull/52) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.12a1](https://github.com/TigreGotico/numtag/tree/0.10.12a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.11a1...0.10.12a1)

**Merged pull requests:**

- fix\(ru, uk, pl, cs\): "one and the same" holds no number [\#51](https://github.com/TigreGotico/numtag/pull/51) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.11a1](https://github.com/TigreGotico/numtag/tree/0.10.11a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.10a1...0.10.11a1)

**Merged pull requests:**

- fix: a percent phrase with no number before it is weak [\#50](https://github.com/TigreGotico/numtag/pull/50) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.10a1](https://github.com/TigreGotico/numtag/tree/0.10.10a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.9a1...0.10.10a1)

**Merged pull requests:**

- fix: an article before a lone homograph is the article [\#49](https://github.com/TigreGotico/numtag/pull/49) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.9a1](https://github.com/TigreGotico/numtag/tree/0.10.9a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.8a1...0.10.9a1)

**Merged pull requests:**

- fix\(ca\): "nou" after "els" or "les" is the number [\#48](https://github.com/TigreGotico/numtag/pull/48) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.8a1](https://github.com/TigreGotico/numtag/tree/0.10.8a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.7a1...0.10.8a1)

**Merged pull requests:**

- fix\(fr, it\): "premier", "primo" and "prima" are homographs [\#47](https://github.com/TigreGotico/numtag/pull/47) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.7a1](https://github.com/TigreGotico/numtag/tree/0.10.7a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.6a2...0.10.7a1)

**Merged pull requests:**

- fix: number words beside a homograph make it sure [\#46](https://github.com/TigreGotico/numtag/pull/46) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.6a2](https://github.com/TigreGotico/numtag/tree/0.10.6a2) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.6a1...0.10.6a2)

**Merged pull requests:**

- test: a gold mention with no low\_confidence flag must be sure [\#45](https://github.com/TigreGotico/numtag/pull/45) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.6a1](https://github.com/TigreGotico/numtag/tree/0.10.6a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.5a1...0.10.6a1)

**Merged pull requests:**

- fix\(fr\): one after "le nombre" is the number [\#44](https://github.com/TigreGotico/numtag/pull/44) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.5a1](https://github.com/TigreGotico/numtag/tree/0.10.5a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.4a1...0.10.5a1)

**Merged pull requests:**

- fix: one before a percent phrase is the number [\#43](https://github.com/TigreGotico/numtag/pull/43) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.4a1](https://github.com/TigreGotico/numtag/tree/0.10.4a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.3a1...0.10.4a1)

**Merged pull requests:**

- fix\(fa\): a weekday name written with a space holds no number [\#42](https://github.com/TigreGotico/numtag/pull/42) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.3a1](https://github.com/TigreGotico/numtag/tree/0.10.3a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.2a1...0.10.3a1)

**Merged pull requests:**

- fix: one after a noun that names a number is the number [\#41](https://github.com/TigreGotico/numtag/pull/41) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.2a1](https://github.com/TigreGotico/numtag/tree/0.10.2a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.1a1...0.10.2a1)

**Merged pull requests:**

- fix\(it\): the elided article "un'" gets the article score [\#40](https://github.com/TigreGotico/numtag/pull/40) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.1a1](https://github.com/TigreGotico/numtag/tree/0.10.1a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.10.0a1...0.10.1a1)

**Merged pull requests:**

- fix\(hu, fr\): a count noun after a sure cardinal is no number [\#39](https://github.com/TigreGotico/numtag/pull/39) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.10.0a1](https://github.com/TigreGotico/numtag/tree/0.10.0a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.9.4a1...0.10.0a1)

**Merged pull requests:**

- feat: raise UnsupportedLanguageError for a language with no lexicon [\#38](https://github.com/TigreGotico/numtag/pull/38) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.9.4a1](https://github.com/TigreGotico/numtag/tree/0.9.4a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.9.3a1...0.9.4a1)

**Merged pull requests:**

- fix: an article that is the whole text gets the article score [\#37](https://github.com/TigreGotico/numtag/pull/37) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.9.3a1](https://github.com/TigreGotico/numtag/tree/0.9.3a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.9.2a1...0.9.3a1)

**Merged pull requests:**

- fix\(ru, pl\): one after a negative particle counts nothing [\#36](https://github.com/TigreGotico/numtag/pull/36) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.9.2a1](https://github.com/TigreGotico/numtag/tree/0.9.2a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.9.1a1...0.9.2a1)

**Merged pull requests:**

- fix: an article before a hyphenated noun gets the article score [\#35](https://github.com/TigreGotico/numtag/pull/35) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.9.1a1](https://github.com/TigreGotico/numtag/tree/0.9.1a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.9.0a1...0.9.1a1)

**Merged pull requests:**

- fix: the hundred of a percent phrase is the percent sign [\#34](https://github.com/TigreGotico/numtag/pull/34) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.9.0a1](https://github.com/TigreGotico/numtag/tree/0.9.0a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.8.4a1...0.9.0a1)

**Merged pull requests:**

- feat: a weak mention says why it is weak [\#33](https://github.com/TigreGotico/numtag/pull/33) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.8.4a1](https://github.com/TigreGotico/numtag/tree/0.8.4a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.8.3a1...0.8.4a1)

**Merged pull requests:**

- fix\(en\): a collective after "thousand" counts the whole cardinal [\#32](https://github.com/TigreGotico/numtag/pull/32) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.8.3a1](https://github.com/TigreGotico/numtag/tree/0.8.3a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.8.2a1...0.8.3a1)

**Merged pull requests:**

- fix\(pt\): the word after "um quinto" decides fraction or ordinal [\#31](https://github.com/TigreGotico/numtag/pull/31) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.8.2a1](https://github.com/TigreGotico/numtag/tree/0.8.2a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.8.1a1...0.8.2a1)

**Merged pull requests:**

- fix: a slash fraction over zero gives no mention [\#30](https://github.com/TigreGotico/numtag/pull/30) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.8.1a1](https://github.com/TigreGotico/numtag/tree/0.8.1a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.8.0a1...0.8.1a1)

**Merged pull requests:**

- fix: an article before an ordinal gets the article score [\#29](https://github.com/TigreGotico/numtag/pull/29) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.8.0a1](https://github.com/TigreGotico/numtag/tree/0.8.0a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.9a1...0.8.0a1)

**Merged pull requests:**

- feat: export ARTICLE\_CONFIDENCE from the package [\#28](https://github.com/TigreGotico/numtag/pull/28) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.9a1](https://github.com/TigreGotico/numtag/tree/0.7.9a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.8a1...0.7.9a1)

**Merged pull requests:**

- fix\(cs\): "jednou" alone is also the adverb "once" [\#27](https://github.com/TigreGotico/numtag/pull/27) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.8a1](https://github.com/TigreGotico/numtag/tree/0.7.8a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.7a1...0.7.8a1)

**Merged pull requests:**

- fix\(ca\): "nou" and "u" alone are words with a second meaning [\#26](https://github.com/TigreGotico/numtag/pull/26) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.7a1](https://github.com/TigreGotico/numtag/tree/0.7.7a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.6a1...0.7.7a1)

**Merged pull requests:**

- fix\(es, de\): a lone article at the clause end gets the article score [\#25](https://github.com/TigreGotico/numtag/pull/25) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.6a1](https://github.com/TigreGotico/numtag/tree/0.7.6a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.5a1...0.7.6a1)

**Merged pull requests:**

- fix: an article before a number in digits gets the article score [\#24](https://github.com/TigreGotico/numtag/pull/24) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.5a1](https://github.com/TigreGotico/numtag/tree/0.7.5a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.4a1...0.7.5a1)

**Merged pull requests:**

- fix\(eu\): read an ordinal with the article -a [\#23](https://github.com/TigreGotico/numtag/pull/23) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.4a1](https://github.com/TigreGotico/numtag/tree/0.7.4a1) (2026-11-16)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.3a1...0.7.4a1)

**Merged pull requests:**

- fix: read "the one hundredth" as an English ordinal [\#22](https://github.com/TigreGotico/numtag/pull/22) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.3a1](https://github.com/TigreGotico/numtag/tree/0.7.3a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.2a1...0.7.3a1)

**Merged pull requests:**

- fix: link an English class across a comma before a group of a hundred or more [\#21](https://github.com/TigreGotico/numtag/pull/21) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.2a1](https://github.com/TigreGotico/numtag/tree/0.7.2a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.1a1...0.7.2a1)

**Merged pull requests:**

- fix: read an English unit ordinal after a ten as the cardinal does [\#20](https://github.com/TigreGotico/numtag/pull/20) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.1a1](https://github.com/TigreGotico/numtag/tree/0.7.1a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.0a2...0.7.1a1)

**Merged pull requests:**

- fix: read a digit count after a joiner prefix and after the first group [\#19](https://github.com/TigreGotico/numtag/pull/19) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.0a2](https://github.com/TigreGotico/numtag/tree/0.7.0a2) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.7.0a1...0.7.0a2)

**Merged pull requests:**

- docs: list the ported languages and add a page per language group [\#18](https://github.com/TigreGotico/numtag/pull/18) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.7.0a1](https://github.com/TigreGotico/numtag/tree/0.7.0a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.6.0a1...0.7.0a1)

**Merged pull requests:**

- feat: read es, gl, ca, ast, an, oc and mwl numbers [\#11](https://github.com/TigreGotico/numtag/pull/11) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.6.0a1](https://github.com/TigreGotico/numtag/tree/0.6.0a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.5.0a1...0.6.0a1)

## [0.5.0a1](https://github.com/TigreGotico/numtag/tree/0.5.0a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.4.0a1...0.5.0a1)

## [0.4.0a1](https://github.com/TigreGotico/numtag/tree/0.4.0a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.3.0a2...0.4.0a1)

**Merged pull requests:**

- feat: read Finnish, Estonian, Hungarian, Turkish and Azerbaijani numbers [\#9](https://github.com/TigreGotico/numtag/pull/9) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.3.0a2](https://github.com/TigreGotico/numtag/tree/0.3.0a2) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.3.0a1...0.3.0a2)

**Merged pull requests:**

- test: a count and a collective after a scale numeral start a new number [\#17](https://github.com/TigreGotico/numtag/pull/17) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.3.0a1](https://github.com/TigreGotico/numtag/tree/0.3.0a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.2.0a4...0.3.0a1)

## [0.2.0a4](https://github.com/TigreGotico/numtag/tree/0.2.0a4) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.2.0a3...0.2.0a4)

**Merged pull requests:**

- docs: fix the claims of the claim audit [\#15](https://github.com/TigreGotico/numtag/pull/15) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.2.0a3](https://github.com/TigreGotico/numtag/tree/0.2.0a3) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.2.0a2...0.2.0a3)

**Merged pull requests:**

- test: a round last class before a collective needs the joiner [\#16](https://github.com/TigreGotico/numtag/pull/16) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.2.0a2](https://github.com/TigreGotico/numtag/tree/0.2.0a2) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.2.0a1...0.2.0a2)

## [0.2.0a1](https://github.com/TigreGotico/numtag/tree/0.2.0a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.1.0a1...0.2.0a1)

**Merged pull requests:**

- docs: quote a saved page in every lexicon and gold source field [\#14](https://github.com/TigreGotico/numtag/pull/14) ([openvoiceos-bot](https://github.com/openvoiceos-bot))
- feat: read el, ar, he, fa and kab numbers [\#10](https://github.com/TigreGotico/numtag/pull/10) ([openvoiceos-bot](https://github.com/openvoiceos-bot))

## [0.1.0a1](https://github.com/TigreGotico/numtag/tree/0.1.0a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.0.2a1...0.1.0a1)

## [0.0.2a1](https://github.com/TigreGotico/numtag/tree/0.0.2a1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.0.1...0.0.2a1)

## [0.0.1](https://github.com/TigreGotico/numtag/tree/0.0.1) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/0.0.1a2...0.0.1)

## [0.0.1a2](https://github.com/TigreGotico/numtag/tree/0.0.1a2) (2026-11-15)

[Full Changelog](https://github.com/TigreGotico/numtag/compare/8755566a98e5c6ad921f1edd2a001145180787c6...0.0.1a2)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
