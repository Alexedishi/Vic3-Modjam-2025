def alienify(s):
    vowels = 'aeiou'
    consonants = ''.join(c for c in 'abcdefghijklmnopqrstuvwxyz' if c not in vowels)

    def is_vowel(c):
        return c.lower() in vowels

    def shift_in_list(c, steps, source_list):
        is_upper = c.isupper()
        c = c.lower()
        if c not in source_list:
            return c  # Leave non-matching chars untouched
        idx = source_list.index(c)
        new_c = source_list[(idx + steps) % len(source_list)]
        return new_c.upper() if is_upper else new_c

    def shift_char(c, index):
        steps = index + 1  # index is 0-based
        if not c.isalpha():
            return c
        if is_vowel(c):
            return shift_in_list(c, steps, vowels)
        else:
            return shift_in_list(c, steps, consonants)

    # Deterministic anagram: sorted characters
    sorted_chars = sorted(s)

    # Apply transformation
    return ''.join(shift_char(c, i) for i, c in enumerate(sorted_chars))

# Read a text file

def get_text_file_paths():
    import os
    import glob
    from pathlib import Path
    message_texts_dir = Path(__file__).parent / 'message_texts'
    files = glob.glob(str(message_texts_dir / '*.txt'))
    if not files:
        raise FileNotFoundError("No text files found in the 'message_texts' directory.")
    return files

def sanitize(s):
    # Remove non-alphanumeric characters and convert to lowercase
    return ''.join(c for c in s if c.isalnum()).lower()

def remove_dups(seq):
    seen = set()
    return [x for x in seq if not (x in seen or seen.add(x))]

def generate_word_map():
    word_list = []

    for file_path in get_text_file_paths():
        with open(file_path, 'r', encoding='utf-8') as file:
            word_list += filter(str.isalnum, remove_dups(file.read().split()))

    word_map = {word: alienify(word) for word in word_list}
    return word_map

def generate_cuslocs(word_map):
    import pdxpy

    cuslocs = []

    for k, v in word_map.items():
        cuslocs.append(
            {
                f"wotw_decipher_word_{sanitize(k)}": [
                    {"type": "country"},
                    {"random_valid": "no"},
                    {"text": {
                        "trigger": {
                            "has_variable": f"wotw_alien_word_deciphered_{sanitize(k)}"
                        },
                        "localization_key": f"wotw_human_word_{sanitize(k)}"
                    }},
                    {"text": {
                        "trigger": {
                            "always": False
                        },
                        "fallback": True,
                        "localization_key": f"wotw_alien_word_{sanitize(k)}"
                    }}
                ]
            }
        )

    return pdxpy.PdxObject(cuslocs)


def generate_word_locs(word_map):
    locs = "l_english:\n\n"
    for k, v in word_map.items():
        locs += f"  wotw_decipherable_word_{sanitize(k)}: \"[GetPlayer.GetCustom('wotw_decipher_word_{k}')]\"\n"
        locs += f"  wotw_alien_word_{sanitize(k)}: \"#italic {v}#!\"\n"
        locs += f"  wotw_human_word_{sanitize(k)}: \"{k}\"\n"
    return locs

def divide_scripted_effects(word_map, N=10):
    from math import ceil
    import random

    keys = list(word_map.keys())
    random.shuffle(keys)  # Shuffle to ensure randomness
    total = len(keys)
    base_size = total // N
    remainder = total % N  # number of parts that get one extra element

    parts = []
    start = 0
    for i in range(N):
        # The first 'remainder' parts get one extra item
        size = base_size + (1 if i < remainder else 0)
        end = start + size
        parts.append(keys[start:end])
        start = end

    return parts

def write_scripted_effect(part, index):
    return {
        f"wotw_decipher_alien_words_part_{index}": [
            {"set_variable": f"wotw_alien_word_deciphered_{sanitize(k)}"} for k in part
        ] + [
            { "set_variable": f"wotw_alien_word_deciphered_part_{index}"}
        ]
    }

def generate_next_scripted_effect(parts):
    import pdxpy
    return pdxpy.PdxObject({
        f"wotw_decipher_alien_words_next_part": [
            pdxpy.PdxUtil.if_statement(
                {"has_variable": f"wotw_alien_word_deciphered_part_{index}"},
                {f"wotw_decipher_alien_words_part_{index + 1}": True}
            ) for index in reversed(range(len(parts) - 1))
        ] + [{"wotw_decipher_alien_words_part_0": True}]
    })


def generate_scripted_effect(word_map):
    import pdxpy
    scripted_effects = []
    parts = divide_scripted_effects(word_map)

    for index, part in enumerate(parts):
        scripted_effects.append(write_scripted_effect(part, index))

    return pdxpy.PdxObject(scripted_effects)

def generate_main_locs():
    locs = "l_english:\n\n"
    for file_path in get_text_file_paths():
        with open(file_path, 'r', encoding='utf-8') as file:
            stem = file_path.split('/')[-1].split('.')[0]
            word_list = [f"$wotw_decipherable_word_{sanitize(k)}$" if k.isalnum() else k for k in file.read().split()]
            locs += f"  wotw_alien_message_{stem}: \"{' '.join(word_list)}\"\n"

    return locs

     

def main():
    word_map = generate_word_map()
    with open("../common/customizable_localization/wotw_alien_words.txt", "w", encoding="utf-8") as f:
        cuslocs = generate_cuslocs(word_map)
        f.write(str(cuslocs))

    with open("../localization/english/wotw_alien_words_l_english.yml", "w", encoding="utf-8-sig") as f:
        f.write(generate_word_locs(word_map))

    with open("../localization/english/wotw_alien_messages_l_english.yml", "w", encoding="utf-8-sig") as f:
        f.write(generate_main_locs())

    with open("../common/scripted_effects/wotw_decipher_alien_words.txt", "w", encoding="utf-8") as f:
        f.write(str(generate_scripted_effect(word_map)) + "\n" + str(generate_next_scripted_effect(divide_scripted_effects(word_map))))


if __name__ == "__main__":
    main()