import numpy as np

from wordle_buddy.utils.word_bank_manager import WordBankManager
from wordle_buddy.utils.word_scorer_entropy import WordScorerEntropy
from wordle_buddy.utils.hyperparameters import Hyperparameters


class WordleGuesser:
    """
    Main class that manages Wordle guessing logic.
    Uses WordBankManager for word storage and WordScorer for ranking guesses.
    """

    def __init__(self, language: str, hparams: "Hyperparameters" = Hyperparameters()) -> None:
        """
        Initializes the WordleGuesser with a specific language.

        Args:
            - language: The language of the word bank (e.g., 'english', 'german', 'austrian', 'spanish').
            - hparams: Hyperparameters object for entropy calculations.
        """
        self.word_bank = WordBankManager(language)  # Load word bank
        self.scorer = WordScorerEntropy(self.word_bank, hparams)  # Attach entropy-based scorer

        self.attempts = []

    def process_guess(self, guess: str, feedback: list):
        """
        Processes a single guess, updates the possible word list, and stores the attempt.

        :param guess: The guessed word (string).
        :param feedback: A list of feedback ('gray', 'yellow', 'green') for each letter.
        """
        guess = self.word_bank.encode_word(guess)  # Convert guess to ascii
        self.word_bank.cull(guess, feedback)
        self.attempts.append((guess, feedback))

    def process_guesses(self, guesses: list, feedbacks: list):
        """
        Processes multiple past guesses and feedback, resetting the game first.
        This ensures the word bank is culled before selecting the next best word.

        :param guesses: List of guessed words (strings).
        :param feedbacks: List of feedback lists corresponding to each guess.
        """
        if len(guesses) != len(feedbacks):
            raise ValueError("The number of guesses and feedbacks must match.")

        self.reset_game()  # Reset the word bank before processing
        for guess, feedback in zip(guesses, feedbacks):
            self.process_guess(guess.lower(), feedback)

    def best_guess(self, num_best_guesses: int = 1) -> list:
        """
        Returns the top `num_best_guesses` best words based on entropy scoring.

        :param num_best_guesses: Number of best guesses to return.
        :return: A list of the best words as strings, sorted by entropy score.
        """
        if self.word_bank.possible_word_bank.size == 0:
            # the word bank is empty, something horrible has happened
            return ['No Viable Guesses']

        scores = self.scorer.score_word_bank(attempt_num=len(self.attempts) + 1)
        num_available = len(self.scorer.current_word_bank)

        # Ensure we don't request more than available words
        num_best_guesses = min(num_best_guesses, num_available)

        best_indices = np.argsort(scores)[::-1][:num_best_guesses]
        best_guesses_ascii = [
            self.scorer.working_word_bank[i]
            for i in best_indices
            if scores[i] > 0
        ]
        best_guesses_chars = [self.word_bank.decode_word(word) for word in best_guesses_ascii]

        if not best_guesses_chars:
            # there was no positive score, something horrible has happened
            return ['No Viable Guesses']
        # Return best guesses as a list of strings
        return best_guesses_chars

    def reset_game(self):
        """Resets the word list and clears previous attempts."""
        self.word_bank.reset()
        self.attempts.clear()

    def display_word_counts(self):
        """Displays the number of possible words remaining."""
        print(f"Total words in bank: {len(self.word_bank.full_word_bank)}")
        print(f"Possible remaining words: {len(self.word_bank.possible_word_bank)}")

    def show_attempts(self):
        """Displays previous guesses and feedback."""
        for attempt, feedback in self.attempts:
            print(f"Guess: {attempt} → Feedback: {feedback}")
