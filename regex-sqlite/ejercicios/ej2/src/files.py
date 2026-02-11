import csv
from collections import namedtuple

nt = namedtuple("Book", ["isbn", "title", "author", "year", "publisher"])

def read_file(file):
    with open(file, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)
        return [nt(r[0], r[1], r[2], r[3], r[4]) for r in reader] 