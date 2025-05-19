from typing import Any
import argparse
import re
from googletrans import Translator
from tqdm import tqdm
import yaml

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--input", help = "path to the input file", required = False)
parser.add_argument("-o", "--output", help = "path to the output file", required = False)
parser.add_argument("-l", "--langs", help = "languages to translate", required = False, default="en,es")
args = parser.parse_args()

PATTENRS = [
    r"&[A-Za-z0-9]{1}+",
    r"%[A-Za-z]+(?: [A-Za-z]+)*%",
    r"{[A-Za-z0-9]+}",
]

KEY_PATTERN = "[{counter}]"

TRANSLATOR = Translator()


g_counter: int = 0
text_patterns_replaced: dict[int, str] = {}
def encode_text(text: str) -> str:
    global g_counter
    global text_patterns_replaced
    text_patterns: list[str] = []
    for pattern in PATTENRS:
        for results in re.finditer(pattern, text):
            text_patterns.append(results.group())
    
    set_text_patterns: set[str] = set(text_patterns)
    for text_pattern in set_text_patterns:
        text = text.replace(text_pattern, KEY_PATTERN.format(counter=g_counter))
        text_patterns_replaced[g_counter] = text_pattern
        g_counter += 1

    return text

def decode_text(text: str) -> str:
    global text_patterns_replaced
    for key in text_patterns_replaced.keys():
        text = text.replace(
            f"{KEY_PATTERN.format(counter=key)} ", text_patterns_replaced[key]
        ).replace(
            KEY_PATTERN.format(counter=key), text_patterns_replaced[key]
        )
    return text


async def translate(text: str, lang: str) -> str:
    return (await TRANSLATOR.translate(text, dest=lang)).text

async def traverse(data: dict[str, Any], lang: str, 
            progress: bool = False, safe_materials: bool = False
) -> dict[str, Any]:
    new_data: dict[str, Any] = {}
    for init_key in tqdm(data.keys()) if progress else data.keys():
        if init_key == 'material' or init_key == "item":
            """	is a material or item and we dont need to translate it"""
            new_data[init_key] = data[init_key]
        elif isinstance(data[init_key], dict):
            """	is a dict and we need to translate it"""
            new_data[init_key] = await traverse(lang=lang, data=data[init_key])
        elif isinstance(data[init_key], list):
            """	is a list and we need to translate it.
            we jooin all the elements of the list and translate them
            """
            new_data[init_key] = (await translate(lang=lang, text="||".join(data[init_key]))).split("||")
        elif isinstance(data[init_key], str):
            """	is a string and we need to translate it"""
            new_data[init_key] = await translate(lang=lang, text=data[init_key])
        else:
            """	is a other type and we dont need to translate it"""
            new_data[init_key] = data[init_key]
            
    return new_data


async def main() -> None:
    # languages to translate the text
    langs = args.langs.split(",")
    if len(langs) != 2:
        print("Error: langs must be in the format 'source,target'")
        exit(1)

    # text from input file
    input_text = open(args.input, "r", encoding="utf-8").read()

    # text enconded to preserve colors, placeholders and other stuff
    text_encoded = encode_text(input_text)

    # transform the raw text to a dict
    data = yaml.safe_load(text_encoded)

    # traverse and translate the text
    new_data = await traverse(data=data, lang=langs[1], progress=True)

    # dump the dict to a string formatted in yaml
    raw_text = yaml.dump(data=new_data, allow_unicode=True, stream=None)

    # decode the preserved colors, placeholders and other stuff
    decoded_text = decode_text(text=raw_text)

    # write the decoded text to the output file
    open(args.output, "w", encoding="utf-8").write(decoded_text)

