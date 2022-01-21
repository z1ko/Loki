
import numpy as np
import random
import argparse

from PIL import Image as im
from itertools import product
from math import isqrt

# Applica pattern binario alle prime n - 1 righe
def set_binary_pattern(s):

    rows, cols = np.shape(s)
    for i in range(rows - 1):
        
        power = 2 ** i
        for j in range(cols):
            s[i, j] = (j // power) % 2


# Genera matrici di offuscamento per uno schema di sbarramento n-n con k subpixel
def generate_obfuscating_matrices(n, k):

    s0 = np.zeros((n, k), dtype=np.uint8)
    s1 = s0.copy()

    # Genera combinazioni binarie nelle prime n - 1 righe
    set_binary_pattern(s0)
    set_binary_pattern(s1)

    # Completa la parità per gli zeri e rompila per gli uni
    for c in range(k):
        parity = sum(s0[:, c]) % 2
        s = s1 if parity == 0 else s0
        s[n - 1, c] = 1

    return s0, s1

# Estende una matrice sfruttando sm
def extend_obfuscating_matrix(sm, s, expansion):

    rows, cols = np.shape(s)
    e = np.zeros((rows, cols * expansion), dtype=np.uint8)
    #TODO
    return e


# Genera matrici estese per uno schema a barriera k-n a partire dalla matrice di combinazione sm
def generate_extendend_obfuscating_matrices(sm, s0, s1):
    
    rows, expansion = np.shape(sm)
    e0 = extend_obfuscating_matrix(sm, s0, expansion)
    e1 = extend_obfuscating_matrix(sm, s1, expansion)

    return e0, e1


# Genera subpixels per ogni layer
def generate_subpixels(pixel, s0, s1):

    # Sceglie che matrice usare per la codifica del pixel
    obfuscator = s0 if pixel == 0 else s1
    rows, cols = np.shape(obfuscator)
    result = np.zeros((rows, cols))

    # Accesso permutato alle colonne
    access = random.sample(range(cols), cols)
    for share in range(rows):
        result[share] = obfuscator[share, access]

    return result
    

# Genera le share
def generate_shares(image, s0, s1, shares, subpixels, stride):
    
    h, w = np.shape(image)
    stride_w, stride_h = stride, subpixels // stride
    result = np.zeros((shares, h * stride_h, w * stride_w), dtype=np.uint8)

    # Attraversa l'immagine e ottiene i subpixel associati ad ogni pixel per share 
    for (y, x) in product(range(h), range(w)):
        subpixels = generate_subpixels(image[y, x], s0, s1)

        # Costruisce un intero pixel associato delle shares
        for share in range(shares):
            for v, subpixel in enumerate(subpixels[share]):

                dy = v // stride_h
                dx = v %  stride_w

                result[share][y * stride_h + dy, x * stride_w + dx] = subpixel

    return result


parser = argparse.ArgumentParser()
parser.add_argument("file", help = "file to obfuscate")
parser.add_argument("shares", type = int, help = "number of shares to generate")
parser.add_argument("--subpixels", type = int, help = "number of subpixel used, default is 2 ^ (shares - 1)")
parser.add_argument("--stride", type = int, help = "tells how to shape the subpixels in the generated shares, default is sqrt(subpixels)")

args = parser.parse_args()

# Carica immagine da offuscare
decode = lambda x: x // 255
with im.open(args.file) as file:
    image = np.asarray(file.convert('L'), dtype=np.uint8)
    image = decode(image)

shares = args.shares
subpixels = args.subpixels if args.subpixels else 2 ** (shares - 1)
stride = args.stride if args.stride else isqrt(subpixels)

assert(subpixels >= 2 ** (shares - 1))
print(f"Generating {shares} shares with {subpixels} subpixels, final contrast value is { 1.0 / subpixels }")

s0, s1 = generate_obfuscating_matrices(shares, subpixels)
result = generate_shares(image, s0, s1, shares, subpixels, stride)

encode = lambda x: x * 255
for share in range(shares):

    data = encode(result[share])
    file = im.fromarray(data, "L")
    file.save(f"share_{share}.png")
    file.close()
