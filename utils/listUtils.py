def is_in_list(item, path):
    with open(path, "r") as file:
        next(file)
        for line in file:
            if line.strip() == item:
                return True
    return False


def append_list(item, path):
    with open(path, "a") as file:
        file.write(f"\n{item}")


def flat_map_list(func, path):
    with open(path, "r") as file:
        next(file)
        for line in file:
            func(line.strip())


def reset_list(path):
    with open(path, "r") as file:
        title = file.readline().strip()
    with open(path, "w") as file:
        file.write(title)
