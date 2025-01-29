from wordle_solver.guesser import WordleGuesser
import numpy as np
import time


def prompt_language_selection() -> str:
    language_options = ["english", "german", "austrian", "spanish"]
    print("\nPick a language from the following:")
    print(f"\t{', '.join(language_options).title()}")

    valid_langauge_selected = False
    while not valid_langauge_selected:
        selected_language = input("").strip().lower()
        if selected_language not in language_options:
            print(f"Sorry {selected_language} is not avialable, please pick from the following:")
            print(f"\t{', '.join(language_options).title()}")
            continue
        valid_langauge_selected = True

    return selected_language


class WordleTerminalHelper:
    def __init__(self, language = None):
        print("Wordle Terminal Helper for all your Wordle Helper Needs")
        if language is None:
            language = prompt_language_selection()
        self.wordle_guesser = WordleGuesser(language=language)
        print("Your Wordle Helper has been set up!")

        self.data = {"words": [], "feedback": []}

    def prompt_guess_and_feedback(self, attempt):
        print(
            f"\nAttempt {attempt}: Please enter your guess, "
            f"proceeded with the feedback using 'g' (green), 'y' (yellow), and 'w' (white)."
        )
        while True:
            word = input("Enter your word guess (or 'exit' to quit): ").strip()
            if word.lower() == 'exit':
                return None, None
            if len(word) != 5:
                print(f"Sorry, `{word}` was not valid, please try again :)")
                continue

            encoded_word = self.wordle_guesser.word_bank.encode_word(word.lower())
            if len(encoded_word) != 5 or encoded_word.min() < 0:
                print(f"Sorry, `{word}` was not valid, please try again :)")
                continue
            encoded_word_in_wordbank = np.any(np.all(self.wordle_guesser.word_bank.full_word_bank == encoded_word, axis=1))
            if not encoded_word_in_wordbank:
                print(f"Sorry, `{word}` was not valid, please try again :)")

            break


        while True:
            feedback = input("Enter your guesses feedback (e.g., 'ggwyw') (or 'exit' to quit): ").strip()
            if feedback.lower() == 'exit':
                None, None

            if len(feedback) != len(word) or any(c not in 'gyw' for c in feedback.lower()):
                print(f"Sorry, `{feedback}` was not in the valid feedback format. Use only 'g', 'y', and 'w'.\n")
                continue
            break

        return word.lower(), feedback.lower()

    def reset_game(self) -> None:
        self.data = {"words": [], "feedback": []}

    @staticmethod
    def format_feedback(feedback):
        format_dict = {
            'g': 'green',
            'y': 'yellow',
            'w': 'gray'
        }
        formatted_feedback = [format_dict[feedback_char] for feedback_char in feedback]
        return formatted_feedback

    def generate_guesses(self, hardcore_mode=False, num_best_guesses=1):
        self.wordle_guesser.process_guesses(self.data['words'], self.data['feedback'])

        self.wordle_guesser.scorer.toggle_mode(hardcore_mode=hardcore_mode)
        best_guesses = self.wordle_guesser.best_guess(num_best_guesses)
        return best_guesses

    def play(self):
        attempts = [1, 2, 3, 4, 5, 6]

        for attempt in attempts:
            print('Processing feedback and generating guesses...')
            start_time = time.perf_counter()
            best_guesses = self.generate_guesses(num_best_guesses=3)
            end_time = time.perf_counter()
            print(f'Optimal Guesses found! [Took {end_time - start_time:.5f}s]')
            print(f'Optimal Guess(es) are:\t{", ".join(best_guesses).title()}')

            word, feedback = self.prompt_guess_and_feedback(attempt)
            self.data['words'].append(word)
            self.data['feedback'].append(self.format_feedback(feedback))

            if word is None:
                print('Sorry to see you go, but hope you had fun playing')
                break
            if feedback == 'ggggg':
                print('Congrats, you did it!')
                break


def main():
    wordle_helper = WordleTerminalHelper(language='english')
    wordle_helper.play()


if __name__ == "__main__":
    main()
