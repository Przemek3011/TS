import random

def generate_bitstream(length=1200, filename="Z.txt"):
    bits = ''.join(random.choice(['0', '1']) for _ in range(length))
    with open(filename, 'w') as file:
        file.write(bits)
    print(f"Wygenerowano plik '{filename}' z losowym ciągiem bitów o długości {length}.")

if __name__ == "__main__":
    generate_bitstream()