# Values

The `value` of a mention is a string of digits. numtag never gives an `int`, a `float` or a `Decimal`. This page states the three value forms, their rules, and how a caller converts them.

## The three forms

| Form | Pattern | Examples |
|---|---|---|
| whole number | `-?[0-9]+` | `"24"`, `"-42"`, `"1000000"` |
| decimal | `-?[0-9]+\.[0-9]+` | `"2.5"`, `"0.375"`, `"-0.25"` |
| fraction | `-?[0-9]+/[0-9]+` | `"1/3"`, `"5/6"`, `"7/3"` |

Each value obeys these rules:

| Rule | Example |
|---|---|
| A whole number has no leading zero. | "007" in the text gives the value `"7"` |
| No value is "-0". | "menos zero" gives `"0"` |
| A decimal has no trailing zero after the point. | "2,50" gives `"2.5"` |
| A fraction is in lowest terms. | "dois sextos" gives `"1/3"` |
| A fraction with a finite decimal form is written as a decimal. | "três oitavos" gives `"0.375"`, "dois quartos" gives `"0.5"` |
| The decimal point is always ".", in every language. | pt "2,5" gives `"2.5"` |

```python
>>> from numtag import tag_numbers
>>> [(m.text, m.value) for m in tag_numbers("O código é 007, menos zero, 2,50, dois sextos, três oitavos e dois quartos.", "pt-PT")]
[('007', '7'), ('menos zero', '0'), ('2,50', '2.5'), ('dois sextos', '1/3'), ('três oitavos', '0.375'), ('dois quartos', '0.5')]
```

The `text` of a mention keeps the digits as written. Only the `value` is canonical.

A fraction with a zero denominator has no value: `Fraction("1/0")` raises `ZeroDivisionError`. So "1/0" gives no mention, and its digits are not read as the two numbers 1 and 0. A chain of slashes, as in a date "3/5/2025", is no fraction and keeps its digits.

```python
>>> [(m.text, m.value) for m in tag_numbers("Many proof assistants, such as Rocq and Lean, define 1/0 = 0.", "en")]
[('0', '0')]
```

> Wikipedia, "Division by zero": "Many proof assistants, such as Rocq and Lean, define 1/0 = 0."

## Convert a value

Convert a value at the point where your code needs a number. Python reads the three forms with these types:

| Type | Whole number | Decimal | Fraction |
|---|---|---|---|
| `int` | yes | no | no |
| `decimal.Decimal` | yes | yes | no |
| `fractions.Fraction` | yes | yes | yes |

`Fraction` reads every value, and it is exact. Use it when you do not know the form.

```python
>>> from decimal import Decimal
>>> from fractions import Fraction
>>> values = [m.value for m in tag_numbers("vinte e quatro, dois vírgula cinco e um terço", "pt-PT")]
>>> values
['24', '2.5', '1/3']
>>> [Fraction(v) for v in values]
[Fraction(24, 1), Fraction(5, 2), Fraction(1, 3)]
>>> int(values[0]), Decimal(values[1])
(24, Decimal('2.5'))
```

The `kind` does not tell the form of the value. A FRACTION mention can have a decimal value ("três quartos" is `"0.75"`), and a CARDINAL mention can come from a decimal ("2,5 milhões" is `"2500000"`). Test the string, or convert with `Fraction`.

## No length limit

numtag builds each value with arithmetic on digit strings: it adds, multiplies and moves the decimal point. No value passes through a Python number type, so no value loses a digit and no value has a size limit.

```python
>>> m = tag_numbers("um centilião", "pt-PT")[0]
>>> len(m.value), m.value[:4]
(601, '1000')
>>> int(m.value) == 10 ** 600
True
>>> float(m.value)
inf
```

A `float` holds about 15 significant digits. Convert to `float` only when your code accepts that loss.

```python
>>> m = tag_numbers("1.234.567.890.123.456.789,5", "pt-PT")[0]
>>> m.value
'1234567890123456789.5'
>>> Decimal(m.value)
Decimal('1234567890123456789.5')
>>> float(m.value)
1.2345678901234568e+18
```

`Decimal(value)` is exact. Arithmetic on a `Decimal` rounds to the precision of the decimal context, 28 digits by default.

## Check a value

`is_canonical_value` checks the pattern of a value string. Read [api.md](api.md#is_canonical_value).

---
[← API reference](api.md) · [Home](index.md) · [Number scale →](number-scale.md)
