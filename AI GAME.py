import tkinter as tk
from tkinter import messagebox
import copy, math, threading, random

# =========================
# CONSTANTS
# =========================
EMPTY, BLACK, WHITE = 0, 1, 2
SIZE = 8
CELL, PAD = 68, 20

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

WEIGHTS = [
[100,-20,10,5,5,10,-20,100],
[-20,-50,-2,-2,-2,-2,-50,-20],
[10,-2,1,1,1,1,-2,10],
[5,-2,1,1,1,1,-2,5],
[5,-2,1,1,1,1,-2,5],
[10,-2,1,1,1,1,-2,10],
[-20,-50,-2,-2,-2,-2,-50,-20],
[100,-20,10,5,5,10,-20,100]
]

def opponent(p):
    return WHITE if p == BLACK else BLACK


# =========================
# BOARD LOGIC
# =========================
class Board:
    def __init__(self):
        self.grid = [[EMPTY]*SIZE for _ in range(SIZE)]
        self.init_board()

    def init_board(self):
        m = SIZE//2
        self.grid[m-1][m-1] = WHITE
        self.grid[m-1][m]   = BLACK
        self.grid[m][m-1]   = BLACK
        self.grid[m][m]     = WHITE

    def copy(self):
        return copy.deepcopy(self.grid)

    def get_flips(self, r, c, p):
        if self.grid[r][c] != EMPTY:
            return []

        flips = []
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            temp = []

            while 0<=nr<SIZE and 0<=nc<SIZE and self.grid[nr][nc] == opponent(p):
                temp.append((nr,nc))
                nr += dr; nc += dc

            if temp and 0<=nr<SIZE and 0<=nc<SIZE and self.grid[nr][nc] == p:
                flips.extend(temp)

        return flips

    def get_moves(self, p):
        return [(r,c) for r in range(SIZE) for c in range(SIZE)
                if self.get_flips(r,c,p)]

    def apply_move(self, r, c, p):
        flips = self.get_flips(r,c,p)
        if not flips:
            return False

        self.grid[r][c] = p
        for fr,fc in flips:
            self.grid[fr][fc] = p

        return True

    def score(self):
        b = sum(row.count(BLACK) for row in self.grid)
        w = sum(row.count(WHITE) for row in self.grid)
        return b, w


# =========================
# AI ENGINE
# =========================
class AI:
    def __init__(self, difficulty="Easy"):
        self.set_difficulty(difficulty)

    def set_difficulty(self, difficulty):
        if difficulty == "Easy":
            self.depth = 2
            self.noise = 40
        elif difficulty == "Medium":
            self.depth = 3
            self.noise = 10
        else:
            self.depth = 5
            self.noise = 0

    # ✅ Heuristic Evaluation Function
    def evaluate(self, board, p):
        h = opponent(p)
        score = 0

        # Positional weights
        for r in range(SIZE):
            for c in range(SIZE):
                if board[r][c] == p:
                    score += WEIGHTS[r][c]
                elif board[r][c] == h:
                    score -= WEIGHTS[r][c]

        # Mobility (extra intelligence)
        my_moves = len(self.get_moves(board, p))
        opp_moves = len(self.get_moves(board, h))
        if my_moves + opp_moves:
            score += 5 * (my_moves - opp_moves)

        # Small randomness (easy/medium)
        score += random.uniform(-self.noise, self.noise)

        return score

    # ✅ Move Ordering (Best-First idea)
    def order_moves(self, board, moves, p):
        scored = []
        for m in moves:
            temp = self.simulate(board, m, p)
            scored.append((self.evaluate(temp, p), m))
        scored.sort(reverse=True, key=lambda x: x[0])  # best first
        return [m for _, m in scored]

    # ✅ Minimax + Alpha-Beta + Depth-Limited
    def minimax(self, board, depth, alpha, beta, maximizing, p):
        moves = self.get_moves(board, p if maximizing else opponent(p))

        if depth == 0 or not moves:
            return self.evaluate(board, p), None

        # 🔥 Apply move ordering
        moves = self.order_moves(board, moves, p if maximizing else opponent(p))

        best_move = moves[0]

        if maximizing:
            max_eval = -math.inf
            for move in moves:
                new_board = self.simulate(board, move, p)
                eval,_ = self.minimax(new_board, depth-1, alpha, beta, False, p)
                if eval > max_eval:
                    max_eval, best_move = eval, move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_move

        else:
            min_eval = math.inf
            for move in moves:
                new_board = self.simulate(board, move, opponent(p))
                eval,_ = self.minimax(new_board, depth-1, alpha, beta, True, p)
                if eval < min_eval:
                    min_eval, best_move = eval, move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def get_moves(self, board, p):
        temp = Board()
        temp.grid = board
        return temp.get_moves(p)

    def simulate(self, board, move, p):
        temp = Board()
        temp.grid = copy.deepcopy(board)
        temp.apply_move(move[0], move[1], p)
        return temp.grid


