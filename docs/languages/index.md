# Supported languages

<!-- agent-hint
covers: Per lexicon, what numtag reads and writes, and its score on the gold corpus.
source: numtag/lexicon/*.json, benchmarks/results.json
generated: yes, by scripts/language_table.py; do not edit by hand
verify: python scripts/language_table.py --check
see: ../adding-a-language.md, ../benchmarks.md
-->

Each row is one lexicon in `numtag/lexicon/`. A lexicon reads cardinals when it has unit entries, ordinals when it has ordinal entries or entries with an ordinal form, and fractions when it has half, denominator, fraction or rational entries. It has a writer when the file has a `writer` block. "Gold rows" is the number of rows in `tests/gold/<lang>.jsonl`, and "right" is the number of rows that numtag reads right, from `benchmarks/results.json`. A dash means the language has no gold file.

The leader languages come first. The other languages follow in alphabetical order.

| Language | Cardinals | Ordinals | Fractions | Writer | Gold rows | Right | Page |
|---|---|---|---|---|---|---|---|
| `pt-PT` | yes | yes | yes | yes | 479 | 473 | [pt.md](pt.md) |
| `pt-BR` | yes | yes | yes | yes | 470 | 464 | [pt.md](pt.md) |
| `es` (es-CO resolves to es) | yes | yes | yes | yes | 237 | 234 | [ibero.md](ibero.md) |
| `fr-FR` | yes | yes | yes | yes | 201 | 199 | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `it` | yes | yes | yes | yes | 194 | 191 | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `de` | yes | yes | yes | yes | 200 | 200 | [germanic.md](germanic.md) |
| `nl` | yes | yes | yes | yes | 187 | 187 | [germanic.md](germanic.md) |
| `da` | yes | yes | yes | yes | 181 | 181 | [germanic.md](germanic.md) |
| `kab` | yes | yes | yes | no | 163 | 163 | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `hi` | yes | yes | no | no | 284 | 284 | [hi.md](hi.md) |
| `bn` | yes | yes | yes | no | 40 | 40 | [bn.md](bn.md) |
| `mwr` | not supported | | | | | | |
| `an` | yes | yes | yes | no | 153 | 153 | [ibero.md](ibero.md) |
| `ar` | yes | yes | yes | no | 157 | 156 | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `ast` | yes | yes | yes | no | 176 | 175 | [ibero.md](ibero.md) |
| `az` | yes | yes | yes | no | 176 | 176 | [uralic-turkic.md](uralic-turkic.md) |
| `bg` | yes | yes | yes | no | 163 | 163 | [slavic.md](slavic.md) |
| `ca` | yes | yes | yes | yes | 228 | 225 | [ibero.md](ibero.md) |
| `ca-ES-valencia` | yes | yes | yes | yes | - | - | [ibero.md](ibero.md) |
| `cs` | yes | yes | yes | no | 185 | 184 | [slavic.md](slavic.md) |
| `el` | yes | yes | yes | no | 161 | 161 | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `en` | yes | yes | yes | yes | 444 | 442 | [en.md](en.md) |
| `en-US` | yes | yes | yes | yes | - | - | [en.md](en.md) |
| `eo` | yes | yes | yes | no | 213 | 213 |  |
| `et` | yes | yes | yes | no | 170 | 170 | [uralic-turkic.md](uralic-turkic.md) |
| `eu` | yes | yes | yes | no | 168 | 168 | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `fa` | yes | yes | yes | no | 153 | 153 | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `fi` | yes | yes | yes | no | 181 | 181 | [uralic-turkic.md](uralic-turkic.md) |
| `fr-BE` | yes | yes | yes | yes | 22 | 22 | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `fr-CH` | yes | yes | yes | yes | 20 | 20 | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `fy` | yes | yes | yes | no | 156 | 156 | [germanic.md](germanic.md) |
| `gl` | yes | yes | yes | yes | 185 | 184 | [ibero.md](ibero.md) |
| `he` | yes | yes | yes | no | 160 | 157 | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `hr` | yes | yes | yes | no | 183 | 182 | [slavic.md](slavic.md) |
| `hu` | yes | yes | yes | no | 197 | 195 | [uralic-turkic.md](uralic-turkic.md) |
| `id` | yes | yes | yes | yes | 175 | 174 | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `lt` | yes | yes | yes | no | 167 | 167 | [baltic.md](baltic.md) |
| `ms` | yes | yes | yes | yes | 162 | 161 | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `mt` | yes | yes | yes | no | 185 | 177 | [el-ar-he-fa-kab.md](el-ar-he-fa-kab.md) |
| `mwl` | yes | yes | yes | no | 162 | 162 | [ibero.md](ibero.md) |
| `nb` | yes | yes | yes | yes | 178 | 178 | [germanic.md](germanic.md) |
| `nn` | yes | yes | yes | yes | 157 | 157 | [germanic.md](germanic.md) |
| `oc` | yes | yes | yes | no | 174 | 174 | [ibero.md](ibero.md) |
| `pl` | yes | yes | yes | no | 167 | 167 | [slavic.md](slavic.md) |
| `ro` | yes | yes | yes | yes | 157 | 157 | [fr-it-ro-eu-id.md](fr-it-ro-eu-id.md) |
| `ru` | yes | yes | yes | no | 195 | 194 | [slavic.md](slavic.md) |
| `sk` | yes | yes | yes | no | 154 | 154 | [slavic.md](slavic.md) |
| `sl` | yes | yes | yes | no | 166 | 166 | [slavic.md](slavic.md) |
| `sq` | yes | no | no | no | 170 | 170 |  |
| `sr` | yes | yes | yes | no | 149 | 149 | [slavic.md](slavic.md) |
| `sv` | yes | yes | yes | no | 176 | 176 | [germanic.md](germanic.md) |
| `tr` | yes | yes | yes | no | 189 | 189 | [uralic-turkic.md](uralic-turkic.md) |
| `uk` | yes | yes | yes | no | 184 | 184 | [slavic.md](slavic.md) |

---
[← Home](../index.md)
