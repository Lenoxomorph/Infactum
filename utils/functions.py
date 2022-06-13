import discord
import csv


async def try_delete(message):
    try:
        await message.delete()
    except discord.HTTPException:
        pass


def search_csv(key, path):
    with open(path, "r") as file:
        reader = csv.DictReader(file, delimiter=",")
        for row in reader:
            if row[reader.fieldnames[0]] == key:
                return row[reader.fieldnames[1]]
