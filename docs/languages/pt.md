# Portuguese

numtag reads European Portuguese and Brazilian Portuguese. The tag `pt-BR` reads Brazilian Portuguese. Every other `pt` tag (`pt`, `pt-PT`, `pt-AO`, `pt-MZ`) reads European Portuguese. The lexicon files are `numtag/lexicon/pt-PT.json` and `numtag/lexicon/pt-BR.json`.

## Two lexicons, one grammar

`pt-BR.json` extends `pt-PT.json`. It changes two settings and keeps every word.

| Setting | `pt-PT` | `pt-BR` |
|---|---|---|
| `scale` | long: "bilião" is 10^12 | short: "bilhão" is 10^9 |
| `space_groups` | true: "1 000 000" is one number | false: a space separates two numbers |

Both lexicons read both spellings of each word: "bilião" and "bilhão", "dezasseis" and "dezesseis", "catorze" and "quatorze".

```python
>>> from numtag import tag_numbers
>>> def read(text, lang="pt-PT"):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read("O clube deve um bilhão de euros.", "pt-PT")
[('um bilhão', '1000000000000')]
>>> read("O clube deve um bilhão de reais.", "pt-BR")
[('um bilhão', '1000000000')]
>>> read("Moram lá 1 000 000 de pessoas.", "pt-PT")
[('1 000 000', '1000000')]
>>> read("Dezasseis ou dezesseis, catorze ou quatorze.", "pt-BR")
[('Dezasseis', '16'), ('dezesseis', '16'), ('catorze', '14'), ('quatorze', '14')]
```

> Priberam, "bilhão", sense 1: "[Informal] Um milhão de milhões (10^12)."

> Priberam, "bilião", sense 2: "[Brasil] Mil milhões (10^9)".

> FLiP, "separadores numéricos": "é aconselhável não utilizar outro separador para as classes de algarismos senão o espaço (ex.: 1000000 ou 1 000 000)".

## What the lexicon reads

| Role | Entries | Examples |
|---|---|---|
| unit | 12 | "zero", "um", "uma", "dois", "duas" |
| ten | 22 | "dez", "onze", "dezasseis", "dezesseis", "vinte" |
| hundred | 18 | "cem", "cento", "duzentos", "duzentas" |
| scale numeral | 1 | "mil" |
| scale noun | 92 | "milhar", "milhão", "milhões", "bilião", "bilhão", up to "centilião" |
| collective | 6 | "dezena", "dúzia", "centena" and their plurals |
| half | 2 | "meio", "meia" |
| denominator | 32 | "terço", "quarto", "décimo", "milésimo" and their plurals |
| ordinal | 132 | "primeiro" to "nongentésimo", in both genders and numbers |
| ordinal scale | 6 | "milésimo", "milionésimo", "bilionésimo" |
| ordinal suffix | 2 | "º", "ª" |

The words are case-insensitive. Digits use "." to group and "," for decimals: "1.234.567,5".

```python
>>> read("Pagou 1.234.567,5 euros e ficou em 1.º lugar na 2.ª volta.")
[('1.234.567,5', '1234567.5'), ('1.º', '1'), ('2.ª', '2')]
>>> read("Comprou duas dúzias, três quartos e um terço de dúzia.")
[('duas dúzias', '24'), ('três quartos', '0.75'), ('um terço de dúzia', '4')]
```

## The settings

| Setting | Value | Source |
|---|---|---|
| `joiner_tens_units` | required | Gramática do Português (Gulbenkian), via Ciberdúvidas 8981 |
| `joiner_after_hundred` | required | the same |
| `joiner_between_groups` | optional | Gulbenkian, Cunha & Cintra, maintainer ruling |
| `joiner_before_last_group` | required | Gulbenkian, Cunha & Cintra, Teyssier, maintainer ruling |
| `joiner_before_round_hundred` | true | the same |
| `comma_between_classes` | true | Gulbenkian, via Ciberdúvidas 8981 |
| `plural_scale_needs_count` | true | Priberam, "milhão" and "milhar" |
| `scale_noun_agrees` | true | Squarisi, Correio Braziliense; Priberam, "milhão" |
| `ordinal_style` | every_word | Teyssier, p. 183 |
| `range_cue` | "entre" | Priberam, "entre" |

[../rulings.md](../rulings.md) quotes each source and shows each rule at work. The main rule of Portuguese numbers is the joiner before the last group.

> Gramática do Português (Fundação Calouste Gulbenkian, 2013-2020, p. 932/933), quoted in Ciberdúvidas 8981: "a conjunção e liga os numerais que denotam as diferentes ordens (centenas, dezenas e unidades) de uma mesma classe [ex. 321 – trezentos e vinte e um]".

```python
>>> read("Pagou trezentos e vinte e um euros, mil e duzentos euros, e não mil duzentos.")
[('trezentos e vinte e um', '321'), ('mil e duzentos', '1200'), ('mil', '1000'), ('duzentos', '200')]
```

## Word lists

| List | Words | Use |
|---|---|---|
| `joiner` | "e" | joins the parts of a number |
| `decimal_marker` | "vírgula", "virgula", "ponto" | starts the fraction part |
| `minus` | "menos" | makes the number negative |
| `minus_idioms` | "pelo menos", "ao menos", "mais ou menos", "a menos" | "menos" in these is no sign |
| `article_one` | "um", "uma" | the article that is also the number one |
| `of` | "de" | "dois milhões de dúzias" |
| `fraction_of` | "de" | "um terço de dúzia" |
| `denominator_particle` | "avos" | "doze avos" |
| `class_noun` | "milhar" | "duas dezenas de milhar" |
| `half_unit` | 20 units of measure and of time | "meio quilo", "meia hora" |
| `abbreviation` | "dez" | "dez." for "dezembro" |
| `lone_decimal_mark` | ",", "." | ",5" and ".5" |
| `range_cue` | "entre" | "entre cem mil e um milhão" |

## Known misreadings

The European Portuguese gold corpus has 458 rows, and numtag reads 452 of them right. The Brazilian corpus has 456 rows, and numtag reads 450 right. The same six sentences fail in both.

| Sentence | Gold | numtag |
|---|---|---|
| Ele tem menos dois anos do que eu. | 2 | -2 |
| O erro foi de um centésimo de segundo. | 0.01 | 0.01, and "segundo" as 2 at 0.4 |
| O apartamento tem três quartos e uma sala. | 3, and "uma" at a low score | 0.75 at 0.4, and "uma" at 0.3 |
| Está no meio da sala. | no number | 0.5 at 0.4 |
| Dormiu no quarto dos fundos. | no number | 4 at 0.4 |
| Segundo o jornal, choveu muito. | no number | 2 at 0.4 |

```python
>>> read("Ele tem menos dois anos do que eu.")
[('menos dois', '-2')]
```

Five of the six get the low score 0.4, so a caller that drops weak mentions loses the wrong reading. Read [../confidence-and-homographs.md](../confidence-and-homographs.md).

---
[← Rulings](../rulings.md) · [Home](../index.md) · [English →](en.md)
