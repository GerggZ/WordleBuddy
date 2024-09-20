import heapq
from typing import Dict, Optional, Type, List
from math import log2
from collections import defaultdict
from hyperparameters import Hyperparameters
from typing import List, Tuple, Union


class ScoreCalculatorBase:
    """Base class for score calculators."""

    def __init__(
            self,
            full_word_bank: List[str],
            hyperparameters: Optional[type] = None
    )-> None:
        """Initialize the score calculator with word bank.

        Args:
            :param full_word_bank: List of all available words
            :param hyperparameters: Optional dictionary of hyperparameters for score calculator
        """
        self.full_word_bank = full_word_bank
        self.hyperparameters = hyperparameters

    def __call__(self, word: str) -> Union[int, float]:
        """Calculate and provide the score for the given word.

        Args:
            :param word: The word for which to calculate the score.
            :param attempt_num: The current attempt number.

        Returns:
            The calculated score for the word --> Larger score should be considered better
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def update_word_bank(self, possible_word_bank: List[str], attempt_num: int) -> None:
        """Update the word bank used for scoring.

        Args:
            :param possible_word_bank: List of words remaining after filtering.
            :param attempt_num: The current attempt number.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def calculate_score(self, word: str, attempt_num: int) -> float:
        """Calculate the score for a given word.

        Args:
            :param word: current word which is to be considered and scored.
            :param attempt_num: The current attempt number.
        """
        raise NotImplementedError("Subclasses should implement this method.")


class GuessHelper:
    """A class for Wordle guessing, managing word banks and scoring."""

    def __init__(
            self,
            full_word_bank: List[str],
            score_calculator_class: Type[ScoreCalculatorBase],
            hyperparameters: Optional[type] = None,
            hardcore_mode: bool = True
    ) -> None:
        """Initialize GuesserHelper with a word bank and hardcore switch

        Args:
            :param full_word_bank: List of all possible words to guess from.
            :param score_calculator_class: Class type of the score calculator to be used.
            :param hyperparameters: Optional dictionary of hyperparameters for the score calculator.
            :param hardcore_mode: Switch between using only the remaining words or all words.
        """
        self.full_word_bank = full_word_bank
        self.possible_word_bank = full_word_bank.copy()
        self.hardcore_mode = hardcore_mode

        self.score_calculator = score_calculator_class(full_word_bank, hyperparameters)

    def find_optimal_guesses(self, attempt_num: int, num_best: int = 5, num_worst: int = 3) -> Tuple[List[Tuple[float, str]], List[Tuple[float, str]]]:
        """Identifies the top 'num_best' and bottom 'num_worst' words based on their calculated scores.

        Args:
            :param attempt_num: Attempt number (i.e., 0 through 5 for Wordle NYT)
            :param num_best: Top N best options based on the calculated score
            :param num_worst: Top N worst options based on the calculated score
        Returns:
            :return: Lists of best and worst word options along with scores;
        """
        # Initiate class for calculating the score
        if self.score_calculator is None:
            raise ValueError("ScoreCalculator is not initialized. Please use a subclass.")

        # Update the score calculator with the current possible word bank
        self.score_calculator.update_word_bank(self.possible_word_bank, attempt_num)

        # Heaps for tracking best and worst words
        best_words_heap, worst_words_heap = [], []

        # select word bank based on playing mode
        word_bank = self.possible_word_bank if self.hardcore_mode else self.full_word_bank

        for word in word_bank:
            word_score = self.score_calculator(word)

            # Track top 'num_best' words using a max-heap
            if len(best_words_heap) < num_best:
                heapq.heappush(best_words_heap, (word_score, word))
            else:
                heapq.heappushpop(best_words_heap, (word_score, word))

            # Track bottom 'num_worst' words using a min-heap (negated max-heap)
            if len(worst_words_heap) < num_worst:
                heapq.heappush(worst_words_heap, (-word_score, word))
            else:
                heapq.heapreplace(worst_words_heap, (-word_score, word))

        # Convert heaps to sorted lists for output
        best_words = sorted([(word, score) for score, word in best_words_heap], reverse=True)
        worst_words = sorted([(word, -score) for score, word in worst_words_heap])

        return best_words, worst_words

    def cull_possible_word_bank(self, guessed_word: str, guessed_word_info: str) -> None:
        """Adjusts the possible word bank based on new information from the guess

        Args:
            :param guessed_word: the word which was guessed
            :param guessed_word_info: the information gained about the word
                                      (i.e., what is green, yellow, or white)

        Raises:
            ValueError: If the selected_word is not in the word bank,
                        if word_info contains invalid characters,
                        or if word_info is not 5 characters long.
        """
        # Validate inputs
        if guessed_word not in self.full_word_bank:
            raise ValueError(f"Error: '{guessed_word}' was not in the word bank")
        if not set(guessed_word_info).issubset({'g', 'y', 'w'}):
            raise ValueError(f"Error: Feedback string '{guessed_word_info}' contains invalid characters, only 'g', 'y', and 'w' allowed")
        if len(guessed_word_info) != 5:
            raise ValueError(f"Error: Feedback string '{guessed_word_info}' must be 5 characters long")

        letter_counts = {}  # Count occurrences of 'g' and 'y' labeled letters

        # Count green ('g') and yellow ('y') labeled letters
        for char, char_info in zip(guessed_word, guessed_word_info):
            if char_info in ('g', 'y'):
                letter_counts[char] = letter_counts.get(char, 0) + 1

        # Cull the possible word bank based on the last guess
        for position, (char, char_info) in enumerate(zip(guessed_word, guessed_word_info)):
            if char_info == 'g':  # Green: letter must be in this exact position
                self.possible_word_bank = [
                    word for word in self.possible_word_bank
                    if word[position] == char
                ]

            elif char_info == 'y':  # Yellow: letter must be in the word, but not in this position
                self.possible_word_bank = [
                    word for word in self.possible_word_bank
                    if char in word and word[position] != char
                ]

            elif char_info == 'w':  # White: handled based on previous letter occurence information
                if letter_counts.get(char, 0) == 0:  # No previous green or yellow for the letter
                    self.possible_word_bank = [
                        word for word in self.possible_word_bank
                        if char not in word
                    ]

                else:  # There was a previous green or yellow occurrence of this letter
                    self.possible_word_bank = [
                        word for word in self.possible_word_bank
                        if word.count(char) <= letter_counts[char] and word[position] != char
                    ]


