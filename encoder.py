# Base62 uses these 62 characters to represent numbers
# 0-9 
# a-z 
# A-Z 

CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"



def encode(num: int) -> str:
   
    if num == 0:
        return CHARS[0]

    result = ""
    while num > 0:
        remainder = num % 62       # which character to use
        result = CHARS[remainder] + result  # prepend the character -> as we are building it right to left
        num = num // 62            # integer division, move to next digit -> gives the quotient
        

    return result


def decode(short_code: str) -> int:
   
    result = 0
    for char in short_code:
        result = result * 62 + CHARS.index(char) # finds the position of the char in the string
    return result
