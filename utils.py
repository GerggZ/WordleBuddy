import os
import json
import pandas as pd
from typing import List

def determine_language() -> str:
    """Prompts the user to select a language and returns the appropriate code.
    Defaults to English if the input is unrecognized.

    Returns:
        str: The selected language code ('english', 'german', 'austrian', or 'spanish').
    """
    print("Available Languages are - English, German (AT, DE), and Spanish")
    language = str(input("Choose Your Language: ")).lower()

    if 'at' in language:
        return 'austrian'  # .at wordle has a different word bank (doesn't use umlauts)
    elif 'de' in language:
        return 'german'
    elif 'spanish' in language:
        return 'spanish'

    return 'english'  # Default to English if no match/invalid input


def load_word_bank_config() -> dict:
    """Loads the word bank configuration from the JSON file.

    Returns:
        dict: A dictionary mapping language codes to word bank file names.
    """
    base_dir = os.path.dirname(__file__)  # Get the directory of the current script
    config_path = os.path.join(base_dir, 'word_banks', 'word_bank_config.json')

    # Load and return the word bank configuration from the JSON file
    with open(config_path, 'r') as f:
        return json.load(f)


def conform_word_bank(word_bank: List[str]) -> List[str]:
    """Filters and processes the word bank to include only valid 5-letter words.

    Args:
        :param word_bank: List of words loaded from the word bank file.

    Returns:
        list: A list of lowercase words that are exactly 5 characters long.
    """
    # Ensure words are lowercase strings and exactly 5 characters long
    return [str(word).lower() for word in word_bank if isinstance(word, str) and len(word) == 5]


def get_word_bank(language: str) -> List[str]:
    """Retrieves and returns the word bank for the given language.

    Args:
        :param language: The language code selected by the user.

    Returns:
        list: A list of valid 5-letter words for the selected language.
    """
    # Load the word bank configuration
    word_bank_config = load_word_bank_config()

    # Get the directory of the current script
    base_dir = os.path.dirname(__file__)

    # Select the appropriate word bank file based on the language, defaulting to English if the language isn't found
    fileloc = os.path.join(base_dir, 'word_banks', word_bank_config.get(language, word_bank_config['word_banks']['english']))
    print(f"\nPlaying {language.capitalize()} Wordle")

    # Load the word bank from the file
    word_bank = pd.read_csv(fileloc, sep=",", header=None, encoding="utf-8").values.flatten().tolist()

    # Return the conformed word bank (only valid 5-letter words)
    return conform_word_bank(word_bank)


def get_valid_word_and_info() -> tuple:
    while True:
        user_word = input("\tPlease enter your word: ").lower()  # Convert word to lowercase
        if not user_word.isalpha():  # Ensure the word contains only letters
            print("\tInvalid input. Please enter a word containing only letters.")
            continue

        user_info = input("\tPlease input the letter information for your word (only g, w, y): ").lower()
        if not all(char in "gwy" for char in user_info):  # Ensure the info contains only 'g', 'w', 'y'
            print("\tInvalid input. Please only use 'g', 'w', or 'y'.")
            continue

        return (user_word, user_info)  # Return the tuple if both inputs are valid
