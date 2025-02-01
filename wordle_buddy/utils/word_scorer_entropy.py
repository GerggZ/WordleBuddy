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

    def __init__(self, word_bank: "WordBankManager", hparams: "Hyperparameters", hardcore_mode: bool = True):
        """
        Initializes the entropy-based word scorer.

        :param word_bank: A reference to the WordBankManager instance.
        :param hparams: Hyperparameters object containing entropy scaling factors.
        """
        self.word_bank = word_bank
        self.hparams = hparams
        self.hardcore_mode = hardcore_mode

        # Find all unique characters and generate a hash table
        unique_chars = sorted(np.unique(self.word_bank.full_word_bank))
        self.char_map = {char: idx for idx, char in enumerate(unique_chars)}

        # Dynamically determine the highest Unicode character used
        self.max_unicode = np.max(self.word_bank.full_word_bank)  # Get max Unicode value from word bank

    def toggle_mode(self, hardcore_mode: bool) -> None:
        """
        Toggles between possible_word_bank and full_word_bank based on the hardcore mode.

        :param hardcore_mode: If True, uses full_word_bank; otherwise, uses possible_word_bank.
        """
        self.hardcore_mode = hardcore_mode

    @property
    def current_word_bank(self) -> NDArray:
        if self.hardcore_mode == True:
            return self.word_bank.possible_word_bank
        else:
            return self.word_bank.full_word_bank

    def _precompute_letter_frequencies(self) -> NDArray:
        """Counts the frequency of each letter in each position across the list of words in the current word bank."""
        # Vectorized counting operation
        char_freq_table = np.zeros((self.max_unicode + 1, 5), dtype=np.int32)

        char_freq_table.fill(0)  # Reset frequencies
        for pos in range(self.word_bank.possible_word_bank.shape[1]):
            np.add.at(char_freq_table, (self.word_bank.possible_word_bank[:, pos], pos), 1)

        return char_freq_table

    def _calculate_entropy_scores(self) -> NDArray:
        """
        Scores all words in the word bank simultaneously using vectorized entropy calculations.

        :return: NumPy array containing scores for all words.
        """
        char_freq_table = self._precompute_letter_frequencies()
        total_char_freq_table = np.sum(char_freq_table, axis=1)  # Sum across positions

        total_viable_words = len(self.word_bank.possible_word_bank)  # Total number of words (of the viable guesses)

        # Probabilities for Green, Yellow, and White entropies
        p_green = char_freq_table / total_viable_words
        p_yellow = (total_char_freq_table[:, None] - char_freq_table) / total_viable_words
        p_white = 1 - total_char_freq_table / total_viable_words

        # Clip to ensure probabilities are between 0 and 1
        epsilon = 1e-10
        p_green = np.clip(p_green, epsilon, 1 - epsilon)
        p_yellow = np.clip(p_yellow, epsilon, 1 - epsilon)
        p_white = np.clip(p_white, epsilon, 1 - epsilon)

        # Compute entropy safely using binary entropy formula H(p) = -p log2(p) - (1-p) log2(1-p)
        green_entropy = -p_green * np.log2(p_green) - (1 - p_green) * np.log2(1 - p_green)
        yellow_entropy = -p_yellow * np.log2(p_yellow) - (1 - p_yellow) * np.log2(1 - p_yellow)
        white_entropy = -p_white * np.log2(p_white) - (1 - p_white) * np.log2(1 - p_white)

        # Expand white entropy so it is for every character position
        white_entropy = np.broadcast_to(white_entropy[:, None], green_entropy.shape)

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
        # per-word character frequency calculation
        num_viable_words, word_length = self.working_word_bank.shape
        per_word_char_frequencies = np.zeros((num_viable_words, self.max_unicode + 1), dtype=int)

        # Efficiently count character occurrences per word using np.add.at()
        np.add.at(per_word_char_frequencies, (np.arange(num_viable_words)[:, None], self.working_word_bank), 1)

        # Extract frequency counts for each character in its respective position
        char_frequencies = np.take_along_axis(per_word_char_frequencies, self.working_word_bank, axis=1)  # Shape: (num_viable_words, 5)

        # Compute smoothed yellow entropy penalty
        yellow_penalty = (1 + (1 / char_frequencies)) / 2  # Progressive but softer penalty

        # Compute white entropy averaging (unchanged)
        white_penalty = np.where(char_frequencies > 0, 1 / char_frequencies, 1)

        word_entropies = (
                green_entropy[self.working_word_bank, np.arange(word_length)] +
                yellow_entropy[self.working_word_bank, np.arange(word_length)] * yellow_penalty +
                white_entropy[self.working_word_bank, np.arange(word_length)] * white_penalty
        )



        non_valid_penalty = 1.0
        if self.word_bank.possible_word_bank.shape[0] <= 2 or attempt_num == self.hparams.max_guesses:
            # Identify potential answers and apply weighting
            is_potential_answer = np.isin(
                self.working_word_bank.view(f'V{self.working_word_bank.shape[1] * 4}'),
                self.word_bank.possible_word_bank.view(f'V{self.working_word_bank.shape[1] * 4}')
            )
            is_potential_answer = np.broadcast_to(
                is_potential_answer, self.working_word_bank.shape
            )
            # if there are less than two words left...or it is our last guess just punt it
            word_entropies *= np.where(is_potential_answer, 1, 0)

        return word_entropies

    def _apply_hparams_old(self, green_entropy, yellow_entropy, white_entropy):
        weighted_entropy = green_entropy + yellow_entropy + white_entropy
        word_entropies = weighted_entropy[self.working_word_bank, np.arange(self.working_word_bank.shape[1])]

        for i, word in enumerate(self.working_word_bank):
            # For each word, identify unique characters
            unique_chars, counts = np.unique(word, return_counts=True)

            for char_idx, count in zip(unique_chars, counts):
                # Get the positions where the current character appears
                char_positions = np.where(word == char_idx)[0]  # Get positions for this character

                yellow_penalty = (1 + (1 / count)) / 2
                white_penalty = 1 / count

                # Apply the diminishing factor to yellow entropy for repeated characters
                for idx, pos in enumerate(char_positions):

                    word_entropies[i, pos] = green_entropy[char_idx, pos] + yellow_entropy[char_idx, pos] * yellow_penalty + white_entropy[char_idx] * white_penalty

        return word_entropies

    def score_word_bank(self, attempt_num: int) -> NDArray:
        """
        Scores all words in the word bank simultaneously using vectorized entropy calculations.
        Weights the word entropies based on the hyperparameters

        :return: NumPy array containing scores for all words.
        """
        self.working_word_bank = self.current_word_bank
        green_entropy, yellow_entropy, white_entropy = self._calculate_entropy_scores()

        # Weight the entropies based on the hyperparameters
        word_entropies = self._apply_hyperparameters(
            attempt_num,
            green_entropy, yellow_entropy, white_entropy
        )

        # Sum entropies across positions for each word
        scores = np.sum(word_entropies, axis=1)

        return scores
