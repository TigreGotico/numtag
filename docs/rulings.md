# Rulings

A ruling is a decided reading of a number phrase. Each ruling below has a rule, example sentences that run as tests, and the source of the rule. A source is a dictionary, a grammar, the CLDR spellout rules, a maintainer ruling, or "structural" where no outside source decides the reading. Each quote in a block quote on this page is also in a source field of a lexicon file or a gold row, word for word.

All examples on this page use this helper:

```python
>>> from numtag import tag_numbers
>>> def read(text, lang="pt-PT"):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
```

## The joiner before the last group

In Portuguese, "e" joins the tens and the units, and the hundreds to the rest of their class ("trezentos e vinte e um"). Between two classes, "e" is required before a last group that is below a hundred or a round hundred. Without the "e", that group starts a new number. Before any other group, the "e" is optional.

```python
>>> read("No cheque lia-se mil duzentos euros, sem o e.")
[('mil', '1000'), ('duzentos', '200')]
>>> read("A viagem custou mil e duzentos euros.")
[('mil e duzentos', '1200')]
>>> read("O comboio transporta mil duzentos e cinquenta passageiros.")
[('mil duzentos e cinquenta', '1250')]
>>> read("O formulário dizia mil trinta páginas, sem o e.")
[('mil', '1000'), ('trinta', '30')]
>>> read("O livro tem mil e trinta páginas.")
[('mil e trinta', '1030')]
```

The same rule holds after every scale word.

```python
>>> read("A empresa faturou dois milhões e trezentos mil euros no ano passado.")
[('dois milhões e trezentos mil', '2300000')]
>>> read("O relatório escreveu dois milhões trezentos mil euros, sem o e.")
[('dois milhões', '2000000'), ('trezentos mil', '300000')]
>>> read("Plantámos um milhão duzentos mil e trezentos pinheiros.")
[('um milhão duzentos mil e trezentos', '1200300')]
```

> Gramática do Português (Fundação Calouste Gulbenkian, 2013-2020, p. 932/933), quoted in Ciberdúvidas 8981: "Liga também as duas classes mais à direita do numeral que contenham valores expressos (ou seja, com casas preeenchidas com algarismos diferentes de zero) quando a segunda termina em dois zeros [...] ou quando começa por zero [...]. Nos outros casos, a conjunção é omitida entre as classes".

> Cunha & Cintra, Nova Gramática do Português Contemporâneo (1984), p. 372, quoted in Ciberdúvidas 34389: "Não se emprega a conjunção entre os milhares e as centenas, salvo quando o número terminar numa centena com dois zeros: 1892 = mil oitocentos e noventa e dois 1800 = mil e oitocentos".

