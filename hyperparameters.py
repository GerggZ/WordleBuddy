from typing import List


class Hyperparameters:
    """
    Hyperparameters for the word guessing logic, including position-specific weights
    for vowels and consonants, as well as penalties for repeated letters and mismatches.
    """

    def __init__(self,
                 vowel_pos_weights: List[float] = [1.2, 1.2, 1.2, 1.2, 1.2], # Default weights for vowels at each position
                 consonant_pos_weights: List[float] = [1.5, 1.0, 1.2, 1.1, 1.5],  # Default weights for consonants
                 repeat_letter_penalty: float = 1.3,  # Penalty for words with repeated letters
                 mismatch_penalty: float = 2.0,  # Penalty for positional mismatches
                 answer_weight_base: float = 1.0,  # Base weight for "can be an answer" factor
                 max_guesses: int = 6  # Base number of guessing rounds possible
                 ):
        """Initialize hyperparameters for the word guessing logic.

        Args:
            :param vowel_position_weights: List of weights assigned to vowels at each position in the word.
            :param consonant_position_weights: List of weights assigned to consonants at each position.
            :param repeat_letter_penalty: Penalty applied when a word contains repeated letters.
            :param mismatch_penalty: Penalty applied for letters that are in the word but not in the correct position.
            :param answer_weight_base: Base weight used to adjust scoring for words that can be valid answers.
            :param max_guesses: The maximum number of guesses allowed during the game.
        """

        # Assign the provided or default positional weights for vowels and consonants
        self.vowel_pos_weights: List[float] = vowel_pos_weights  # Vowel positional weights
        self.consonant_pos_weights: List[float] = consonant_pos_weights  # Consonant positional weights

        # Penalties for repeating letters and incorrect positions
        self.repeat_letter_penalty: float = repeat_letter_penalty  # Penalty for repeated letters
        self.mismatch_penalty: float = mismatch_penalty  # Penalty for letters in incorrect positions

        # Base weight for "can be an answer" adjustment based on guesses left and possible words left
        self.answer_weight_base: float = answer_weight_base  # Base weight for words that could be valid answers

        self.max_guesses = max_guesses
