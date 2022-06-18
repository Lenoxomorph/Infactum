import csv
import shutil
from tempfile import NamedTemporaryFile


def search_csv(key, path):
    with open(path, "r", newline='', encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=",")
        for row in reader:
            if row[reader.fieldnames[0]] == key:
                return row[reader.fieldnames[1]]


def append_csv(item, path):
    with open(path, "a", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(item)


def edit_csv(item, path):
    temp_file = NamedTemporaryFile('w+t', delete=False, newline='', encoding="utf-8")  # Delete False

    with open(path, 'r', newline='') as csv_file, temp_file:
        reader = csv.reader(csv_file, delimiter=',')
        writer = csv.writer(temp_file, delimiter=',')
        for row in reader:
            if row[0] == item[0]:
                continue
            writer.writerow(row)

    shutil.move(temp_file.name, path)
    append_csv(item, path)
