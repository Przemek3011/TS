from warnings import warn
import warnings
from itertools import zip_longest      # do sprawdzania także różnej liczby linii
warnings.simplefilter("always")

FLAG = "01111110"
GEN  = "1001"          # wielomian x³ + 1 → 3-bitowa reszta CRC
# ────────────────────────────────────────────────────────────
#  Funkcje pomocnicze: XOR i dzielenie modulo-2
# ────────────────────────────────────────────────────────────
def minus_gen(x: str) -> str:
    return ''.join('0' if x[i] == GEN[i] else '1' for i in range(1, len(GEN)))

def div_rem(data: str) -> str:
    nxt, rem = len(GEN), data[:len(GEN)]
    while nxt <= len(data):
        rem = minus_gen(rem) if rem[0] == '1' else rem[1:]
        if nxt == len(data):
            break
        rem += data[nxt]
        nxt += 1
    return rem

def crc(data: str) -> str:
    return div_rem(data + '0' * (len(GEN) - 1))
# ────────────────────────────────────────────────────────────
#  Kodowanie: ramki + bit-stuffing
# ────────────────────────────────────────────────────────────
def encode(data: str, max_datasize: int = 32) -> list[str]:
    frames, i = [], 0
    while i < len(data):
        cur = data[i:i+max_datasize] + crc(data[i:i+max_datasize])
        cur_frame, ones = '', 0
        for c in cur:
            if ones == 5:
                cur_frame += '0'; ones = 0      # bit-stuffing
            ones = ones + 1 if c == '1' else 0
            cur_frame += c
        frames.append(FLAG + cur_frame + FLAG)
        i += max_datasize
    return frames
# ────────────────────────────────────────────────────────────
#  Dekodowanie
# ────────────────────────────────────────────────────────────
def decode(stream: str) -> tuple[str,int,int]:
    frames = list(filter(None, stream.split(FLAG)))
    decoded, ok, bad = [], 0, 0
    for frame in frames:
        current, i, ones = '', 0, 0
        while i < len(frame):
            current += frame[i]
            if frame[i] == '1':
                ones += 1
                if ones == 5: i += 1; ones = 0  # pomijamy wstawiony '0'
            else:
                ones = 0
            i += 1
        if div_rem(current) != '0'*(len(GEN)-1):
            warn(f"Frame containing {frame} omitted."); bad += 1
        else:
            decoded.append(current[:-(len(GEN)-1)]); ok += 1
    return ''.join(decoded), ok, bad
# ────────────────────────────────────────────────────────────
#  Operacje na plikach
# ────────────────────────────────────────────────────────────
def create_frames(src: str, dst: str) -> None:
    try:
        with open(src, 'r', newline='') as f: lines = f.readlines()
    except FileNotFoundError: print("Source file not found."); return
    total = 0
    with open(dst, 'w', newline='') as g:
        for line in lines:
            data, sep = line.rstrip('\n'), line[len(line.rstrip('\n')):]
            frames = encode(data); total += len(frames)
            g.write(''.join(frames) + sep)
    print(f"Plik {dst} został wygenerowany.\nLiczba zakodowanych ramek: {total}")

def decode_frames(src: str, dst: str) -> None:
    try:
        with open(src, 'r', newline='') as f: lines = f.readlines()
    except FileNotFoundError: print("Source file not found."); return
    ok = bad = 0
    with open(dst, 'w', newline='') as g:
        for line in lines:
            stream, sep = line.rstrip('\n'), line[len(line.rstrip('\n')):]
            out, c_ok, c_bad = decode(stream)
            ok += c_ok; bad += c_bad
            g.write(out + sep)
    print("Dekodowanie zakończone.")
    print(f"Poprawnie zdekodowane ramki: {ok}\nUsunięte (uszkodzone) ramki: {bad}")

# ────────────────────────────────────────────────────────────
#  NOWA ❹ FUNKCJA – porównanie istniejących plików
# ────────────────────────────────────────────────────────────
def compare_files(file1: str = "Z.txt", file2: str = "Z1.txt") -> None:
    """Porównaj dwa pliki linia-po-linii (bez ponownego kodowania/ dekodowania)."""
    try:
        with open(file1, 'r', newline='') as f1, open(file2, 'r', newline='') as f2:
            for lineno, (ln1, ln2) in enumerate(zip_longest(f1, f2, fillvalue=None), 1):
                if ln1 != ln2:
                    print(f"Pliki różnią się. Pierwsza różnica w linii {lineno}.")
                    return
            print("Pliki są identyczne.")
    except FileNotFoundError as e:
        print(f"Brak pliku: {e.filename}")
# ────────────────────────────────────────────────────────────
#  Funkcja testowa (wciąż dostępna jako opcja 3)
# ────────────────────────────────────────────────────────────
def test_decoding() -> None:
    create_frames("Z.txt", "W.txt")
    decode_frames("W.txt", "Z1.txt")
    compare_files("Z.txt", "Z1.txt")
# ────────────────────────────────────────────────────────────
#  MENU
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("1. Zakoduj plik Z.txt do W.txt")
    print("2. ZDEKODUJ W.txt do Z1.txt (weryfikacja CRC)")
    print("3. Porównaj Z.txt ↔ Z1.txt (z ponownym kodowaniem i dekodowaniem)")
    print("4. Porównaj istniejące Z.txt ↔ Z1.txt (bez dodatkowych operacji)")
    choice = input("Wybierz opcję (1/2/3/4): ")

    if choice == '1':
        create_frames("Z.txt", "W.txt")
    elif choice == '2':
        decode_frames("W.txt", "Z1.txt")
    elif choice == '3':
        test_decoding()
    elif choice == '4':
        compare_files()
    else:
        print("Nieprawidłowy wybór.")
