# Supported languages

<!-- agent-hint
covers: Per lexicon, what numtag reads and writes, and its score on the gold corpus.
source: numtag/lexicon/*.json, benchmarks/results.json
generated: yes, by scripts/language_table.py; do not edit by hand
verify: python scripts/language_table.py --check
see: ../adding-a-language.md, ../benchmarks.md
-->

Each row is one lexicon in `numtag/lexicon/`. A lexicon reads cardinals when it has unit entries, ordinals when it has ordinal entries or entries with an ordinal form, and fractions when it has half, denominator, fraction or rational entries. It has a writer when the file has a `writer` block. "Gold rows" is the number of rows in `tests/gold/<lang>.jsonl`, "Rows right" is the number of rows that numtag reads right, from `benchmarks/results.json`, and "Share" is rows right divided by gold rows. A dash means the language has no gold file.

The leader languages come first, each named by its full tag and the lexicon that the tag resolves to. The other languages follow in alphabetical order.

| Language | Cardinals | Ordinals | Fractions | Writer | Gold rows | Rows right | Share | Page |
|---|---|---|---|---|---|---|---|---|
| `pt-PT` | yes | yes | yes | yes | 479 | 473 | 98.7% | [pt.md](pt.md) |
| `pt-BR` | yes | yes | yes | yes | 470 | 464 | 98.7% | [pt.md](pt.md) |
| `es-CO` (resolves to `es`) | yes | yes | yes | yes | 237 | 234 | 98.7% | [ibero.md](ibero.md) |
| `fr-FR` | yes | yes | yes | yes | 201 | 199 | 99.0% | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `it-IT` (resolves to `it`) | yes | yes | yes | yes | 194 | 191 | 98.5% | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `de-DE` (resolves to `de`) | yes | yes | yes | yes | 200 | 200 | 100.0% | [germanic.md](germanic.md) |
| `nl-NL` (resolves to `nl`) | yes | yes | yes | yes | 187 | 187 | 100.0% | [germanic.md](germanic.md) |
| `da-DK` (resolves to `da`) | yes | yes | yes | yes | 181 | 181 | 100.0% | [germanic.md](germanic.md) |
| `kab` | yes | yes | yes | yes | 194 | 194 | 100.0% | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `hi-IN` (resolves to `hi`) | yes | yes | no | yes | 284 | 284 | 100.0% | [hi.md](hi.md) |
| `bn-IN` (resolves to `bn`) | yes | yes | yes | yes | 75 | 75 | 100.0%[^bn] | [bn.md](bn.md) |
| `mwr` | yes | yes | yes | yes | 26 | 26 | 100.0%[^mwr] |  |
| `an` | yes | yes | yes | no | 153 | 153 | 100.0% | [ibero.md](ibero.md) |
| `ar` | yes | yes | yes | no | 157 | 156 | 99.4% | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `ast` | yes | yes | yes | no | 176 | 175 | 99.4% | [ibero.md](ibero.md) |
| `az` | yes | yes | yes | no | 176 | 176 | 100.0% | [uralic-turkic.md](uralic-turkic.md) |
| `bg` | yes | yes | yes | no | 163 | 163 | 100.0% | [slavic.md](slavic.md) |
| `ca` | yes | yes | yes | yes | 228 | 225 | 98.7% | [ibero.md](ibero.md) |
| `ca-ES-valencia` | yes | yes | yes | yes | - | - | - | [ibero.md](ibero.md) |
| `cs` | yes | yes | yes | yes | 185 | 184 | 99.5% | [slavic.md](slavic.md) |
| `el` | yes | yes | yes | no | 161 | 161 | 100.0% | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `en` | yes | yes | yes | yes | 444 | 442 | 99.5% | [en.md](en.md) |
| `en-US` | yes | yes | yes | yes | - | - | - | [en.md](en.md) |
| `eo` | yes | yes | yes | no | 213 | 213 | 100.0% |  |
| `et` | yes | yes | yes | no | 170 | 170 | 100.0% | [uralic-turkic.md](uralic-turkic.md) |
| `eu` | yes | yes | yes | yes | 168 | 168 | 100.0% | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `fa` | yes | yes | yes | no | 153 | 153 | 100.0% | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `fi` | yes | yes | yes | no | 181 | 181 | 100.0% | [uralic-turkic.md](uralic-turkic.md) |
| `fr-BE` | yes | yes | yes | yes | 22 | 22 | 100.0%[^fr-BE] | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `fr-CH` | yes | yes | yes | yes | 20 | 20 | 100.0%[^fr-CH] | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `fy` | yes | yes | yes | no | 156 | 156 | 100.0% | [germanic.md](germanic.md) |
| `gl` | yes | yes | yes | yes | 185 | 184 | 99.5% | [ibero.md](ibero.md) |
| `he` | yes | yes | yes | no | 160 | 157 | 98.1% | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `hr` | yes | yes | yes | no | 183 | 182 | 99.5% | [slavic.md](slavic.md) |
| `hu` | yes | yes | yes | no | 197 | 195 | 99.0% | [uralic-turkic.md](uralic-turkic.md) |
| `id` | yes | yes | yes | yes | 175 | 174 | 99.4% | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `lt` | yes | yes | yes | no | 167 | 167 | 100.0% | [baltic.md](baltic.md) |
| `ms` | yes | yes | yes | yes | 162 | 161 | 99.4% | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `mt` | yes | yes | yes | no | 185 | 177 | 95.7% | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `mwl` | yes | yes | yes | no | 162 | 162 | 100.0% | [ibero.md](ibero.md) |
| `nb` | yes | yes | yes | yes | 178 | 178 | 100.0% | [germanic.md](germanic.md) |
| `nn` | yes | yes | yes | yes | 157 | 157 | 100.0% | [germanic.md](germanic.md) |
| `oc` | yes | yes | yes | no | 174 | 174 | 100.0% | [ibero.md](ibero.md) |
| `pl` | yes | yes | yes | yes | 167 | 167 | 100.0% | [slavic.md](slavic.md) |
| `ro` | yes | yes | yes | yes | 157 | 157 | 100.0% | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `ru` | yes | yes | yes | yes | 195 | 194 | 99.5% | [slavic.md](slavic.md) |
| `sk` | yes | yes | yes | no | 154 | 154 | 100.0% | [slavic.md](slavic.md) |
| `sl` | yes | yes | yes | no | 166 | 166 | 100.0% | [slavic.md](slavic.md) |
| `sq` | yes | no | no | no | 170 | 170 | 100.0% |  |
| `sr` | yes | yes | yes | no | 149 | 149 | 100.0% | [slavic.md](slavic.md) |
| `sv` | yes | yes | yes | yes | 176 | 176 | 100.0% | [germanic.md](germanic.md) |
| `tr` | yes | yes | yes | no | 189 | 189 | 100.0% | [uralic-turkic.md](uralic-turkic.md) |
| `uk` | yes | yes | yes | no | 184 | 184 | 100.0% | [slavic.md](slavic.md) |

[^bn]: The score of `bn` rests on 75 rows.

[^mwr]: The score of `mwr` rests on 26 rows.

[^fr-BE]: The score of `fr-BE` rests on 22 rows.

[^fr-CH]: The score of `fr-CH` rests on 20 rows.

---
[← Home](../index.md)
