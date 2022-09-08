import csv
import shutil
from tempfile import NamedTemporaryFile


def search_csv(key, path):
    with open(path, "r", newline='', encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=",")
        next(reader)
        for row in reader:
            if row[0] == key:
                return row[1:]


def append_csv(item, path):
    with open(path, "a", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(item)


def write_csv(rows, path):
    with open(path, "w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def edit_csv(item, path):
    temp_file = NamedTemporaryFile('w+t', delete=False, newline='', encoding="utf-8")

    with open(path, 'r', newline='') as csv_file, temp_file:
        reader = csv.reader(csv_file, delimiter=',')
        writer = csv.writer(temp_file, delimiter=',')
        for row in reader:
            if row[0] == item[0]:
                continue
            writer.writerow(row)

    shutil.move(temp_file.name, path)
    append_csv(item, path)


def read_line(row_num, path):
    return read_csv(path)[row_num]


def read_csv(path):
    with open(path, "r", newline='', encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=',')
        return list(reader)


def read_keys(path):
    with open(path, "r", newline='', encoding="utf-8") as file:
        return_list = []
        for line in csv.reader(file, delimiter=','):
            return_list.append(line[0])
        return return_list
