import random
import string

def generate_password(length=8, use_digits=True, use_symbols=True):
    characters = string.ascii_letters
    if use_digits:
        characters += string.digits
    if use_symbols:
        characters += string.punctuation

    password = ''.join(random.choice(characters) for _ in range(length))
    return password
"Added Task 3: Random Password Generator"

if __name__ == "__main__":
    print("Random Password Generator")
    length = int(input("Enter password length: "))
    use_digits = input("Include digits? (y/n): ").lower() == 'y'
    use_symbols = input("Include symbols? (y/n): ").lower() == 'y'

    pwd = generate_password(length, use_digits, use_symbols)
    print(f"Your generated password is: {pwd}")
