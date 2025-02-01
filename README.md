# WordleBuddy

A Python-based Wordle solver that assists in solving Wordle puzzles by processing feedback from guesses and narrowing down possible word choices. The solver can be used both through a terminal-based interface or by importing the `WordleGuesser` class.

## Features

- **Interactive Terminal Version**: A simple command-line interface to make guesses and get optimal word suggestions based on your feedback.
- **Word Bank Management**: Supports different languages for the word bank (e.g., English, German, Austrian, Spanish).
- **Feedback Processing**: Provides guesses based on Wordle feedback with green (g), yellow (y), and gray (w) characters.
- **Optimized Guessing**: Suggests the best guesses based on previous guesses and feedback.

## Installation

You can install `wordle_buddy` directly using pip:

```bash
pip install wordle_buddy
```

## Usage

There are two main ways to use the Wordle Buddy:

### 1. Terminal Version

You can run the terminal-based version directly from the command line:

```bash
python terminal_version.py
```

This will prompt you for guesses and feedback interactively. The program will suggest optimal guesses based on the provided feedback.

### 2. Importing and Using in Your Code

You can also import and use the solver in your Python projects:

```python
from wordle_buddy.guesser import WordleGuesser

# Create an instance of the WordleGuesser class
wordle_guesser = WordleGuesser(language='english')

# Example of processing guesses and feedback
wordle_guesser.process_guesses(["CRIMP", "CLIMB"], [["gray", "green", "green", "gray", "yellow"], ["gray", "gray", "green", "gray", "gray"]])
best_guesses = wordle_guesser.best_guess(num_best_guesses=3)
print(f"Best guesses: {', '.join(best_guesses)}")
```

### Understanding the Feedback

- **Green (g)**: Correct letter, correct position.
- **Yellow (y)**: Correct letter, wrong position.
- **White (w)**: Incorrect letter.

### `WordleTerminalHelper` Class

The terminal version of the game uses the `WordleTerminalHelper` class, which helps you interact with the solver. It includes:

- **Guessing and Feedback**: Prompts the user for word guesses and feedback, processes the feedback, and provides optimal guesses.
- **Hardcore Mode**: An option to make the guesses more optimized (e.g., fewer possibilities).
  
### Main Game Loop

You can follow the game’s main loop using the `play()` method, which:

1. Prompts the user for guesses and feedback.
2. Suggests optimal guesses based on prior feedback.
3. Continues until the puzzle is solved or the user exits.

## Project Structure

- `wordle_buddy/`
  - `__init__.py`: Marks the directory as a package.
  - `guesser.py`: Contains the core `WordleGuesser` class with logic for processing guesses and generating optimal guesses.
  - `english_word_bank.txt`: A list of valid English words for the game (stored in a text file).
- `terminal_version.py`: A command-line interface to interact with the Wordle Buddy.
- `requirements.txt`: Lists any required Python dependencies.

## Contribution

Feel free to fork the project, open issues, or create pull requests for new features and improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

