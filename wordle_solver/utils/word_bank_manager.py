import numpy as np
from numpy.typing import NDArray
from typing import Dict, List
import importlib.resources as pkg_resources

from wordle_solver.word_banks import __name__ as word_banks_package  # Package name reference


class WordBankManager:
    """
    Manages a dynamically loaded word bank from .npy files.
    Uses NumPy for efficient filtering based on Wordle feedback.
    """

    def __init__(self, language: str):
        """
        Loads the word bank from the specified .npy file.

        :param language: The selected language (must match a key in WORD_BANK_FILE_PATHS).
        """
        self.full_word_bank, self.ascii_converter_key = self._load_word_bank(language)
        self.possible_word_bank = self.full_word_bank.copy()

    @staticmethod
    def _load_word_bank(language: str) -> np.ndarray:
        """Loads and converts the word bank from the package directory."""
        file_name = f"{language}_word_bank.npy"

        try:
            with pkg_resources.files(word_banks_package).joinpath(file_name).open("rb") as file:
                word_list = np.load(file)  # Load `.npy` file
        except FileNotFoundError:
            raise FileNotFoundError(f"❌ Word bank file '{file_name}' not found in package. Ensure it exists in `wordle_solver/word_banks/`.")

        # Convert characters to ASCII values
        word_bank = np.array([[ord(char) for char in word] for word in word_list], dtype=np.int32)

        # Find the minimum ASCII value
        min_value = word_bank.min()

        # Normalize by subtracting the minimum ASCII value
        normalized_word_bank = word_bank - min_value

        return normalized_word_bank, min_value

    @staticmethod
    def _find_duplicates(word: NDArray) -> Dict[int, int]:
        """Counts occurrences of each letter in the guessed word."""
        counts = np.bincount(word[word >= 0])
        return {char: count for char, count in enumerate(counts) if count > 0}

    def _remove_gray(self, incorrect: int) -> None:
        """Removes words containing an incorrect letter (gray feedback)."""
        mask = ~np.any(self.possible_word_bank == incorrect, axis=1)  # Find words without the letter
        self.possible_word_bank = self.possible_word_bank[mask]

    def _remove_green(self, index: int, correct: int) -> None:
        """Keeps only words where the correct letter is in the exact position (green feedback)."""
        mask = self.possible_word_bank[:, index] == correct
        self.possible_word_bank = self.possible_word_bank[mask]

    def _remove_yellow(self, index: int, correct: int) -> None:
        """Removes words where the letter is in the wrong position but ensures it is present elsewhere (yellow feedback)."""
        contains_letter = np.any(self.possible_word_bank == correct, axis=1)  # Letter must be present somewhere
        wrong_position = self.possible_word_bank[:, index] != correct  # But NOT in this position
        self.possible_word_bank = self.possible_word_bank[(contains_letter) & (wrong_position)]  # Parentheses for clarity

    def _remove_duplicate_letters(self, letter: int, max_count: int) -> None:
        """Removes words where the letter appears more times than allowed."""
        counts = (self.possible_word_bank == letter).sum(axis=1)
        self.possible_word_bank = self.possible_word_bank[counts <= max_count]

    def _regular_removal(self, letter: int, position: int, feedback: str) -> None:
        """
        Applies filtering based on Wordle feedback.

        :param guess: The guessed word.
        :param information: List of feedback ('gray', 'yellow', 'green').
        """
        if feedback == 'gray':
            self._remove_gray(letter)  # Remove words containing this letter
        elif feedback == 'green':
            self._remove_green(position, letter)  # Keep words with this letter at correct position
        elif feedback == 'yellow':
            self._remove_yellow(position, letter)  # Keep words containing the letter but not at this position

    def cull(self, guess: str, information: List[str]) -> None:
        """
        Processes a Wordle guess and filters out impossible words.

        :param guess: The guessed word.
        :param information: List of feedback ('gray', 'yellow', 'green').
        """
        occurrences = self._find_duplicates(guess)
        indices_dict = {char: [i for i, c in enumerate(guess) if c == char] for char in occurrences}

        for letter, count in occurrences.items():
            indices = indices_dict[letter]
            feedback = [information[i] for i in indices]

            if len(self.possible_word_bank) == 0:
                return

            if count == 1:
                self._regular_removal(letter, indices[0], feedback[0])
            else:
                if 'gray' in feedback:
                    max_count = len(feedback) - feedback.count('gray')
                    self._remove_duplicate_letters(letter, max_count)

                for i, color in zip(indices, feedback):
                    if color == 'green':
                        self._remove_green(i, letter)
                    elif color == 'yellow':
                        self._remove_yellow(i, letter)

    def decode_word(self, word: NDArray) -> str:
        """Converts a numpy array of integers back to a string using the stored ascii converter key value."""
        return "".join(chr(char + self.ascii_converter_key) for char in word)

    def encode_word(self, word: str) -> NDArray:
        """Converts string into a numpy array of integers using the stored ascii converter key value."""
        return np.array([ord(char.lower()) - self.ascii_converter_key for char in word])  # Convert guess to ascii

    def reset(self) -> None:
        """Resets the possible words list to the full original list."""
        self.possible_word_bank = self.full_word_bank.copy()
