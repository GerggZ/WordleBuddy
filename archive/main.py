from utils import determine_language, get_word_bank, get_valid_word_and_info
from guessing import GuessHelper, EntropyScoreCalculator
from hyperparameters import Hyperparameters
from gui import GUIApp
import tkinter as tk

def setup():
    """
    Sets up wordle analyzer with language of choice
    and relevant dataset
    """

    # language = determine_language()
    language = 'english'
    word_bank = get_word_bank(language)

    # Define hyperparameters with refined focus on impactful factors
    custom_hyperparameters = Hyperparameters()

    return word_bank, custom_hyperparameters

def main():
    word_bank, custom_hyperparameters = setup()
    guesser_helper = GuessHelper(
        full_word_bank=word_bank, ScoreCalculator=EntropyScoreCalculator,
        hyperparameters=custom_hyperparameters, hardcore_mode=True
    )
    # Create the GUI
    root = tk.Tk()
    app = GUIApp(root, guesser_helper)
    root.mainloop()

    j = 7

    # for attempt in range(6):
    #     print(f"Attempt {attempt + 1}:")
    #
    #     # Find the best guesses (you can adjust the number of guesses to return)
    #     best_guesses, worst_guesses = guesser_helper.find_optimal_guesses(attempt, num_best=10, num_worst=10)
    #
    #     best_guess_str = ", ".join([f"{word}: {score:.3f}" for score, word in best_guesses])
    #     worst_guess_str = ", ".join([f"{word}: {score:.3f}" for score, word in worst_guesses])
    #     print(f"\t\tBest Guesses: {best_guess_str}")
    #     print(f"\t\tWorst Guesses: {worst_guess_str}")
    #
    #     selected_word_and_info = get_valid_word_and_info()
    #
    #     if selected_word_and_info[1] == 'ggggg':
    #         print(f"Word solved! The word is {selected_word_and_info[0]}")
    #         break
    #
    #     # Update word bank based on feedback from the guess
    #     # For simplicity, we'll just remove the selected word from the word bank
    #     guesser_helper.cull_possible_word_bank(*selected_word_and_info)
    #
    #     # Break the loop if only one word remains (indicating a win)
    #     if len(guesser_helper.possible_word_bank) == 1:
    #         print(f"Word solved! The word is {guesser_helper.possible_word_bank[0]}")
    #         break


if __name__ == '__main__':
    main()
