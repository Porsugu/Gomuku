import numpy as np
import os
import time
import tkinter as tk
from tkinter import messagebox, Frame, Button, Label, StringVar, IntVar, Radiobutton


class GomokuGame:
    def __init__(self, board_size=15):
        self.board_size = board_size
        self.board = np.zeros((board_size, board_size), dtype=int)
        self.current_player = 1  # 1 represents black stones, 2 represents white stones
        self.game_over = False
        self.winner = None

    def reset_game(self):
        """Reset the game"""
        self.board = np.zeros((self.board_size, self.board_size), dtype=int)
        self.current_player = 1
        self.game_over = False
        self.winner = None

    def make_move(self, row, col):
        """Place a stone at the specified position"""
        if self.game_over:
            return False

        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            return False

        if self.board[row, col] != 0:
            return False

        self.board[row, col] = self.current_player

        # Check if the game is over
        if self.check_win(row, col):
            self.game_over = True
            self.winner = self.current_player
        elif np.all(self.board != 0):  # Check for a draw
            self.game_over = True

        # Switch player
        self.current_player = 3 - self.current_player  # 1->2, 2->1
        return True

    def check_win(self, row, col):
        """Check if there are five consecutive stones from the last move"""
        player = self.board[row, col]
        directions = [
            (0, 1),  # horizontal
            (1, 0),  # vertical
            (1, 1),  # diagonal
            (1, -1)  # anti-diagonal
        ]

        for dr, dc in directions:
            count = 1  # including the current position

            # Check one direction
            for i in range(1, 5):
                r, c = row + dr * i, col + dc * i
                if not (0 <= r < self.board_size and 0 <= c < self.board_size) or self.board[r, c] != player:
                    break
                count += 1

            # Check the opposite direction
            for i in range(1, 5):
                r, c = row - dr * i, col - dc * i
                if not (0 <= r < self.board_size and 0 <= c < self.board_size) or self.board[r, c] != player:
                    break
                count += 1

            if count >= 5:
                return True

        return False

    def display_board(self):
        """Display the board"""
        os.system('cls' if os.name == 'nt' else 'clear')

        print("  " + " ".join([f"{i}" for i in range(10)]) + " " + " ".join(
            [chr(i + 65 - 10) for i in range(10, self.board_size)]))

        for i in range(self.board_size):
            row_str = f"{i} " if i < 10 else f"{chr(i + 65 - 10)} "

            for j in range(self.board_size):
                if self.board[i, j] == 0:
                    # Special markings for corners and center point
                    if (i == 0 or i == self.board_size - 1 or i == self.board_size // 2) and \
                            (j == 0 or j == self.board_size - 1 or j == self.board_size // 2):
                        row_str += "+ "
                    else:
                        row_str += ". "
                elif self.board[i, j] == 1:
                    row_str += "○ "  # Black stone
                else:
                    row_str += "● "  # White stone

            print(row_str)

        player_name = "Black(○)" if self.current_player == 1 else "White(●)"
        print(f"\nCurrent Player: {player_name}")

        if self.game_over:
            if self.winner:
                winner_name = "Black(○)" if self.winner == 1 else "White(●)"
                print(f"Game Over! {winner_name} wins!")
            else:
                print("Game Over! It's a draw!")

    def get_valid_moves(self):
        """Get all valid move positions"""
        valid_moves = []

        # Optimization: only consider empty positions around existing stones
        if np.any(self.board != 0):  # If there are stones on the board
            for i in range(self.board_size):
                for j in range(self.board_size):
                    if self.board[i, j] == 0:  # Empty position
                        # Check if there are stones in 8 directions
                        has_neighbor = False
                        for di in [-1, 0, 1]:
                            for dj in [-1, 0, 1]:
                                if di == 0 and dj == 0:
                                    continue
                                ni, nj = i + di, j + dj
                                if 0 <= ni < self.board_size and 0 <= nj < self.board_size and self.board[ni, nj] != 0:
                                    has_neighbor = True
                                    break
                            if has_neighbor:
                                break

                        if has_neighbor:
                            valid_moves.append((i, j))
        else:  # If the board is empty, return the center position
            valid_moves.append((self.board_size // 2, self.board_size // 2))

        return valid_moves


class GomokuAI:
    def __init__(self, game, max_depth=3):
        self.game = game
        self.max_depth = max_depth

    def _calculate_separation(self, board, whose_turn):
        opponent = 3 - whose_turn
        size = len(board)

        my_pieces = []
        opponent_pieces = []

        for i in range(size):
            for j in range(size):
                if board[i, j] == whose_turn:
                    my_pieces.append((i, j))
                elif board[i, j] == opponent:
                    opponent_pieces.append((i, j))

        if not my_pieces or not opponent_pieces:
            return 0

        total_min_distance = 0
        for my_i, my_j in my_pieces:
            min_distance = float('inf')
            for opp_i, opp_j in opponent_pieces:
                distance = abs(my_i - opp_i) + abs(my_j - opp_j)
                min_distance = min(min_distance, distance)

            total_min_distance += min_distance

        separation_score = total_min_distance / len(my_pieces)

        return separation_score * 10

    def evaluate_board(self, whose_turn, board):

        opponent = 3 - whose_turn  # 1->2, 2->1

        # Pattern scores
        pattern_scores = {
            5: 100000,  # Five in a row (victory)
            'open_four': 10000,  # Open four
            'half_four': 1000,  # Half-blocked four
            'jump_four': 800,  # Jump four (slightly weaker than half-blocked four)
            'open_three': 500,  # Open three
            'jump_three': 300,  # Jump three (weaker than open three)
            'half_three': 100,  # Half-blocked three
            'open_two': 50,  # Open two
            'half_two': 10  # Half-blocked two
        }

        my_score = 0
        opponent_score = 0

        # Check all rows, columns, and diagonals
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        size = len(board)

        # Check each direction
        for start_i in range(size):
            for start_j in range(size):
                for di, dj in directions:
                    # Skip starting points that would go out of bounds
                    end_i, end_j = start_i + 4 * di, start_j + 4 * dj
                    if not (0 <= end_i < size and 0 <= end_j < size):
                        continue

                    # Extract the stones on this line
                    line = []
                    for step in range(5):
                        i, j = start_i + step * di, start_j + step * dj
                        line.append(board[i, j])

                    # Check my patterns
                    my_pattern = self._check_pattern(line, whose_turn)
                    if my_pattern in pattern_scores:
                        my_score += pattern_scores[my_pattern]

                    # Check opponent's patterns
                    opponent_pattern = self._check_pattern(line, opponent)
                    if opponent_pattern in pattern_scores:
                        opponent_score += pattern_scores[opponent_pattern]

        # return my_score - opponent_score

        separation_score = self._calculate_separation(board, whose_turn)

        score_diff = my_score - opponent_score

        # If current player gets a higher score, increase the separation
        if score_diff > 0:  # Current player gets a higher score
            final_score = my_score - opponent_score + separation_score
        else:
            final_score = my_score - opponent_score - separation_score

        return final_score

    def _check_pattern(self, line, player):

        # Normal
        if line.count(player) == 5:
            return 5

        if line.count(player) == 4 and line.count(0) == 1:
            return 'open_four'

        if line.count(player) == 4 and line.count(3 - player) == 1:
            return 'half_four'

        if line == [0, player, player, player, 0]:
            return 'open_three'

        if line.count(player) == 3 and line.count(0) == 1 and line.count(3 - player) == 1:
            return 'half_three'

        if line == [0, player, player, 0, 0] or line == [0, 0, player, player, 0]:
            return 'open_two'

        if line.count(player) == 2 and line.count(0) == 2 and line.count(3 - player) == 1:
            return 'half_two'

        # Jump3
        if line == [player, 0, player, player, 0] or line == [0, player, 0, player, player] or \
                line == [player, player, 0, player, 0] or line == [0, player, player, 0, player]:
            return 'jump_three'

        # Jump4
        if (line.count(player) == 4 and line.count(0) == 1 and
                (line[1] == 0 or line[2] == 0 or line[3] == 0)):
            return 'jump_four'

        return 0

    def minimax(self, depth, alpha, beta, is_maximizing):

        if self.game.game_over or depth == 0:
            return self.evaluate_board(self.game.current_player, self.game.board), None

        valid_moves = self.game.get_valid_moves()

        if not valid_moves:
            return 0, None

        best_move = None

        if is_maximizing:
            max_eval = float('-inf')
            for row, col in valid_moves:

                board_copy = np.copy(self.game.board)
                current_player = self.game.current_player

                self.game.make_move(row, col)

                eval_score, _ = self.minimax(depth - 1, alpha, beta, False)

                self.game.board = board_copy
                self.game.current_player = current_player
                self.game.game_over = False
                self.game.winner = None

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = (row, col)

                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break

            return max_eval, best_move
        else:
            min_eval = float('inf')
            for row, col in valid_moves:

                board_copy = np.copy(self.game.board)
                current_player = self.game.current_player

                self.game.make_move(row, col)

                eval_score, _ = self.minimax(depth - 1, alpha, beta, True)

                self.game.board = board_copy
                self.game.current_player = current_player
                self.game.game_over = False
                self.game.winner = None

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = (row, col)

                beta = min(beta, eval_score)
                if beta <= alpha:
                    break

            return min_eval, best_move

    def get_best_move(self):

        _, best_move = self.minimax(self.max_depth, float('-inf'), float('inf'), True)
        return best_move


def play_pvp():
    game = GomokuGame()

    while not game.game_over:
        game.display_board()

        try:
            player_input = input("Enter row and column (e.g., 7 7), or 'q' to quit: ")

            if player_input.lower() == 'q':
                break

            row, col = map(int, player_input.split())

            if not game.make_move(row, col):
                print("Invalid move, please try again!")
                time.sleep(1)

        except ValueError:
            print("Input format error, please try again!")
            time.sleep(1)

    game.display_board()
    print("Game Over!")


def play_pve():
    """Player vs AI mode"""
    game = GomokuGame()
    ai = GomokuAI(game)

    # Choose who goes first
    player_choice = input("Which side do you want to choose? (1=Black first, 2=White second): ")
    player = int(player_choice) if player_choice in ['1', '2'] else 1

    while not game.game_over:
        game.display_board()

        if game.current_player == player:
            try:
                player_input = input("Enter row and column (e.g., 7 7), or 'q' to quit: ")

                if player_input.lower() == 'q':
                    break

                row, col = map(int, player_input.split())

                if not game.make_move(row, col):
                    print("Invalid move, please try again!")
                    time.sleep(1)

            except ValueError:
                print("Input format error, please try again!")
                time.sleep(1)
        else:
            print("AI is thinking...")
            time.sleep(0.5)  # Add a visual effect of thinking time

            best_move = ai.get_best_move()
            if best_move:
                row, col = best_move
                game.make_move(row, col)
                print(f"AI chose position: {row} {col}")
                time.sleep(1)

    game.display_board()
    print("Game Over!")


class GomokuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gomoku")
        self.root.resizable(False, False)

        self.cell_size = 40  # Size of each cell
        self.board_size = 15  # Board size
        self.canvas_size = self.cell_size * (self.board_size + 2)  # Add 2 for margins

        # Game mode selection
        self.mode_frame = Frame(self.root, padx=20, pady=20)
        self.mode_frame.pack()

        Label(self.mode_frame, text="Gomoku", font=("Arial", 24, "bold")).pack(pady=10)

        self.game_mode = IntVar(value=1)
        Radiobutton(self.mode_frame, text="Player vs Player (PVP)", variable=self.game_mode, value=1, font=("Arial", 12)).pack(
            anchor=tk.W, pady=5)
        Radiobutton(self.mode_frame, text="Player vs AI (PVE)", variable=self.game_mode, value=2, font=("Arial", 12)).pack(
            anchor=tk.W, pady=5)

        self.player_choice = IntVar(value=1)
        Label(self.mode_frame, text="Choose your stone (PVE mode)", font=("Arial", 12)).pack(anchor=tk.W, pady=5)
        Radiobutton(self.mode_frame, text="Black (First)", variable=self.player_choice, value=1, font=("Arial", 12)).pack(
            anchor=tk.W, pady=2)
        Radiobutton(self.mode_frame, text="White (Second)", variable=self.player_choice, value=2, font=("Arial", 12)).pack(
            anchor=tk.W, pady=2)

        Button(self.mode_frame, text="Start Game", command=self.start_game, font=("Arial", 14), padx=20, pady=10).pack(
            pady=20)

        # Game interface
        self.game_frame = Frame(self.root)
        self.game = None
        self.ai = None
        self.canvas = None
        self.status_var = StringVar(value="Please select a game mode")

    def start_game(self):
        """Start the game"""
        self.mode_frame.pack_forget()
        self.game_frame.pack()

        self.game = GomokuGame(self.board_size)
        if self.game_mode.get() == 2:  # PVE mode
            self.ai = GomokuAI(self.game, max_depth=2)
            self.player = self.player_choice.get()
        else:  # PVP mode
            self.ai = None
            self.player = None

        # Create game interface
        self.create_game_ui()

        # If it's PVE mode and AI goes first, let AI make the first move
        if self.game_mode.get() == 2 and self.player != 1:
            self.ai_move()

    def create_game_ui(self):
        """Create game interface"""
        control_frame = Frame(self.game_frame)
        control_frame.pack(side=tk.TOP, pady=10)

        Label(control_frame, textvariable=self.status_var, font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=20)
        Button(control_frame, text="Restart", command=self.restart_game, font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        Button(control_frame, text="Back to Menu", command=self.back_to_menu, font=("Arial", 10)).pack(side=tk.LEFT,
                                                                                                     padx=5)

        # Create canvas
        canvas_frame = Frame(self.game_frame, padx=20, pady=10)
        canvas_frame.pack()

        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_size, height=self.canvas_size, bg="#DDBB88")
        self.canvas.pack()

        # Draw the board
        self.draw_board()

        # Bind click event
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Update status
        self.update_status()

    def draw_board(self):
        """Draw the board"""
        # Clear canvas
        self.canvas.delete("all")

        # Draw grid
        for i in range(self.board_size):
            # Horizontal lines
            self.canvas.create_line(
                self.cell_size, (i + 1) * self.cell_size,
                self.board_size * self.cell_size, (i + 1) * self.cell_size,
                width=2
            )

            # Vertical lines
            self.canvas.create_line(
                (i + 1) * self.cell_size, self.cell_size,
                (i + 1) * self.cell_size, self.board_size * self.cell_size,
                width=2
            )

        # Draw center point and star points
        center = self.board_size // 2
        star_positions = [
            (center, center),  # Center point
            (3, 3), (3, self.board_size - 4),  # Top-left and bottom-left star points
            (self.board_size - 4, 3), (self.board_size - 4, self.board_size - 4)  # Top-right and bottom-right star points
        ]

        for x, y in star_positions:
            self.canvas.create_oval(
                (x + 1) * self.cell_size - 4, (y + 1) * self.cell_size - 4,
                (x + 1) * self.cell_size + 4, (y + 1) * self.cell_size + 4,
                fill="black"
            )

        # Draw stones
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.game.board[i, j] == 1:  # Black stone
                    self.draw_stone(j, i, "black")
                elif self.game.board[i, j] == 2:  # White stone
                    self.draw_stone(j, i, "white")

    def draw_stone(self, x, y, color):
        """Draw a stone"""
        # Note: x corresponds to column (horizontal), y corresponds to row (vertical)
        canvas_x = (x + 1) * self.cell_size
        canvas_y = (y + 1) * self.cell_size
        radius = self.cell_size // 2 - 2

        # Draw the stone
        self.canvas.create_oval(
            canvas_x - radius, canvas_y - radius,
            canvas_x + radius, canvas_y + radius,
            fill=color, outline="black"
        )

        # Add a marker for the last move
        last_move_x, last_move_y = None, None
        for i in range(self.board_size):
            for j in range(self.board_size):
                # Find the last move
                if self.game.board[i, j] != 0 and self.game.board[i, j] != self.game.current_player:
                    last_move_x, last_move_y = j, i

        if last_move_x is not None and last_move_y is not None and last_move_x == x and last_move_y == y:
            mark_color = "white" if color == "black" else "black"
            mark_size = radius // 3
            self.canvas.create_rectangle(
                canvas_x - mark_size, canvas_y - mark_size,
                canvas_x + mark_size, canvas_y + mark_size,
                fill=mark_color, outline=mark_color
            )

    def on_canvas_click(self, event):
        """Handle canvas click event"""
        if self.game.game_over:
            return

        # If it's PVE mode and not the player's turn, ignore the click
        if self.game_mode.get() == 2 and self.game.current_player != self.player:
            return

        # Calculate the closest intersection point
        x = round((event.x - self.cell_size) / self.cell_size)
        y = round((event.y - self.cell_size) / self.cell_size)

        # Check if coordinates are valid
        if not (0 <= x < self.board_size and 0 <= y < self.board_size):
            return

        # In the logical board, y is row, x is column
        # Try to place a stone
        if self.game.make_move(y, x):
            # Redraw the board
            self.draw_board()

            # Update status
            self.update_status()

            # Check if the game is over
            if self.game.game_over:
                self.show_game_result()
                return

            # If it's PVE mode and AI's turn, let AI make a move
            if self.game_mode.get() == 2 and self.game.current_player != self.player:
                self.root.after(500, self.ai_move)  # Delay 500ms so the player can see their move

    def ai_move(self):
        """AI's move"""
        if not self.game.game_over:
            best_move = self.ai.get_best_move()
            if best_move:
                row, col = best_move
                self.game.make_move(row, col)

                # Redraw the board
                self.draw_board()

                # Update status
                self.update_status()

                # Check if the game is over
                if self.game.game_over:
                    self.show_game_result()

    def update_status(self):
        """Update status display"""
        player_name = "Black" if self.game.current_player == 1 else "White"
        if not self.game.game_over:
            self.status_var.set(f"Current turn: {player_name}")
        else:
            if self.game.winner:
                winner = "Black" if self.game.winner == 1 else "White"
                self.status_var.set(f"Game Over! {winner} wins!")
            else:
                self.status_var.set("Game Over! It's a draw!")

    def show_game_result(self):
        """Show game result"""
        if self.game.winner:
            winner = "Black" if self.game.winner == 1 else "White"
            message = f"Game Over! {winner} wins!"
        else:
            message = "Game Over! It's a draw!"

        messagebox.showinfo("Game Over", message)

    def restart_game(self):
        """Restart the game"""
        self.game.reset_game()
        self.draw_board()
        self.update_status()

        # If it's PVE mode and AI goes first, let AI make the first move
        if self.game_mode.get() == 2 and self.player != 1:
            self.ai_move()

    def back_to_menu(self):
        """Return to the main menu"""
        self.game_frame.pack_forget()
        self.mode_frame.pack()


def main():
    root = tk.Tk()
    app = GomokuGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

