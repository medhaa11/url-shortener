# Base62 uses these 62 characters to represent numbers
# 0-9 = 10 characters
# a-z = 26 characters
# A-Z = 26 characters
# Total = 62 characters
CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def encode(num: int) -> str:
    """
    Converts a database ID (integer) into a Base62 short code.

    Examples:
        encode(1)       → "1"
        encode(100)     → "1C"
        encode(5432)    → "1Cq"
        encode(1000000) → "4c92"

    How it works — same as converting to any other base:
        Take the number, divide by 62, the remainder picks a character.
        Repeat with the quotient until nothing is left.
        Build the string right to left.
    """
    if num == 0:
        return CHARS[0]

    result = ""
    while num > 0:
        remainder = num % 62       # which character to use
        result = CHARS[remainder] + result  # prepend the character -> as we are building it right to left
        num = num // 62            # integer division, move to next digit -> gives the quotient
        

    return result


def decode(short_code: str) -> int:
    """
    Converts a Base62 short code back into the original integer.
    The reverse of encode().

    Examples:
        decode("1")    → 1
        decode("1C")   → 100
        decode("1Cq")  → 5432

    You won't use this often — but it's useful for debugging
    and understanding that the encoding is completely reversible.
    """
    result = 0
    for char in short_code:
        result = result * 62 + CHARS.index(char) # finds the position of the char in the string
    return result
