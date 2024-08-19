import fire
import yaml
from deep_translator import GoogleTranslator
from tqdm import tqdm
import sqlite3
import re

conn = sqlite3.connect('materials.db')
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS materials (
        name text NOT NULL PRIMARY KEY,
        numericId text,
        isBlock text,
        isItem text,
        isSolid text,
        isOccluding text,
        key text,
        blockTranslationKey text,
        itemTranslationKey text,
        maxStackSize text,
        maxDurability text,
        blockDataClass text,
        isInteractable text,
        hasGravity text,
        isEdible text,
        isRecord text,
        isFlammable text,
        isBurnable text,
        isFuel text,
        hardness text,
        blastResistence text,
        slipperiness text,
        craftingRemainingItem text,
        equipmentSlot text,
        creativeCategory text,
        compostChance text)""")
conn.commit()


def exist_material(material: str):
    query = cursor.execute(f'select *  from materials where name="{material}"')
    return False if len(query.fetchall()) == 0 else True


def translate(text: str, langs: [str] = ("en", "es")):
    encoded_text = text
    vars = {}
    counter = 0
    for i in re.finditer("&[A-Za-z0-9]+", encoded_text):
        temp_uuid = f"|-{counter}-|"
        vars[temp_uuid] = i.group()[0:2]
        encoded_text = encoded_text.replace(i.group()[0:2], str(temp_uuid) + ' ')
        counter += 1

    for i in re.finditer("%[A-Za-z0-9]+%", encoded_text):
        temp_uuid = f"|-{counter}-|"
        vars[temp_uuid] = i.group()
        encoded_text = encoded_text.replace(i.group(), str(temp_uuid) + ' ')
        counter += 1

    try:
        translate_text = GoogleTranslator(source=langs[0], target=langs[1]).translate(encoded_text)
    except:
        translate_text = encoded_text

    decoded_text = translate_text
    for i in vars.keys():
        decoded_text = decoded_text.replace(
            str(i), vars[i]
        )
    for i in vars.keys():
        decoded_text = decoded_text.replace(
            str(i) + " ", vars[i]
        )
    return decoded_text


def traversal(data: dict, progress: bool = False, safe_materials: bool = False, langs: [str] = ("en", "es")):
    new_data = {}
    iterable = tqdm(data.keys()) if progress else data.keys()
    for i in iterable:
        if i == 'material' or i == "item":
            continue
        if isinstance(data[i], dict):
            new_data[i] = traversal(data=data[i])
        elif isinstance(data[i], list):
            one_line = " |%| ".join(data[i])
            one_line_translated = translate(one_line, langs)
            new_data[i] = list(map(lambda x: x.replace("|%| ", ""), one_line_translated.split(" |%| ")))
            # new_data[i] = list(map(lambda x: translate(x, langs), data[i]))
        elif isinstance(data[i], str):
            if safe_materials and exist_material(data[i]):
                continue
            new_data[i] = translate(data[i].replace('\'', ""), langs)
        else:
            new_data[i] = data[i]
    return new_data


class ConfigTranslatorApp(object):

    def help(self):
        pass

    def translate(self, path: str, output_file_name: str = 'config_translate.yml', lang_from: str = "en",
                  lang_to: str = "es", safe_materials: bool = False):
        config = yaml.safe_load(
            open(path, 'r', encoding='utf-8').read()
        )
        new_config = traversal(data=config,
                               progress=True,
                               safe_materials=safe_materials,
                               langs=[lang_from, lang_to])

        new_file = open(output_file_name, "w", encoding='utf-16')
        yaml.dump(data=new_config, allow_unicode=True, stream=new_file)
        new_file.close()
        print("------Translate Complete--------")


def main():
    exit_code = fire.Fire(ConfigTranslatorApp)


#if __name__ == '__main__':
    fire.Fire(ConfigTranslatorApp)
