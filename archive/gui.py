import tkinter as tk
from tkinter import messagebox


class GUIApp:
    def __init__(self, root, guesser_helper):
        self.root = root
        self.guesser_helper = guesser_helper  # Inject guesser_helper here
        self.root.title("Wordle Game")

        self.attempt_num = 0  # Track the number of attempts

        # Set up the Word to Guess
        self.word_to_guess = tk.StringVar()
        self.word_entry = tk.Entry(root, textvariable=self.word_to_guess, font=('Arial', 14))
        self.word_entry.grid(row=0, column=1, columnspan=5, padx=10, pady=10)

        self.set_word_button = tk.Button(root, text="Set Word", command=self.set_word)
        self.set_word_button.grid(row=0, column=6, padx=10, pady=10)

        # Set up guess input area
        self.guess = tk.StringVar()
        self.guess_entry = tk.Entry(root, textvariable=self.guess, font=('Arial', 14))
        self.guess_entry.grid(row=1, column=1, columnspan=5, padx=10, pady=10)

        self.submit_button = tk.Button(root, text="Submit", command=self.submit_guess)
        self.submit_button.grid(row=1, column=6, padx=10, pady=10)

        # Grid for results display
        self.result_labels = [
            [tk.Label(root, text="", width=5, height=2, font=('Arial', 14), relief="solid") for _ in range(5)] for _ in
            range(6)]
        for i in range(6):
            for j in range(5):
                self.result_labels[i][j].grid(row=i + 2, column=j + 1, padx=5, pady=5)

        self.current_row = 0

        # Create a frame for displaying best and worst guesses
        self.guess_info_frame = tk.Frame(root)
        self.guess_info_frame.grid(row=0, column=0, rowspan=8, padx=10, pady=10)

        self.best_guesses_label = tk.Label(self.guess_info_frame, text="Best Guesses:", font=('Arial', 12))
        self.best_guesses_label.grid(row=0, column=0, sticky='w')

        self.best_guesses_text = tk.Label(self.guess_info_frame, text="", font=('Arial', 10), justify='left',
                                          wraplength=200)
        self.best_guesses_text.grid(row=1, column=0, sticky='w')

        self.worst_guesses_label = tk.Label(self.guess_info_frame, text="Worst Guesses:", font=('Arial', 12))
        self.worst_guesses_label.grid(row=2, column=0, sticky='w')

        self.worst_guesses_text = tk.Label(self.guess_info_frame, text="", font=('Arial', 10), justify='left',
                                           wraplength=200)
        self.worst_guesses_text.grid(row=3, column=0, sticky='w')

    def set_word(self):
        word = self.word_to_guess.get().lower()
        if len(word) != 5:
            messagebox.showerror("Error", "Please enter a 5-letter word!")
        else:
            self.secret_word = word
            self.word_entry.config(state='disabled')
            self.set_word_button.config(state='disabled')

            # Call the guesser_helper to get best and worst guesses before processing the guess
            best_guesses, worst_guesses = self.guesser_helper.find_optimal_guesses(self.attempt_num)
            self.update_guess_info(best_guesses, worst_guesses)

    def submit_guess(self):
        guess = self.guess.get().lower()
        if len(guess) != 5:
            messagebox.showerror("Error", "Please enter a 5-letter guess!")
            return None  # No result if the guess is invalid

        result = ["w"] * 5  # Default all letters to 'w' (wrong)

        if self.current_row < 6:
            # Track remaining letter counts in the secret word
            remaining_letters = {}
            for letter in self.secret_word:
                remaining_letters[letter] = remaining_letters.get(letter, 0) + 1

            # First pass: mark green and decrease count for correct letters
            for i, letter in enumerate(guess):
                if letter == self.secret_word[i]:
                    self.result_labels[self.current_row][i].config(text=letter, bg="green", fg="white")
                    result[i] = 'g'  # Mark as green in result string
                    remaining_letters[letter] -= 1  # Correct position letter used

            # Second pass: mark yellow and decrease count for misplaced letters
            for i, letter in enumerate(guess):
                if letter != self.secret_word[i]:  # Skip if already marked green
                    if letter in remaining_letters and remaining_letters[letter] > 0:
                        self.result_labels[self.current_row][i].config(text=letter, bg="yellow", fg="black")
                        result[i] = 'y'  # Mark as yellow in result string
                        remaining_letters[letter] -= 1  # Misplaced letter used
                    else:
                        self.result_labels[self.current_row][i].config(text=letter, bg="gray", fg="white")
                        result[i] = 'w'  # Mark as white (wrong letter)

            self.current_row += 1
            self.guess.set("")  # Clear the guess input field

            gyw_string = ''.join(result)  # Return result string (e.g., "gywgw")

            # Call GuesserHelper to update it with the guess and result string
            self.guesser_helper.cull_possible_word_bank(guess, gyw_string)
            # Call the guesser_helper to get best and worst guesses before processing the guess
            best_guesses, worst_guesses = self.guesser_helper.find_optimal_guesses(self.attempt_num)
            self.update_guess_info(best_guesses, worst_guesses)

            self.attempt_num += 1  # Increment attempt number
        else:
            messagebox.showinfo("Game Over", "You've used all your attempts!")

    def update_guess_info(self, best_guesses, worst_guesses):
        """Update the labels showing best and worst guesses."""

        best_guess_str = ", ".join([f"\t{word}: {score:.3f}\n" for score, word in best_guesses])
        worst_guess_str = ", ".join([f"\t{word}: {score:.3f\n}" for score, word in worst_guesses])
        best_guesses_str = f"{best_guess_str}"
        worst_guesses_str = f"{worst_guess_str}"

        # Update the GUI labels with the formatted strings
        self.best_guesses_text.config(text=best_guesses_str)
        self.worst_guesses_text.config(text=worst_guesses_str)
