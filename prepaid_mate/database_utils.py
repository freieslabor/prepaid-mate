from datetime import datetime


def pformat_cents(
        cents: int,
        show_sign: bool = False,
        html: bool = False,
) -> str:

    string: str = f'{cents/100:1.2f}€'

    if show_sign and cents > 0:
        string = f'+{string}'

    if html:
        color: str = ''

        if cents > 0:
            color = 'green'

        elif cents < 0:
            color = 'red'

        string = f'<span style="color: {color}">{string}</span>'

    return string


def pformat_timestamp(timestamp: int) -> str:
    return str(datetime.fromtimestamp(timestamp))
