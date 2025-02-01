import warnings
from dataclasses import dataclass, field
import numpy as np


@dataclass
class Hyperparameters:
    """
    Hyperparameters for the word guessing logic, including position-specific weights
    for vowels and consonants, as well as penalties for repeated letters and mismatches.

        - vowel_position_weights (array): List of weights assigned to vowels at each position in the word.
        - consonant_position_weights (array): List of weights assigned to consonants at each position.
        - repeat_letter_penalty (float): Penalty applied when a word contains repeated letters.
        - mismatch_penalty (float): Penalty applied for letters that are in the word but not in the correct position.
        - invalid_word_decay_rate_penalty (float): Used to calculate penalty applied to words that are not valid answers
        - max_guesses (int): The maximum number of guesses allowed during the game.
        - hardcore_mode (bool): Using the full word bank or just the possible word bank as guessing possibilities
    """
    vowel_pos_weights: np.ndarray = field(default_factory=lambda: np.array([1.2, 1.2, 1.2, 1.2, 1.2]))
    consonant_pos_weights: list[float] = field(default_factory=lambda: np.array([1.5, 1.0, 1.2, 1.1, 1.5]))
    repeat_letter_penalty: float = 1.3
    mismatch_penalty: float = 2.0
    invalid_word_decay_rate_penalty: float = 0.5
    max_guesses: int = 6

    hardcore_mode: bool = False

    def __post_init__(self):
        """
        Optional validation to ensure all hparams are within valid ranges
        and issue warnings for unconventional settings.
        """
        if not all(weight > 0 for weight in self.vowel_pos_weights):
            raise ValueError("All vowel position weights must be positive.")
        if not all(weight > 0 for weight in self.consonant_pos_weights):
            raise ValueError("All consonant position weights must be positive.")
        if self.repeat_letter_penalty <= 0:
            raise ValueError("Repeat letter penalty must be positive.")
        if self.mismatch_penalty <= 0:
            raise ValueError("Mismatch penalty must be positive.")
        if self.invalid_word_decay_rate_penalty <= 0:
            raise ValueError("Non-answer decay rate must be positive.")
        if self.max_guesses <= 0:
            raise ValueError("Max guesses must be a positive integer.")
        if not isinstance(self.hardcore_mode, bool):
            raise ValueError("Hardcore mode must be a boolean")

        # Issue a warning if max_guesses is not the conventional value of 6
        if self.max_guesses != 6:
            warnings.warn(
                f"max_guesses is set to {self.max_guesses}, which differs from the conventional value of 6.",
                UserWarning
            )