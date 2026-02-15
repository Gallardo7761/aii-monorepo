import csv

class FileReader:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, delimiter=";"):
        self.delimiter = delimiter

    def read(self, file):
        results = []
        try:
            with open(file, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                for row in reader:
                    results.append(dict(row))
        except Exception as e:
            print(f"Error leyendo archivo: {e}")
        return results