class EntropyScoreCalculator(ScoreCalculatorBase):
    """Score calculator that uses entropy-based calculations for scoring words."""
    def __call__(self, word: str) -> float:
        """Calculate the total entropy for a given word based on feedback.

        Args:
            :param word: The word for which to calculate the entropy.

        Returns:
            The calculated entropy score for the word.
        """
        score = 0
        vowels = "aeiou"
        letter_counts = defaultdict(int)  # Automatically initializes counts to 0

        for pos, char in enumerate(word):
            # include the letter in the dictionary
            letter_counts[char] += 1

            # Calculate entropies
            green_entropy = self.calculate_green_entropy(char, pos)
            yellow_entropy = self.calculate_yellow_entropy(char, pos)
            white_entropy = self.calculate_white_entropy(char)

            # Calculate White (not in the word) entropy
            if letter_counts[char] > 1:
                white_entropy = 0  # set white entropy to 0 if letter is already looked at
                diminishing_factor = 1 / letter_counts[char]
                yellow_entropy *= diminishing_factor  # introduce diminishing factor for repeated letters

            # Combine the entropies with positional weights
            char_weight = self.hyperparameters.vowel_pos_weights[pos] if char in vowels else self.hyperparameters.consonant_pos_weights[pos]
            score += char_weight * (green_entropy + yellow_entropy + white_entropy)

        # Apply an additional weight if the word is a potential answer
        if word in self.possible_word_bank:
            answer_weight = self.hyperparameters.answer_weight_base * (1 + self.attempt_num / self.hyperparameters.max_guesses)
            score *= answer_weight

        return score

    def update_word_bank(self, possible_word_bank: List[str], attempt_num: int) -> None:
        """Update the word bank and calculate letter frequencies.

        Args:
            :param possible_word_bank: The list of words remaining after filtering based on previous guesses.
            :param attempt_num: The current attempt number for tracking purposes.
        """
        self.possible_word_bank = possible_word_bank
        self.letter_frequencies = self.count_letter_frequencies()
        self.attempt_num = attempt_num
        self.total_words_list = len(possible_word_bank)

    def count_letter_frequencies(self) -> Dict[int, Dict[str, int]]:
        """Counts the frequency of each letter in each position across the list of possible words.

        Returns:
            A dictionary where each key is a position (0-4) and each value is another dictionary
            mapping letters to their frequency at that position.
        """
        letter_frequencies = defaultdict(lambda: defaultdict(int))

        for word in self.possible_word_bank:
            for pos, char in enumerate(word):
                letter_frequencies[pos][char] += 1

        return dict(letter_frequencies)

    def calculate_green_entropy(self, char: str, pos: int) -> float:
        """
        Calculates the entropy for whether the letter is in the correct position (Green feedback).

        Args:
            char (str): The letter being checked.
            pos (int): The position of the letter being evaluated.

        Returns:
            float: The entropy for the position.
        """
        frequency = self.letter_frequencies[pos].get(char, 0)

        if frequency == 0 or frequency >= self.total_words_list:
            return float(0)  # No information gain if frequency is 0 or equals total words

        p = frequency / self.total_words_list
        entropy = -p * log2(p) - (1 - p) * log2(1 - p)

        return entropy

    def calculate_yellow_entropy(self, char: str, pos: int) -> float:
        """
        Calculates the entropy for whether the letter is in the word but in a different position (Yellow feedback).

        Args:
            char (str): The letter being checked.
            pos (int): The current position of the letter being evaluated.

        Returns:
            float: The entropy for the letter being in other positions (Yellow feedback).
        """
        other_position_frequency = sum(
            self.letter_frequencies[other_pos].get(char, 0) for other_pos in range(len(self.letter_frequencies)) if other_pos != pos
        )

        if other_position_frequency == 0 or other_position_frequency >= self.total_words_list:
            return float(0)  # No information gain if it's never or always in other positions

        p = other_position_frequency / self.total_words_list
        entropy = -p * log2(p) - (1 - p) * log2(1 - p)

        return entropy

    def calculate_white_entropy(self, char: str) -> float:
        """
        Calculates the entropy for whether the letter is not in the word at all (White feedback).

        Args:
            char (str): The letter being checked.

        Returns:
            float: The entropy for the letter not being in the word (White feedback).
        """
        total_char_frequency = sum(
            self.letter_frequencies[pos].get(char, 0) for pos in range(len(self.letter_frequencies))
        )

        if total_char_frequency == 0 or total_char_frequency >= self.total_words_list:
            return float(0)  # No information gain if it's never or always in the word

        p = total_char_frequency / self.total_words_list
        entropy = -p * log2(p) - (1 - p) * log2(1 - p)

        return entropy


class HardCodedCalculator(ScoreCalculatorBase):
    """
    Estimates how many words will be left after every guess
    """
    # Not yet Implemented