# =========================
# UI
# =========================
class OthelloUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Othello AI")

        self.board = Board()
        self.ai = AI("Easy")

        self.current = BLACK
        self.thinking = False

        self.status = tk.StringVar(value="Your turn (Black ●)")
        self.difficulty = tk.StringVar(value="Easy")

        self.build_ui()
        self.draw()

    def build_ui(self):
        tk.Label(self.root, textvariable=self.status,
                 font=("Courier",12,"bold")).pack()

        self.canvas = tk.Canvas(self.root,
                                width=SIZE*CELL+2*PAD,
                                height=SIZE*CELL+2*PAD,
                                bg="#2d7a47")
        self.canvas.pack()

        self.canvas.bind("<Button-1>", self.click)

        frame = tk.Frame(self.root)
        frame.pack()

        tk.OptionMenu(frame, self.difficulty, "Easy","Medium","Hard",
                      command=self.change_diff).pack(side="left")

        tk.Button(frame, text="New Game", command=self.new_game).pack(side="left")

    def change_diff(self, val):
        self.ai.set_difficulty(val)

    def new_game(self):
        self.board = Board()
        self.current = BLACK
        self.status.set("Your turn (Black ●)")
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        moves = self.board.get_moves(self.current)

        for r in range(SIZE):
            for c in range(SIZE):
                x = PAD + c*CELL
                y = PAD + r*CELL

                self.canvas.create_rectangle(x, y, x+CELL, y+CELL, fill="#35954f")

                if self.board.grid[r][c] == BLACK:
                    self.canvas.create_oval(x+10,y+10,x+CELL-10,y+CELL-10,fill="black")
                elif self.board.grid[r][c] == WHITE:
                    self.canvas.create_oval(x+10,y+10,x+CELL-10,y+CELL-10,fill="white")

                # ✅ Valid move hint
                elif (r,c) in moves and self.current == BLACK:
                    self.canvas.create_oval(
                        x+CELL//2-6, y+CELL//2-6,
                        x+CELL//2+6, y+CELL//2+6,
                        fill="#52c46a"
                    )

    def click(self, event):
        if self.current != BLACK or self.thinking:
            return

        c = (event.x - PAD)//CELL
        r = (event.y - PAD)//CELL

        if not (0<=r<SIZE and 0<=c<SIZE):
            return

        if not self.board.apply_move(r,c,BLACK):
            return

        self.current = WHITE
        self.draw()
        self.root.after(100, self.ai_turn)

    def ai_turn(self):
        self.status.set("AI thinking...")
        self.thinking = True

        threading.Thread(target=self.run_ai, daemon=True).start()

    def run_ai(self):
        _, move = self.ai.minimax(
            self.board.copy(),
            self.ai.depth,
            -math.inf, math.inf,
            True, WHITE
        )
        self.root.after(0, self.finish_ai, move)

    def finish_ai(self, move):
        self.thinking = False

        if move:
            self.board.apply_move(move[0], move[1], WHITE)

        self.current = BLACK
        self.draw()

        b, w = self.board.score()

        if not self.board.get_moves(BLACK) and not self.board.get_moves(WHITE):
            msg = f"Game Over\nBlack: {b}  White: {w}"
            messagebox.showinfo("Result", msg)
        else:
            self.status.set("Your turn (Black ●)")


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    OthelloUI(root)
    root.mainloop()