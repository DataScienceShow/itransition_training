import os
import hashlib
from functools import reduce

# Directory containing the binary files
dir_path = os.path.join(os.path.dirname(__file__), '..', 'task2')

# List all .data files
files = [f for f in os.listdir(dir_path) if f.endswith('.data')]
files.sort()  # sort for reproducibility, not required by task

hashes = []

for fname in files:
    fpath = os.path.join(dir_path, fname)
    with open(fpath, 'rb') as f:
        data = f.read()
    h = hashlib.sha3_256(data).hexdigest()
    hashes.append(h)

def sorting_key(h):
    # Product of (each hex digit + 1)
    prod = 1
    for c in h:
        prod *= (int(c, 16) + 1)
    return prod

# Sort hashes by the product key
hashes_sorted = sorted(hashes, key=sorting_key)

# Concatenate sorted hashes (no separator)
result_str = ''.join(hashes_sorted)

# Append email in lowercase as required by the task
email = 'ziyodullofficial@gmail.com'
result_with_email = result_str + email

# Compute SHA3-256 of the result string with email (as bytes)
final_hash = hashlib.sha3_256(result_with_email.encode('utf-8')).hexdigest()

print(final_hash)
