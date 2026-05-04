---
date: 2026-04-25
draft: true
title: Python 헷갈리는 문법
categories: python
tags:
  - python
author: grrru
---
## Annotated

```python
from typing import Annotated, get_args, get_origin


def is_positive(num: int) -> bool:
    return num > 0


MyNumber = Annotated[int, is_positive]


def main():
    my_number: MyNumber = -10

    print(my_number)  # -10
    print(type(MyNumber))  # <class 'typing._AnnotatedAlias'>
    print(get_origin(MyNumber))  # <class 'typing.Annotated'>
    print(get_args(MyNumber))  # (<class 'int'>, <function is_positive at 0x102d8c1f0>)

    base_type, validator = get_args(MyNumber)

    print(validator(my_number))  # False


main()
```