> Teyssier, Manual de Língua Portuguesa (1989), pp. 181-182, quoted in [Ciberdúvidas 31900](https://ciberduvidas.iscte-iul.pt/consultorio/perguntas/a-conjuncao-e-nos-numerais/31900): "E não figura entre os milhares e as centenas, excepto quando a mil se segue um algarismo simples, p. ex.: 4.226: Quatro mil duzentos e vinte e seis 1.400: mil e quatrocentos 1.030: mil e trinta".

> Maintainer ruling: "The 'e' is only required in the final piece; otherwise it is optional."

In Galician, the normative form writes no "e" after "mil" or "cento" ("mil novecentos e noventa", "cento un"). Text also writes "dous mil e vinte e seis", and a split reading gives a wrong value, so the "e" between groups is optional. Both forms read as one number.

```python
>>> read("A lei entra en vigor en dous mil e vinte e seis.", "gl")
[('dous mil e vinte e seis', '2026')]
>>> read("en dous mil vinte e seis", "gl")
[('dous mil vinte e seis', '2026')]
```

> Maintainer ruling: "be lenient and read 'mil e' as one number"

In English, "and" is optional between groups and after "hundred". Both forms read the same number.

```python
>>> read("The war ended in two thousand and one.", "en")
[('two thousand and one', '2001')]
>>> read("The war ended in two thousand one.", "en")
[('two thousand one', '2001')]
>>> read("The book has one hundred and one pages.", "en")
[('one hundred and one', '101')]
```

> CLDR 49 RBNF en: %spellout-cardinal writes no "and" ("100: << hundred[ >>];", "1000: << thousand[ >>];") and %spellout-cardinal-verbose writes one before a last group below 100.

> Wikipedia, "English numerals": in American English "many students are taught [...] not to use the word and anywhere in the whole part of a number, so it is not used before the tens and ones"; "Despite this rule, some Americans use the and in reading numbers containing tens and ones as an alternative".

## A comma between classes

In Portuguese, a comma after a scale word and before a number word links two classes of one number. The classes go from the largest down, so the class after the comma is smaller: "2 mil, milhões de pessoas" is 2000 and then a noun phrase. The joiner rule still holds after the comma: a round last group needs "e", so a comma before it ends the number.

```python
>>> read("O cheque era de dois milhões, duzentos e trinta e seis mil trezentos e vinte e um euros.")
[('dois milhões, duzentos e trinta e seis mil trezentos e vinte e um', '2236321')]
>>> read("Dos dois milhões, trezentos mil foram para impostos.")
[('dois milhões', '2000000'), ('trezentos mil', '300000')]
```

> Gramática do Português (Fundação Calouste Gulbenkian, 2013-2020, p. 932/933), quoted in Ciberdúvidas 8981: "Nos outros casos, a conjunção é omitida entre as classes [ex. 2 236 321 – dois milhões, duzentos e trinta e seis mil trezentos e vinte e um]". The same page: "é costume os milhões e os milhares serem simplesmente separados com vírgula, ficando o e subentendido".

In English, a comma after a scale word also links the next class, when that class is a hundred or more. Before a smaller group the comma ends the number, because English writes "and" there, not a comma.

```python
>>> read("The city has one million, two hundred thousand people.", "en")
[('one million, two hundred thousand', '1200000')]
>>> read("They printed two thousand, five of which were signed.", "en")
[('two thousand', '2000'), ('five', '5')]
```

> Wikipedia, "English numerals", the table of spoken forms: "One thousand, two hundred (and) twenty-five" for 1225, "One thousand, nine hundred" for 1900, and "One thousand (and) fifty" for 1050, with no comma before a group below a hundred.

## A count before a larger scale noun

Only "mil" or "thousand" counts a larger scale noun: "mil milhões" is 10^9. A count with "e" after "mil" counts the noun only when the count is well formed. In Portuguese the last group after "mil e" is below a hundred or a round hundred. In English the last group after "thousand and" is below a hundred.

```python
>>> read("O estádio custou mil e quinhentos milhões de euros.")
[('mil e quinhentos milhões', '1500000000')]
>>> read("O país deve dois mil e trezentos milhões.")
[('dois mil e trezentos milhões', '2300000000')]
>>> read("Escreveu mil e cento e vinte milhões.")
[('mil', '1000'), ('cento e vinte milhões', '120000000')]
>>> read("The debt is two thousand five hundred million.", "en")
[('two thousand five hundred million', '2500000000')]
>>> read("The debt is two thousand and five hundred million.", "en")
[('two thousand', '2000'), ('five hundred million', '500000000')]
```

A scale noun closes its group, so "milhão" counts no larger noun.

```python
>>> read("Gastou um milhão e dois bilhões.", "pt-BR")
[('um milhão', '1000000'), ('dois bilhões', '2000000000')]
```

> Gramática do Português (Fundação Calouste Gulbenkian, 2013-2020, p. 932/933), as quoted for joiner_before_last_group: "e" joins the two rightmost classes "quando a segunda termina em dois zeros [...] ou quando começa por zero".

> CLDR 49 RBNF en: "%%and: 1: ' and =%spellout-cardinal-verbose=; 100: ' =%spellout-cardinal-verbose=;"

## A scale noun agrees with its count

In Portuguese, a scale noun agrees in number with its count. A singular "milhão", "bilião" or "bilhão" takes only the count one, so a larger count before it is a separate number. A plural noun takes no count of one or of a half in words, so "meio milhões" and "um milhões" are not one number. A lone "meio" keeps its own reading, a fraction with `Reason.HOMOGRAPH`, as in "no meio da sala". "um milhões" gives no mention. Digits do not agree, so "1 milhões" stays one million. English keeps the singular after any count.

```python
>>> read("Doaram cem mil e um milhão de euros.")
[('cem mil', '100000'), ('um milhão', '1000000')]
>>> read("Contaram mil e um milhões de estrelas.")
[('mil e um milhões', '1001000000')]
>>> [(m.text, m.value, m.confidence) for m in tag_numbers("meio milhões de pessoas", "pt-PT")]
[('meio', '0.5', 0.4)]
>>> read("um milhões de pessoas")
[]
>>> read("The town got two million dollars.", "en")
[('two million', '2000000')]
```

> Squarisi, "Milhão, milhar e mil — concordância", Blog da Dad, Correio Braziliense: "Milhão é substantivo masculino. O numeral ou o adjetivo que o modifica deve concordar com ele: dois milhões de pessoas, duzentos milhões de estrelas, o milhão de dólares".

> Wiktionary, "million", usage notes: "Until the early 20th century, million behaved much like an ordinary quantificational noun".

## Collectives

A collective noun ("dúzia", "dezena", "centena", "dozen", "score") takes a count and ends its number. Its count is the whole cardinal before it, so "mil e duas dúzias" is 1002 × 12. After a scale noun, the collective counts only its own group, because the noun closes the group before it.

```python
>>> read("Encomendámos mil e duas dúzias de ovos.")
[('mil e duas dúzias', '12024')]
>>> read("Vendeu um milhão e duas dúzias de rosas.")
[('um milhão e duas dúzias', '1000024')]
>>> read("Pediu uma dúzia e duas mil dúzias de pastéis.")
[('uma dúzia', '12'), ('duas mil dúzias', '24000')]
```

A collective of a place value ("dezena", "centena") after "mil e" counts only the group after the joiner. Without the joiner, a count and a collective after a scale numeral start a new number.

```python
>>> read("Vieram treze mil e duas centenas de pessoas.")
[('treze mil e duas centenas', '13200')]
>>> read("Vieram treze mil duas centenas de pessoas.")
[('treze mil', '13000'), ('duas centenas', '200')]
>>> read("Compraram mil duzentas dúzias de ovos.")
[('mil', '1000'), ('duzentas dúzias', '2400')]
```

The count starts a new number also where the joiner rule lets a group follow with no "e". "mil duzentas e três" is one number, 1203, but before a collective the count "duzentas e três" starts a new number.

```python
>>> read("Compraram mil duzentas e três dúzias de ovos.")
[('mil', '1000'), ('duzentas e três dúzias', '2436')]
```

The joiner rule decides where the number ends before a collective. A round last class such as "duzentos mil" needs "e" after "um milhão". Without the "e", the class and its collective start a new number.

```python
>>> read("O armazém recebeu um milhão duzentos mil dúzias de ovos.")
[('um milhão', '1000000'), ('duzentos mil dúzias', '2400000')]
>>> read("O armazém recebeu um milhão e duzentos mil dúzias de ovos.")
[('um milhão e duzentos mil dúzias', '3400000')]
```

The ovos-number-parser pt test suite expects 3400000 for "um milhão duzentos mil dúzias", with no "e". When ovos-number-parser reads Portuguese through numtag, that test row changes to the two numbers above.

Source: maintainer ruling.

"de" and a plural collective or scale noun multiply a collective. A singular class noun after "de" names that class.

```python
>>> read("Comprou uma dúzia de dúzias de ovos.")
[('uma dúzia de dúzias', '144')]
>>> read("Chegaram duas dezenas de milhar de pessoas.")
[('duas dezenas de milhar', '20000')]
>>> read("Comeu um terço de dúzia de ovos.")
[('um terço de dúzia', '4')]
```

> Priberam, "milhar", sense 3: "Ordem ou grupo de algarismos intermédio às unidades e aos milhões."

> Priberam, "dúzia", sense 1: "Conjunto de doze."

English joins classes with no "and", so a count and a collective after "thousand" belong to the number: the collective counts the whole cardinal. After "million" and larger the collective counts only the class after the noun, as after "milhão".

```python
>>> read("They packed one thousand twenty-four dozen eggs.", "en")
[('one thousand twenty-four dozen', '12288')]
>>> read("They packed one million three hundred thousand dozen eggs.", "en")
[('one million three hundred thousand dozen', '4600000')]
```

> CLDR 49 RBNF en %spellout-cardinal: "1000: << thousand[ >>];", "1000000: << million[ >>];"

In English, "score" takes a cardinal after "and".

```python
>>> read("Four score and seven years ago our fathers brought forth a nation.", "en")
[('Four score and seven', '87')]
```

> Wiktionary, "dozen", noun: "A set of twelve"; "score", noun: "Twenty (20)".

## Halves

"e meio" after a scale noun adds half of that noun. After a collective it adds half of the collective. After a small number it adds a half of one.

```python
>>> read("Venderam um milhão e meio de bilhetes.")
[('um milhão e meio', '1500000')]
>>> read("Comprei dúzia e meia de ovos.")
[('dúzia e meia', '18')]
>>> read("A medição deu mil e meio.")
[('mil e meio', '1000.5')]
>>> read("Juntou cem e meia dúzia de cromos.")
[('cem e meia dúzia', '106')]
>>> read("Two and a half million people voted.", "en")
[('Two and a half million', '2500000')]
>>> read("The deal was worth 2 and a half million dollars.", "en")
[('2 and a half million', '2500000')]
```

Source: maintainer ruling for the half of a scale noun, and Priberam for the half dozen:

> Priberam, "dúzia": "meia dúzia": "Conjunto de seis.".

A half before a noun that it halves is not part of the number before it. "uma hora e meia" is a duration: one hour and a half hour. numtag gives the two numbers, and a date library reads the duration. This reading is a maintainer ruling. A half before a unit of measure is half of that unit.

```python
>>> read("Esperou uma hora e meia.")
[('uma', '1'), ('meia', '0.5')]
>>> read("Pesou um milhão e meio quilo.")
[('um milhão', '1000000'), ('meio', '0.5')]
```

> Dicio, "Meio-dia e meio ou meio-dia e meia": "A palavra meia é um numeral fracionário e se refere à metade de um todo, de uma unidade. Sendo um numeral fracionário, deverá estabelecer concordância com a unidade fracionada".

A half after a small cardinal joins it: "às três e meia" is 3.5. No outside source covers a half after a small cardinal, so this reading is structural. A clock reader takes the hour and the half from the words.

```python
>>> read("Saímos às três e meia.")
[('três e meia', '3.5')]
```

## Ranges after "entre" and "between"

After a range cue, the first number ends at a joiner that splits the words into two complete numbers, the first one smaller.

```python
>>> read("O prémio fica entre cem mil e um milhão de euros.")
[('cem mil', '100000'), ('um milhão', '1000000')]
>>> read("O custo fica entre cinco mil e sessenta e sete milhões.")
[('cinco mil', '5000'), ('sessenta e sete milhões', '67000000')]
>>> read("The prize is between five hundred thousand and two million dollars.", "en")
[('five hundred thousand', '500000'), ('two million', '2000000')]
```

With no cue, the same words can read as one number.

```python
>>> read("O custo foi de cinco mil e sessenta e sete milhões.")
[('cinco mil e sessenta e sete milhões', '5067000000')]
```

> Priberam, "entre", sense 3: "Indica situação entre duas ou mais coisas, duas ou mais ideias, dois ou mais conceitos, etc."

> Wiktionary, "between", sense 1: "In the position or interval that separates (two things), or intermediate in quantity or degree".

## The tie-break between splits

Where the same words split into two numbers at more than one joiner, the split with the fewest significant digits wins. When two splits tie, the longer first number wins. A split inside a number below a thousand wins only with fewer digits. The same rule picks the split after a range cue, and a range cue never reads worse than the same words with no cue. This rule is structural, with no outside source: the limits of a range are most often round numbers.

```python
>>> read("Foram mil milhões e mil e quinhentos milhões.")
[('mil milhões', '1000000000'), ('mil e quinhentos milhões', '1500000000')]
>>> read("Gastou dois milhões e mil e três milhões.")
[('dois milhões e mil', '2001000'), ('três milhões', '3000000')]
>>> read("O valor fica entre dois milhões e quinhentos mil e três milhões.")
[('dois milhões e quinhentos mil', '2500000'), ('três milhões', '3000000')]
>>> read("The fee is between two thousand and one hundred and fifty thousand dollars.", "en")
[('two thousand', '2000'), ('one hundred and fifty thousand', '150000')]
```

In the first example, 1 + 2 significant digits beat the split 1000001000 and 500000000, with 7 + 1. In the second, both splits have 5 significant digits, so the longer first number wins.

## The leftmost longest number

At each position numtag takes the longest number. Where a number can still grow by a plain group, it takes the group, and a later count starts the next number. With nothing before it, a compound count reads as one number. A number ends where no rule takes the next word.

```python
>>> read("Foram um milhão e quinhentos mil e dois milhões.")
[('um milhão e quinhentos mil', '1500000'), ('dois milhões', '2000000')]
>>> read("Foram duzentos mil e dois milhões.")
[('duzentos mil e dois milhões', '200002000000')]
>>> read("twenty one twenty", "en")
[('twenty one', '21'), ('twenty', '20')]
>>> read("um um um")
[('um', '1'), ('um', '1'), ('um', '1')]
```

No rule joins "um" to "um", so each word is a number. This rule is structural, with no outside source.

## Decimals

A decimal marker ("vírgula", "point") or a decimal mark in digits ("2,5", "2.5") starts the fraction part. Each word after the marker gives its own digits. Where the words split in more than one way, the reading with the fewest parts wins.

```python
>>> read("O bebé pesa dois vírgula cinco quilos.")
[('dois vírgula cinco', '2.5')]
>>> read("O valor de pi é três vírgula um quatro.")
[('três vírgula um quatro', '3.14')]
>>> read("The rate is three point twenty five.", "en")
[('three point twenty five', '3.25')]
```

> CLDR 49 RBNF pt_PT and pt %spellout-cardinal-masculine: "x.x: << vírgula >>;"; Priberam, "vírgula", sense 2: "[Matemática] Sinal gráfico (,) que serve para separar os números inteiros das fracções decimais."

> Wiktionary, "point", noun sense 1.3: "A decimal point".

A marker word with no number before it starts no fraction part: it is a noun. So digits after it keep their count of parts. With a number before the marker, the digits are decimal digits and count no parts.

```python
>>> read("At that point 3 quarters of the votes were counted.", "en")
[('3 quarters', '0.75')]
>>> read("two point 5 quarters", "en")
[('two', '2'), ('5', '5')]
```

Where the comma marks decimals, the word for the point is no decimal marker. So "o artigo 5 ponto 3" is two numbers, and so are "cinco ponto três", Galician "5 punto 3", Mirandese "5 ponto 3", Asturian "5 puntu 3" and German "Artikel 5 Punkt 3". English writes decimals with a point, so "2 point 5" stays one decimal.

```python
>>> read("Leia o artigo 5 ponto 3 e o artigo cinco ponto três.")
[('5', '5'), ('3', '3'), ('cinco', '5'), ('três', '3')]
>>> read("Turn it up 2 point 5.", "en")
[('2 point 5', '2.5')]
```

> Manual de Comunicação do Senado Federal, "Números": "Use vírgula para o decimal."

Spanish writes either mark, so "punto" stays a decimal marker: "dos punto cinco" is 2.5. The Ortografía (2010) recommends the point, and much of Latin America writes and says it. "el apartado 3 punto 2" reads 3.2, and that is the known cost.

```python
>>> read("El valor es dos punto cinco, o dos coma cinco.", "es")
[('dos punto cinco', '2.5'), ('dos coma cinco', '2.5')]
```

> RAE-ASALE, Diccionario panhispánico de dudas, 2.ª edición, "punto": "En algunas áreas hispanohablantes, separa la parte entera de la parte decimal en los números escritos con cifras: π = 3.1416… En España y amplias zonas de América se usa para ello la coma (→ coma2, 5): π = 3,1416… Ambas opciones son válidas de acuerdo con la normativa internacional."

> Sociedad Española de Astronomía, "¿Punto o coma?": "hasta 2010 recomendaban la coma (Diccionario panhispánico de dudas, 2005) mientras que ahora recomiendan el punto".

Indonesian keeps "titik" for the same reason. CLDR spells a point decimal with it, and Indonesian text writes both marks. So "di 3 titik 5 orang" reads 3.5.

> CLDR 48 RBNF (ICU 78) id %spellout-cardinal: "x.x: << titik >>;"

Digits after a decimal marker are the decimal digits only when no part word follows them. Before a power of ten they are its numerator, as words are: Russian "2 целых 5 сотых", Czech "2 celé 5 setin", Slovene "2 celi 5 stotink" and Croatian "2 cijela 5 stotinki" are 2.05. Before any other part word they are no decimal digits, so "2 целых 3 пятых" is no 2.3.

```python
>>> read("Ответ: 2 целых 5 сотых.", "ru")
[('2 целых 5 сотых', '2.05')]
>>> read("Rezultat je dve celi pet stotink.", "sl")
[('dve celi pet stotink', '2.05')]
```

> Slovar slovenskega knjižnega jezika (SSKJ², Fran), "stotinka" (knowledge/wiki/audits/numtag/follow-up-prs/sources/sl/fran-stotinka.txt): "del na sto enakih delov razdeljene merske enote", "mat. ena cela, pet stotink 1,05"

Where the comma marks decimals, a point between digits groups thousands. A point that cannot group digits marks decimals: the group after it does not have three digits, or the number before it is 0. A time of day also takes a point, so an hour from 0 to 23 with minutes from 00 to 59 reads no number, and so does "24.00". A day and a month with a period after them are a date ("24.12."), and they read no number. A decimal with that shape at the end of a sentence ("Es sind 2.5.") reads no number for the same reason. A space group before a point and digits is one number, as in SI Brochure 5.4.4 ("43 279.168 29"): "1 234.5" reads 1234.5, "1 234.567" reads 1234.567 and "-1 234.5" reads -1234.5. Two group marks cannot both group thousands, so the point is the decimal. A locale's own group mark before a point decimal reads the same way, whether the mark is a space, a no-break space or an apostrophe: "1 234.5" in Finnish (a plain space, the Finnish lexicon mark), "10 123.5" in Russian (a no-break space) and "1'234.5" in Swiss French read 1234.5, 10123.5 and 1234.5. Where a point is the group mark (Portuguese, German), a second point is no decimal mark, so "1.234.5" reads no number. Without a space group, a point and three digits stay a thousands mark: "1.500" reads 1500. A space group is one to three digits and a single space before the next group, so "em 2024 123.45 euros" and "entre 10-123.5 kg" read 123.45 and 123.5. A sign before the first group keeps the group, and a signed number continues no group ("12 -123.5" reads 12 and -123.5). A hyphen joins no group, so "120-160" reads 120 and 160.

```python
>>> read("Custa 1.5 milhões, e pi é 3.14159.")
[('1.5 milhões', '1500000'), ('3.14159', '3.14159')]
>>> read("Pesa 0.500 kg e custa 1.500 euros.")
[('0.500', '0.5'), ('1.500', '1500')]
>>> read("Gegen 11.29 Uhr zog der Protest los.", "de")
[]
>>> read("Am 24.12. ist Heiligabend.", "de")
[]
>>> read("Preis: 1'234.5 CHF", "fr-CH")
[("1'234.5", '1234.5')]
```

> Unicode CLDR (cldr-json, cldr-numbers-full/main/<locale>/numbers.json, "symbols-numberSystem-latn"), "group": U+00A0 in bg, et, fi, hu, kab, nb, nn, pl, ru, sk, sv and uk; U+202F in fr and fr-BE; the apostrophe in fr-CH; the decimal symbol is a comma in each. BIPM, SI Brochure, 9th edition, 5.4.4: no dot or comma is ever inserted in the spaces between groups.

> BIPM, SI Brochure, 9th edition, 5.4.4: the decimal marker "shall be either the point on the line or the comma on the line." "The decimal marker chosen should be that which is customary in the language and context concerned." "If the number is between +1 and −1, then the decimal marker is always preceded by a zero."

> Wikipedia, "Date and time representation by country": "In Finland and Indonesia, the common separator between hours and minutes is a dot (18.45, for example)." de.wikipedia, "Uhrzeit": the Swiss Federal Chancellery says "zwischen den Stunden und den Minuten ein Punkt und kein Doppelpunkt verwendet werden". en.wikipedia, "Date and time notation in Finland": "When the year is not specified, a trailing full stop is used", "20.10 represents 8:10 pm and 20.10. represents 20 October."

The fraction part follows the grammar of the whole part. A hundreds word never follows another part, as "cem" never follows units in a cardinal. So the decimal ends before it. This rule is structural, with no outside source.

```python
>>> read("zero vírgula vinte e cinco cem")
[('zero vírgula vinte e cinco', '0.25'), ('cem', '100')]
>>> read("zero vírgula dois cinco")
[('zero vírgula dois cinco', '0.25')]
```

A multiplier after a decimal multiplies it, as a scale word does.

```python
>>> read("one point two hundred", "en")
[('one point two hundred', '120')]
>>> read("Sales hit one point two million units.", "en")
[('one point two million', '1200000')]
>>> read("um vírgula dois mil")
[('um vírgula dois mil', '1200')]
```

> Wikipedia, "English numerals": a decimal is read "as a cardinal number, followed by", then "point", "and then by the digits of the fractional part". 1.2 million is "one point two million".

A mark right before the first digit is a decimal mark, because a group mark stands only between digits. An ellipsis is not a decimal mark.

```python
>>> read("A taxa é de ,5 por cento e o resto ...5.")
[(',5', '0.5'), ('5', '5')]
>>> read("The rate is .5 percent.", "en")
[('.5', '0.5')]
```

## Ordinals

An ordinal scale word multiplies only the last group of the number before it. The larger groups before that add. Where the product does not fit after the groups before it, the ordinal starts a new number.

```python
>>> read("He was the two million three hundred thousandth customer.", "en")
[('two million three hundred thousandth', '2300000')]
>>> read("six thousand two hundredth", "en")
[('six thousand two hundredth', '6200')]
>>> read("one thousand two thousandth", "en")
[('one thousand two', '1002'), ('thousandth', '1000')]
>>> read("dois milhões e trezentos milésimo")
[('dois milhões e trezentos milésimo', '2300000')]
```

> CLDR 49 RBNF en %spellout-ordinal: "100: <%spellout-numbering< hundred[ >>|th];", "1000: <%spellout-numbering< thousand[ >>|th];".

In Portuguese every word of an ordinal is ordinal, and a cardinal count before "milésimo" multiplies it. In English only the last word is ordinal.

```python
>>> read("Ficou em vigésimo primeiro lugar.")
[('vigésimo primeiro', '21')]
>>> read("O dois milésimo visitante ganhou.")
[('dois milésimo', '2000')]
>>> read("It was the twenty-first day.", "en")
[('twenty-first', '21')]
```

Source: CLDR 49 RBNF pt and pt_PT, %spellout-ordinal-masculine, rule `2000: <%spellout-cardinal-masculine< milésimo[ >>];`. A cardinal count before "milésimo" multiplies it.

In English "one hundredth" is a fraction or an ordinal. After "the" it is the ordinal. With no article it is the fraction.

```python
>>> read("We celebrated the one hundredth anniversary.", "en")
[('one hundredth', '100')]
>>> read("Each coin is worth one hundredth of a dollar.", "en")
[('one hundredth', '0.01')]
```

> Wikipedia, "English numerals": "In spoken English, ordinal numerals and partitive numerals are identical with a few exceptions. Thus 'fifth' can mean the element between fourth and sixth, or the fraction created by dividing the unit into five pieces".

## Fractions

A count and a denominator make a fraction. "avos" joins only a denominator above ten, so "dez avos" is no fraction. A fraction word after "e" adds that part of one.

```python
>>> read("Cada herdeiro recebe um doze avos.")
[('um doze avos', '1/12')]
>>> read("A resposta é doze vinte e cinco avos.")
[('doze vinte e cinco avos', '0.48')]
>>> read("Escreveu dez avos no quadro.")
[('dez', '10')]
>>> read("Ganhou dois milhões e quarto.")
[('dois milhões e quarto', '2000000.25')]
```

> Priberam, "avo", [Matemática]: "Palavra que se junta a um denominador maior que dez para indicar a divisão da unidade no número de partes iguais indicado por esse denominador (ex.: doze vinte e cinco avos = 12/25)."

"quinto", "sexto" and "décimo" are both a denominator and an ordinal. After "um" or "uma", the word after them decides. As a fraction the word is a noun, and "de" or a contraction of "de" joins its complement, so the fraction stays. Any other word is the noun that the ordinal adjective orders: "um quinto andar" is the fifth floor. At the end of the text, or before punctuation or a joiner, the fraction stays. An ordinal before "parte" qualifies the part, so "a décima parte" is a tenth.

```python
>>> read("Recebeu um quinto da herança.")
[('um quinto', '0.2')]
>>> read("Comprou um quinto andar em Lisboa.")
[('um', '1'), ('quinto', '5')]
>>> read("Recebeu a décima parte do valor.")
[('décima parte', '0.1')]
```

> Priberam, "quinto": "adjectivo numeral e nome masculino 1. Que ou o que numa série vem logo depois do quarto. nome masculino 2. Quinta parte."; "de": "Une ao nome o seu complemento (ex.: folha de papel)". Ciberdúvidas 33764: "No primeiro caso, estamos em presença de um adjetivo numeral que qualifica parte; no segundo caso, em presença de um nome."

A verb after "um quinto" also makes the ordinal, so an ordinal read this way has the low score of a word with a second meaning: "Um décimo sobreviveu." reads the ordinal 10 at that score.

A Hungarian part word of a hundred or more, written as one word with its count and with no count before it, is one part of the product: "háromszázad" is 1/300, as "háromszáz" is 300. hu.wikipedia uses it so in "háromszázad része a klórénak". By AkH 12 §293 the glued form is also a count of parts before a noun, so "háromszázad másodperc" can be 3/100. That reading is the documented alternative. The reader gives the frequent multiplier reading at the low score of a word with a second meaning. A number or "egész" before the word leaves the word to the readings that take that count, so "egy kétszázad" is 1/200 and "3 tízezred" is 3/10000, as "három tízezred" is. A hyphen before it ends a range.

```python
>>> read("A mennyisége körülbelül háromszázad része a klórénak.", "hu")
[('háromszázad', '1/300')]
>>> read("Az atommag az atom méretének tízezred része.", "hu")
[('tízezred', '0.0001')]
>>> read("Egy kétszázad milliméter vastag.", "hu")
[('Egy kétszázad', '0.005')]
```

> hu.wikipedia, Bróm: "háromszázad része a klórénak". hu.wikipedia, Oxigén: "kétezred részét". hu.wikipedia, Atommag: "tízezred része". hu.wikipedia, Izotópos összetétel: "százezred Å-nyi (1 fm)". hu.wikipedia, ETME: "háromezred részével". AkH 12 §293: "Ha azonban a tőszámnévi jelzős törtszámnév egészében jelzői szerepű, a két számnevet egybeírjuk, például: az ország kétharmad része, háromnegyed óra múlva".

In German a count written in one word with a part word is part of the denominator: "Zweihundertstel" is the 200th part, 1/200, as "zehntausendstel" is 1/10000. A count written apart is the numerator, so "zwei Hundertstel" is 2/100 and "drei Zweihundertstel" is 3/200. A value with no finite decimal form stays a fraction: "ein Dreitausendstel" is "1/3000". A number in digits is the numerator too, so "3 Zweihundertstel" is 3/200. A decimal in words, "ein halbes" or a count of a thousand or more before the glued word has no reading that folds it in, so the word stays unread. A glued part word with no count before it can be a plural with no determiner, as in "wertvolle Hundertstel", so it scores as a homograph.

```python
>>> read("Aber der Grundstoff für Bier mache gerade mal ein Zweihundertstel des Endpreises aus.", "de")
[('ein Zweihundertstel', '0.005')]
>>> read("ein Dreitausendstel", "de")
[('ein Dreitausendstel', '1/3000')]
>>> read("zwei Hundertstel", "de")
[('zwei Hundertstel', '0.02')]
>>> read("3 Zweihundertstel", "de")
[('3 Zweihundertstel', '0.015')]
```

> Wiktionary de, "Zehntausendstel": "der zehntausendste Teil von etwas", "Als Bruchzahl ist ein ''Zehntausendstel'' <sup>1</sup>/<sub>10000</sub> und als Kommazahl 0,0001."; DWDS, "Zehntausendstel": "das sind fünf Zehntausendstel Millimeter".

A Basque part word takes the ending -(r)en on the cardinal, so "hamarren" is a tenth and "milaren" a thousandth. "erdi", "heren" and "laurden" are the irregular forms for 2, 3 and 4. A count before the word gives the parts, and "bat" after it gives one part. "zati" between two cardinals reads "a/b" aloud. After "milioi", the part word makes one compound noun with it, so "milioi erdi" is half a million with or without "bat". The -(r)en word alone is also a genitive ("bosten artean", among five), so it reads no number with no count and no "bat".

```python
>>> read("Zortzi hamarren falta dira.", "eu")
[('Zortzi hamarren', '0.8')]
>>> read("Hiru zati lau idatzi du.", "eu")
[('Hiru zati lau', '0.75')]
>>> read("Milioi erdi euro eman zituen.", "eu")
[('Milioi erdi', '500000')]
```

> Euskaltzaindia, 203. araua, EBO (VI), "Zenbakizko adierazpenak", 6: "Zenbakitzailea bat zenbakia denean (a = 1 denean) eratzen diren zenbakiak izendatzeko, -(r)en eransten zaio zenbaki kardinalari"; "7/8: zazpi zortziren", "8/10: zortzi hamarren", "2/100: bi ehunen"; footnote 22: "3/2 = hiru erdi (hiru *biren)"; "(egokia) 3/4 hiru zati lau (edo hiru laurden)"; note 28: "Izendatzailea milioi bat denean, milioi izena erabiltzen da, ondoren bat erantsi gabe, eta izen-izen erako hitz-elkarte arrunta eratzen da (ordu(-)laurden, final(-)laurden hitzetan bezala)".

"laurden" and "heren" with no count, no article and no "bat" are one part, at the low score of a word with a second meaning. "final laurden" is the quarter-final, and "heren" is also the old ordinal "third". A noun before the word is no part of the number, as in "ordu laurden" (a quarter of an hour). After "eta" with no number before it, the word adds a quarter to an hour of the clock, which is no number word, so "hirurak eta laurden" reads no number.

```python
>>> read("Ordu laurden barru iritsiko da.", "eu")
[('laurden', '0.25')]
>>> read("Hirurak eta laurden dira.", "eu")
[]
```

> Euskaltzaindiaren Hiztegia, "laurden": "Lau zati berdinetan banatu den zerbaiten zati bakoitza."; "final laurden": "Finalerdien aurretik jokatzen diren lau partida edo norgehiagoketako bakoitza."; "heren": "Hiru zati berdinetan banatu den zerbaiten zati bakoitza.", "Hirugarrena. Heren egunean piztu zen".

## A fraction of a scale word

A fraction word, "de" or "of", and a singular scale noun make that part of the scale noun. "um quarto de milhão" is a quarter of 1000000, so it is one number, 250000. The article of the scale word may stand before it. A part that is no whole number reads as a fraction. "um quarto" alone keeps the low score of a word with a second meaning (a room), but before "de milhão" it is sure. A plural scale word, a scale numeral such as "mil", or a scale word that starts a longer number ("mil milhões", "milhar de milhões", "um milhão e meio") gives no product, and so does a count after "de": "um quarto de dois milhões" is two numbers.

```python
>>> read("Calcularam um quarto de milhão de euros.")
[('um quarto de milhão', '250000')]
>>> read("Pagaram dois terços de um milhão de euros.")
[('dois terços de um milhão', '2000000/3')]
>>> read("Perdeu um quarto de hora.")
[('um quarto', '0.25')]
>>> read("He inherited a quarter of a million pounds.", "en")
[('a quarter of a million', '250000')]
>>> read("There were three quarters of a million votes.", "en")
[('three quarters of a million', '750000')]
```

> Priberam, "quarto", nome masculino: "Cada uma das quatro partes iguais em que se divide a unidade; quarta parte de um todo." Cambridge Dictionary, "quarter" (fourth part): "one of four equal or almost equal parts of something"; example: "He inherited a quarter of a million pounds on his mother's death".

A half before "de" is no part of the scale word: "no meio de um milhão de pessoas" says "in the middle", so "meio" stays a separate word. "half a million" and "meio milhão" have their own rule.

## A joiner prefix before a number

In Hebrew and Arabic, the conjunction "and" is one letter, ו in Hebrew and و in Arabic, written joined to the next word. A joiner inside a number stays in the span: "עשרים ושלוש" is 23. A joiner before the first word of a number is no part of it, so the span starts after the letter. A one-letter article or preposition glued to a number word ("בשלושה") stays in the span of that word.

```python
>>> read("עשרים ושלוש", "he")
[('עשרים ושלוש', '23')]
>>> read("קניתי ספר ועשרה עטים", "he")
[('עשרה', '10')]
>>> read("בשלושה ימים", "he")
[('בשלושה', '3')]
>>> read("ובשלושה ימים", "he")
[('בשלושה', '3')]
>>> read("بين 15 و20 درجة", "ar")
[('15', '15'), ('20', '20')]
```

> CLDR RBNF, common/rbnf/he.xml: "1: ו=%spellout-numbering=;", "2: ושתיים;": ו is written joined to the next word. en.wiktionary "و", usage notes: "Arabic conjunctions and prepositions that have only one letter, such as وَ ( wa ) , are written as a prefix."

## The group mark follows CLDR, with four exceptions

A lexicon's `group_mark` is the CLDR group symbol of its language, and `tests/test_group_marks.py` checks every language against it. Estonian, Finnish, Hungarian, Norwegian and Swedish write a no-break space (U+00A0), and a plain space also reads through `space_groups`.

Czech, Galician, Occitan and European Portuguese keep the dot, although CLDR gives U+00A0 for all four. Written text in these languages groups digits with a dot ("1.500" is 1500), and a no-break space group mark would stop that reading. Brazilian Portuguese needs no exception: CLDR "pt" gives the dot.

> CLDR 48 numbers, gl (latn): decimal ",", group " "; the dot groups digits as in es and pt-PT ("1.000.000"), as ovos-number-parser reads gl.

## Words that are no number

A scale noun alone, or a plural scale noun with no count, names no number. A singular scale noun before "de" counts one.

```python
>>> read("Ganhou o milhão.")
[]
>>> read("Havia milhões de pessoas na rua.")
[]
>>> read("Chegou um milhão de pessoas, quase milhão de votos.")
[('um milhão', '1000000'), ('milhão', '1000000')]
>>> read("Millions of people watched.", "en")
[]
```

> Priberam, "milhão", sense 2: "[Informal, Figurado] Número ou quantidade muito grande".

A word of vague quantity right before a scale word takes the place of its count. In Croatian, "nekoliko", "puno", "više" and "mnogo" govern the genitive plural, so "nekoliko milijuna" is no number, while "milijuna" after "oko" or "više od" is the genitive singular and counts one. The `vague_quantifier` entries of the lexicon hold these words.

```python
>>> read("Prije nekoliko milijuna godina.", "hr")
[]
>>> read("Bilo ih je nekoliko stotina.", "hr")
[]
>>> read("Bilo ih je oko milijuna.", "hr")
[('milijuna', '1000000')]
>>> read("Bilo ih je više od milijuna.", "hr")
[('milijuna', '1000000')]
>>> read("Bilo ih je pet milijuna.", "hr")
[('pet milijuna', '5000000')]
```

> Hrvatski jezični portal, "više": "6. (čega) neodređena količina a. ob. veća od četiri, a manja od desetak; nekoliko [više milijuna ljudi]".

A clitic of the `vague_clitic` list may stand between the vague word and the scale word: "nekoliko je tisuća puta dalje" holds no number. The reading follows the vague word and ignores the case of the scale word, so "Puno je milijun eura" also reads no number, although "milijun" there is a singular form that counts one million. This is a known trade-off.

```python
>>> read("Najbliža zvijezda nekoliko je tisuća puta dalje od posljednjeg planeta.", "hr")
[]
>>> read("Puno je milijun eura za taj projekt.", "hr")
[]
>>> read("Do 2030 nekoliko milijuna ljudi", "hr")
[('2030', '2030')]
```

Turkish lists "birkaç", "birçok", "kaç", "onlarca", "yüzlerce", "binlerce" and "milyonlarca". Turkish writes the hundred as "yüz", a numeral that is one hundred alone, so "yüz" after a vague word also reads no number. "iki yüz" keeps its count.

```python
>>> read("Birkaç milyon kişi geldi.", "tr")
[]
>>> read("Birkaç yüz kişi geldi.", "tr")
[]
>>> read("Kaç bin kişi geldi?", "tr")
[]
>>> read("Onlarca milyon dolar harcandı.", "tr")
[]
>>> read("İki yüz kişi geldi.", "tr")
[('İki yüz', '200')]
```

> TDK Güncel Türkçe Sözlük, "birkaç": "Çok olmayan, az sayıda".

The Yazım Kılavuzu writes "birkaç" as one word. The split spelling "bir kaç" is a `number_name` and a vague phrase, so it also names no number.

```python
>>> read("Bir kaç milyon kişi geldi.", "tr")
[]
>>> read("Bir milyon kişi geldi.", "tr")
[('Bir milyon', '1000000')]
```

A hyphenated compound with a word that is not a number word is one noun, so "segunda-feira" holds no number. "dez." before a digit or a lower-case word is the abbreviation of "dezembro". At a sentence end, "dez." is ten.

```python
>>> read("Na segunda-feira chegam três.")
[('três', '3')]
>>> read("A reunião é a 3 dez. 2025.")
[('3', '3'), ('2025', '2025')]
>>> read("Os bilhetes eram dez.")
[('dez', '10')]
```

> Dicio, "Abreviaturas: lista de abreviações": "dezembro - dez.".

The hundred of a percent phrase is the percent sign, not a number: ca "per cent", fr "pour cent", it "per cento", oc "per cent", tr "yüzde", el "τοις εκατό". It is the sign after a number, after a `{slot}` that holds a number, and when the phrase stands alone. In tr the percent word comes before the number: "yüzde elli sekiz" is 58 %. With no number before it, "per" can mean "for", and the hundred counts: "Ho he venut per cent euros." At the end of the text or before "de", alone or joined to the article ("dels", "du", "degli"), the phrase can also be the percent sign with its number missing, as in "Tant per cent." There the hundred counts with `Reason.HOMOGRAPH` and the confidence 0.4. Spanish differs: a hundred is "cien" there, and "ciento" stays in percentages and idioms only, so "por ciento" has no "for a hundred" reading. With no number before it, the phrase holds no number. "cien por cien" (DPD "ciento" §3, totality) is 100 once, and only when "cien" stands alone before "por cien": "mil cien por cien" is 1100 and 100. The words after a percent phrase that follows a number start a new number: "cien por cien y cinco por ciento" is 100 and 5.

```python
>>> read("Posa el volum al cinquanta per cent.", "ca")
[('cinquanta', '50')]
>>> read("Ho he venut per cent euros.", "ca")
[('cent', '100')]
>>> read("Augmentation de six pour cent.", "fr-FR")
[('six', '6')]
>>> read("Katılım yüzde elli sekiz oldu.", "tr")
[('elli sekiz', '58')]
```

```python
>>> [(m.text, m.value, m.confidence) for m in tag_numbers("Calcula el tant per cent de descompte.", "ca")]
[('cent', '100', 0.4)]
>>> read("Calcula el tanto por ciento de descuento.", "es")
[]
>>> read("La humedad está al cien por cien.", "es")
[('cien', '100')]
```

> DPD "ciento" §2: "en la lengua actual se prefiere claramente la forma apocopada cien"

> TDK Güncel Türkçe Sözlük, "yüzde" 2: "Herhangi bir sayı ile kullanıldığında yüze bölünen bir şeyin o kadarlık parçasını belirten bir söz"

The word for one before a percent phrase counts the hundredths, so it is never the article. "un pour cent" is 1 %, and the mention has no reason.

```python
>>> [(m.text, m.value, m.reasons) for m in tag_numbers("Mets le volume à un pour cent.", "fr-FR")]
[('un', '1', frozenset())]
```

> DIEC2, "per" 2, prep.: "Indica: [...] b) Proporció. El deu per cent dels guanys."

> DIEC2 "per" 2 1 f): "Allò en lloc de què, en comptes de què, en bescanvi de què, al preu de què, en nom de què."

