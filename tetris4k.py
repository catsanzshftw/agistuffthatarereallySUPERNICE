"""
TETRIS – Electronika‑60 recreation
Faithfully mimics the first public build (1984) while staying in one Pygame file.

Controls
--------
← / → : Move
↓      : Soft‑drop
SPACE  : Hard‑drop
↑ or W : Rotate clockwise
1      : Toggle next‑piece preview (as in original)
ESC    : Quit

Optional at start‑up: type a launch level (0–9) in the terminal to set gravity speed.
"""

import pygame, random, sys, time

# -----------  CONSTANTS  -----------
BLOCK = 24                           # square size in px
COLS, ROWS = 10, 20                  # play‑field
WIDTH, HEIGHT = COLS*BLOCK, ROWS*BLOCK
FPS          = 60

# Monochrome palette – light‑green on black CRT style
BG_COLOUR    = (  0,   0,   0)
BRICK_COLOUR = (  0, 220,   0)
GRID_COLOUR  = (  0, 110,   0)

SHAPES = [
    [[1,1,1,1]],                                        # I
    [[1,1],[1,1]],                                      # O
    [[0,1,0],[1,1,1]],                                  # T
    [[1,0,0],[1,1,1]],                                  # J
    [[0,0,1],[1,1,1]],                                  # L
    [[0,1,1],[1,1,0]],                                  # S
    [[1,1,0],[0,1,1]],                                  # Z
]

# Pre‑compute all four rotations for each tetromino (simplest CW turn)
def rotations(shape):
    rots = []
    m = shape
    for _ in range(4):
        rots.append(m)
        m = [list(row)[::-1] for row in zip(*m)]
    return rots

SHAPES = [rotations(s) for s in SHAPES]

# ----------  MODEL CLASSES ----------
class Piece:
    def __init__(self):
        self.type   = random.randrange(len(SHAPES))
        self.rot    = 0
        self.shape  = SHAPES[self.type]
        self.x      = COLS//2 - len(self.shape[0][0])//2
        self.y      = 0
    def image(self):      return self.shape[self.rot]
    def rotate(self):     self.rot = (self.rot+1) % 4

class Game:
    def __init__(self, start_level=0):
        self.board   = [[0]*COLS for _ in range(ROWS)]
        self.cur     = Piece()
        self.next    = Piece()
        self.score   = 0
        self.preview = False       # OFF by default
        self.drop_ms = max(50, 1000 - 100*start_level)
        self.next_drop = pygame.time.get_ticks()+self.drop_ms
        self.thousands = 0         # tick‑marks after 999
    # --- helpers ---
    def block_at(self, x,y): return 0<=x<COLS and 0<=y<ROWS and self.board[y][x]
    def fits(self, piece, dx,dy,rot):
        img = piece.shape[(piece.rot+rot)%4]
        for r,row in enumerate(img):
            for c,val in enumerate(row):
                if val:
                    nx, ny = piece.x+c+dx, piece.y+r+dy
                    if nx<0 or nx>=COLS or ny>=ROWS or (ny>=0 and self.board[ny][nx]):
                        return False
        return True
    # --- actions ---
    def commit(self):
        for r,row in enumerate(self.cur.image()):
            for c,val in enumerate(row):
                if val:
                    y = self.cur.y+r
                    x = self.cur.x+c
                    if y<0:       # game over
                        return False
                    self.board[y][x]=1
        self.clear_lines()
        self.cur = self.next
        self.next = Piece()
        return True
    def clear_lines(self):
        new = [row for row in self.board if any(v==0 for v in row)]
        cleared = ROWS - len(new)
        if cleared:
            self.board = [[0]*COLS for _ in range(cleared)] + new
        # scoring: +1 per piece +5 bonus if preview OFF (per original)
        self.score += 1 + (5 if not self.preview else 0)
        if self.score>999:
            self.score -= 1000
            self.thousands += 1
    # -------- main update ----------
    def update(self, keys, now):
        moved=False
        if keys[pygame.K_LEFT]  and self.fits(self.cur,-1,0,0): self.cur.x-=1; moved=True
        if keys[pygame.K_RIGHT] and self.fits(self.cur, 1,0,0): self.cur.x+=1; moved=True
        if keys[pygame.K_DOWN]  and self.fits(self.cur, 0,1,0): self.cur.y+=1; moved=True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if self.fits(self.cur,0,0,1): self.cur.rotate(); moved=True
        if keys[pygame.K_SPACE]:          # hard‑drop
            while self.fits(self.cur,0,1,0): self.cur.y+=1
            if not self.commit(): return False
            self.next_drop = now+self.drop_ms
            moved=True
        if now>=self.next_drop and not moved:
            if self.fits(self.cur,0,1,0):
                self.cur.y+=1
            else:
                if not self.commit(): return False
            self.next_drop = now+self.drop_ms
        return True

# -------------  DRAWING -------------
def draw_square(screen, x,y):
    rect = pygame.Rect(x*BLOCK, y*BLOCK, BLOCK, BLOCK)
    pygame.draw.rect(screen, BRICK_COLOUR, rect)
    pygame.draw.rect(screen, GRID_COLOUR, rect, 1)

def render(screen, game):
    screen.fill(BG_COLOUR)
    # grid
    for y in range(ROWS):
        for x in range(COLS):
            if game.board[y][x]:
                draw_square(screen,x,y)
    # current piece
    for r,row in enumerate(game.cur.image()):
        for c,val in enumerate(row):
            if val and game.cur.y+r>=0:
                draw_square(screen, game.cur.x+c, game.cur.y+r)
    # border
    pygame.draw.rect(screen, GRID_COLOUR, (0,0,WIDTH,HEIGHT), 2)
    # side panel (text)
    font = pygame.font.SysFont("Courier", 20, bold=True)
    score_txt = font.render(f" SCORE {game.thousands}'{game.score:03}", True, BRICK_COLOUR)
    screen.blit(score_txt, (WIDTH+20, 30))
    if game.preview:
        font_s = pygame.font.SysFont("Courier", 16)
        screen.blit(font_s.render("NEXT", True, GRID_COLOUR), (WIDTH+36, 70))
        for r,row in enumerate(game.next.image()):
            for c,val in enumerate(row):
                if val:
                    x = WIDTH+40 + c*BLOCK
                    y = 90 + r*BLOCK
                    pygame.draw.rect(screen, BRICK_COLOUR, (x,y,BLOCK,BLOCK))
                    pygame.draw.rect(screen, GRID_COLOUR, (x,y,BLOCK,BLOCK), 1)
    pygame.display.flip()

# -------------  MAIN LOOP -----------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH+140, HEIGHT))
    pygame.display.set_caption("TETRIS (Electronika‑60 recreation)")
    clock = pygame.time.Clock()

    try:
        start_lvl = int(input("Launch level (0–9)? ") or "0")
    except ValueError:
        start_lvl = 0
    game = Game(start_lvl)

    while True:
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key==pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key==pygame.K_1:
                game.preview = not game.preview          # toggle like original

        if not game.update(keys, now): break            # game over
        render(screen, game)
        clock.tick(FPS)

    # simple game‑over splash
    font = pygame.font.SysFont("Courier", 28, bold=True)
    text = font.render(" GAME OVER ", True, BRICK_COLOUR)
    screen.blit(text, (WIDTH//2-text.get_width()//2, HEIGHT//2-20))
    pygame.display.flip()
    time.sleep(3)
    pygame.quit()

if __name__ == "__main__":
    main()
