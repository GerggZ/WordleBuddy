import numpy as np
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wordle_solver.utils.word_bank_manager import WordBankManager


class WordScorerEntropy:
    """
    Scores word guesses using entropy-based information gain.
    Connected to WordBankManager and dynamically updates based on possible words.
    """

    def __init__(self, word_bank: "WordBankManager", hparams):
        """
        Initializes the entropy-based word scorer.

        :param word_bank: A reference to the WordBankManager instance.
        :param hparams: Hyperparameters object containing entropy scaling factors.
        """
        self.word_bank = word_bank
        self.hparams = hparams

        # Dynamically determine the highest Unicode character used
        max_unicode = np.max(self.word_bank.full_word_bank)  # Get max Unicode value from word bank
        self.char_freq_table = np.zeros((max_unicode + 1, 5), dtype=np.int32)

    def _precompute_letter_frequencies(self) -> None:
        """Counts the frequency of each letter in each position across the list of possible words."""
        # Vectorized counting operation
        self.char_freq_table.fill(0)  # Reset frequencies
        for pos in range(self.word_bank.possible_word_bank.shape[1]):
            np.add.at(self.char_freq_table, (self.word_bank.possible_word_bank[:, pos], pos), 1)

    def score_word_bank(self) -> np.ndarray:
        """
        Scores all words in the word bank simultaneously using vectorized entropy calculations.

        :return: NumPy array containing scores for all words.
        """
        self._precompute_letter_frequencies()

        total_words = len(self.word_bank.possible_word_bank)  # Total number of words
        total_char_frequencies = np.sum(self.char_freq_table, axis=1)  # Overall frequency of each character

        # Probabilities for Green, Yellow, and White entropies
        p_green = np.clip(self.char_freq_table / total_words, 1e-10,
                          1)  # Probability of the letter being in the correct position
        p_yellow = np.clip((total_char_frequencies[:, None] - self.char_freq_table) / total_words, 1e-10,
                           1)  # Probability of the letter being in the word but in the wrong position
        p_white = np.clip(1 - total_char_frequencies / total_words, 1e-10,
                          1)  # Probability of the letter not appearing in the word

        # Compute entropy safely using binary entropy formula H(p) = -p log2(p) - (1-p) log2(1-p)
        green_entropy = -p_green * np.log2(p_green) - (1 - p_green) * np.log2(1 - p_green)
        yellow_entropy = -p_yellow * np.log2(p_yellow) - (1 - p_yellow) * np.log2(1 - p_yellow)
        white_entropy = -p_white * np.log2(p_white) - (1 - p_white) * np.log2(1 - p_white)

        # Expand white entropy to match positions
        white_entropy = white_entropy[:, None]  # Shape (m, 1) to broadcast correctly across positions

        # Compute total entropy contribution
        total_entropy = green_entropy + yellow_entropy + white_entropy

        # Extract entropies for each word
        word_entropies = total_entropy[
            self.word_bank.possible_word_bank, np.arange(self.word_bank.possible_word_bank.shape[1])]

        # Sum entropies across positions for each word
        scores = np.sum(word_entropies, axis=1)

        return scores