> DIEC2 "percentatge": "Tant per cent."

> TLFi, "cent": "Pour cent unités. Abrév. % (cf. pourcentage). Augmentation de six pour cent; taux d'intérêt de trois pour cent par an."

"menos" before a number makes it negative, except in idioms such as "pelo menos" and "mais ou menos". "meios" is a noun in "meios de pagamento", so it gives no fraction.

```python
>>> read("A temperatura desceu para menos quarenta e dois graus.")
[('menos quarenta e dois', '-42')]
>>> read("Precisa de pelo menos dois dias.")
[('dois', '2')]
>>> read("Aceitamos dois meios de pagamento.")
[('dois', '2')]
```

Some number words are also a noun that a count takes. Right after a sure cardinal, such a word is that noun: Hungarian "öt hét" is five weeks, and French "dix secondes" is ten seconds. The language lists these words. French "premier" and "second" are never the last word of a longer ordinal, so "dix premiers" is 10 and 1st, not 11th.

```python
>>> read("Öt hét múlva jövök vissza.", "hu")
[('Öt', '5')]
>>> read("Attendez dix secondes avant de recommencer.", "fr")
[('dix', '10')]
>>> read("Les dix premiers arrivés gagnent un prix.", "fr")
[('dix', '10'), ('premiers', '1'), ('un', '1')]
```

> Wikipedia, "Hungarian noun phrase": "Therefore, the plural is not used with numerals or quantity expressions." TLFi (CNRTL), "second": "Second et deuxième peuvent être empl. l'un à la place de l'autre, sauf dans les syntagmes figés, les loc. et les adj. numéraux ordinaux comp. (où second n'est jamais empl.)".

---
[← Confidence and homographs](confidence-and-homographs.md) · [Home](index.md) · [Portuguese →](languages/pt.md)
