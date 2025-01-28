import numpy as np
from numpy.typing import NDArray
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wordle_solver.utils.word_bank_manager import WordBankManager
    from wordle_solver.utils.hyperparameters import Hyperparameters


class WordScorerEntropy:
    """
    Scores word guesses using entropy-based information gain.
    Connected to WordBankManager and dynamically updates based on possible words.
    """

    def __init__(self, word_bank: "WordBankManager", hparams: "Hyperparameters", hardcore_mode: bool = False):
        """
        Initializes the entropy-based word scorer.

        :param word_bank: A reference to the WordBankManager instance.
        :param hparams: Hyperparameters object containing entropy scaling factors.
        """
        self.word_bank = word_bank
        self.hparams = hparams
        self.hardcore_mode = hardcore_mode
        self.toggle_mode(hardcore_mode)

        # Dynamically determine the highest Unicode character used
        max_unicode = np.max(self.word_bank.full_word_bank)  # Get max Unicode value from word bank
        self.char_freq_table = np.zeros((max_unicode + 1, 5), dtype=np.int32)

    def toggle_mode(self, hardcore_mode: bool) -> None:
        """
        Toggles between possible_word_bank and full_word_bank based on the hardcore mode.

        :param hardcore_mode: If True, uses full_word_bank; otherwise, uses possible_word_bank.
        """
        self.hardcore_mode = hardcore_mode
        self.current_word_bank = (
            self.word_bank.full_word_bank if self.hardcore_mode else self.word_bank.possible_word_bank
        )

    def _precompute_letter_frequencies(self) -> None:
        """Counts the frequency of each letter in each position across the list of words in the current word bank."""
        # Vectorized counting operation
        self.char_freq_table.fill(0)  # Reset frequencies
        for pos in range(self.current_word_bank.shape[1]):
            np.add.at(self.char_freq_table, (self.current_word_bank[:, pos], pos), 1)

    def _calculate_entropy_scores(self) -> NDArray:
        """
        Scores all words in the word bank simultaneously using vectorized entropy calculations.

        :return: NumPy array containing scores for all words.
        """
        self._precompute_letter_frequencies()

        total_words = len(self.current_word_bank)  # Total number of words
        total_char_frequencies = np.sum(self.char_freq_table, axis=1)  # Overall frequency of each character

        # Probabilities for Green, Yellow, and White entropies
        # Clip to ensure probabilities are between 0 and 1
        epsilon = 1e-10
        p_green = np.clip(
            self.char_freq_table / total_words, epsilon, 1 - epsilon
        )  # Probability of the letter being in the correct position
        p_yellow = np.clip(
            (total_char_frequencies[:, None] - self.char_freq_table) / total_words, epsilon, 1 - epsilon
        )  # Probability of the letter being in the word but in the wrong position
        p_white = np.clip(
            1 - total_char_frequencies / total_words, epsilon, 1 - epsilon
        )  # Probability of the letter not appearing in the word

        # Compute entropy safely using binary entropy formula H(p) = -p log2(p) - (1-p) log2(1-p)
        green_entropy = -p_green * np.log2(p_green) - (1 - p_green) * np.log2(1 - p_green)
        yellow_entropy = -p_yellow * np.log2(p_yellow) - (1 - p_yellow) * np.log2(1 - p_yellow)
        white_entropy = -p_white * np.log2(p_white) - (1 - p_white) * np.log2(1 - p_white)

        # Expand white entropy to match positions
        white_entropy = white_entropy[:, None]  # Shape (m, 1) to broadcast correctly across positions

        return green_entropy, yellow_entropy, white_entropy

    def _apply_hyperparameters(
            self,
            attempt_num: int,
            green_entropy: NDArray, yellow_entropy: NDArray, white_entropy: NDArray
    ) -> NDArray:
        """
        Applies hyperparameters to the entropy calculations, vectorized for efficiency

        - Penalizes repeated letters progressively in yellow entropy
        - Averages white entropy across repeated instances
        - Boosts entropy for words that could be the correct answer

        Args:
            - attempt_num: Current attempt number (used for weighting)
            - green_entropy: Green entropy scores for all words
            - yellow_entropy: Yellow entropy scores for all words
            - white_entropy: White entropy scores for all words
        Returns:
            - NDArray: Adjusted word entropies
        """
        # Combine entropies
        weighted_entropy = green_entropy + yellow_entropy + white_entropy

        # Get word matrix (integer representation of words)
        words_matrix = self.word_bank.possible_word_bank  # Shape: (num_words, 5)

        # Use the length of self.char_freq_table to define the bin count size
        bin_count_size = len(self.char_freq_table)

        # per-word character frequency calculation
        num_words, word_length = words_matrix.shape
        per_word_char_frequencies = np.zeros((num_words, bin_count_size), dtype=int)

        # Efficiently count character occurrences per word using np.add.at()
        np.add.at(per_word_char_frequencies, (np.arange(num_words)[:, None], words_matrix), 1)

        # Extract frequency counts for each character in its respective position
        char_frequencies = np.take_along_axis(per_word_char_frequencies, words_matrix, axis=1)  # Shape: (num_words, 5)

        # Compute smoothed yellow entropy penalty
        yellow_penalty_factors = (1 + (1 / char_frequencies)) / 2  # Progressive but softer penalty

        # Compute white entropy averaging (unchanged)
        white_penalty_factors = np.where(char_frequencies > 0, 1 / char_frequencies, 1)

        # Identify repeated letters
        repeated_mask = char_frequencies > 1  # True where a character appears more than once

        # Extract entropies for words in the possible word bank
        word_entropies = weighted_entropy[
            self.word_bank.possible_word_bank, np.arange(self.word_bank.possible_word_bank.shape[1])
        ]
        # Apply penalties in a single vectorized operation
        word_entropies *= np.where(repeated_mask, yellow_penalty_factors * white_penalty_factors, 1)

        # Identify potential answers and apply weighting
        is_potential_answer = np.isin(self.word_bank.possible_word_bank, self.word_bank.possible_word_bank)
        answer_weights = self.hparams.answer_weight_base * (1 + attempt_num / self.hparams.max_guesses)

        # Apply answer weighting in a vectorized manner
        word_entropies *= 1 + (is_potential_answer * answer_weights)

        return word_entropies

    def score_word_bank(self, attempt_num: int) -> NDArray:
        """
        Scores all words in the word bank simultaneously using vectorized entropy calculations.
        Weights the word entropies based on the hyperparameters

        :return: NumPy array containing scores for all words.
        """
        green_entropy, yellow_entropy, white_entropy = self._calculate_entropy_scores()

        # Weight the entropies based on the hyperparameters
        word_entropies = self._apply_hyperparameters(
            attempt_num,
            green_entropy, yellow_entropy, white_entropy
        )

        # Sum entropies across positions for each word
        scores = np.sum(word_entropies, axis=1)

        return scores
