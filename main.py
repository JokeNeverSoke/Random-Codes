

import curses
import logging
import random
import time
import sys

try:
    import _curses._CursesWindow as window
except ModuleNotFoundError:
    window = object


class MineBlock(object):
    """docstring for MineBlock."""

    def __init__(self, ismine: bool = False):
        self.ismine = ismine
        self.marked = False
        self.checked = False
        self.number = False

    def __str__(self) -> str:
        return self.returnstr()

    def returnstr(self) -> str:
        """Get the string representation of the block"""
        if self.checked:
            if self.number:
                return str(self.number)  # nearby mines
            else:
                return "&"  # checked empty spot
        else:
            if self.marked:
                return "F"  # flagged
            else:
                return "#"  # not checked or flagged


class MineMap(object):
    """docstring for MineMap.
                pos x
                length_x
          1 2 3 4 5 6 7 8 9 10
      l 1 # # # # # # F # # F
    p e 2 # 5 3 3 2
    o n 3
    s g 4
    y t 5
      h 6
      _ 7
      y 8
        9
        10
    """

    def __init__(
            self,
            mines: int = 10,
            length_y: int = 10,
            length_x: int = 10,
            logger: logging.Logger = logging.getLogger(__name__)
    ):
        self.length_y: int = length_y
        self.length_x: int = length_x
        self.end: bool = False
        self.logger: logging.Logger = logger
        self.mines = []
        self.focus : list = [self.length_x//2, self.length_y//2]
        self.lastfocus = tuple(self.focus)

        # add logger
        self.logger.setLevel(1)
        self.logger.addHandler(logging.FileHandler(".mines.log", "w"))
        self.logger.debug("Logger initialized")

        # set mine locations
        if mines > length_y * length_x:  # check if mine too much
            raise ValueError("Mine amount can't be larger than square amount!")
        elif mines < 0:
            return ValueError("Mine amount can't be lower than 0")
        self.logger.debug(
            f"Board initialized with length_y {self.length_y} length_x {self.length_x} mines {mines}")

        # generate board
        self.board = [[MineBlock() for _ in range(length_y)]
                      for _ in range(length_x)]
        self.logger.debug("Board created")

        # pick out mines
        for _ in range(mines):
            pos_x, pos_y = random.randrange(
                length_y), random.randrange(length_x)
            while self.board[pos_y][pos_x].ismine:
                pos_x, pos_y = random.randrange(
                    length_y), random.randrange(length_x)
            self.board[pos_y][pos_x].ismine = True
            self.mines.append((pos_x, pos_y))
            self.logger.debug("Mine set at {}-{}".format(pos_x, pos_y))

    def getpos(self, pos_x: int, pos_y: int):
        """Demonstrative function"""
        return self.board[pos_y][pos_x]

    def run(self, stdscr: window):
        """Run the game using curses"""
        stdscr.nodelay(True)
        first = True
        while True:
            # keypress = stdscr.getch()
            # if keypress == -1:
            #     time.sleep(0.05)
            # else:
            #     self.logger.debug("Received keypress {}".format(keypress))
            if not first:
                try:
                    keypress = stdscr.getkey()
                    self.logger.debug("Received key {}".format(keypress))
                    if keypress == "KEY_UP":
                        if self.focus[1] > 0:
                            self.lastfocus = tuple(self.focus)
                            self.focus[1] -= 1
                    elif keypress == "KEY_DOWN":
                        if self.focus[1] < self.length_y:
                            self.lastfocus = tuple(self.focus)
                            self.focus[1] += 1
                    elif keypress == "KEY_LEFT":
                        if self.focus[0] > 0:
                            self.lastfocus = tuple(self.focus)
                            self.focus[0] -= 1
                    elif keypress == "KEY_RIGHT":
                        if self.focus[0] < self.length_x:
                            self.lastfocus = tuple(self.focus)
                            self.focus[0] += 1
                    self.logger.debug("Focus now at: {} {}".format(*self.focus))
                    self.logger.debug("Last focus now at: {} {}".format(*self.lastfocus))
                except:
                    pass
            else:
                first = False

            # check if window too small
            num_rows, num_cols = stdscr.getmaxyx()
            if num_cols < self.length_x*4 + 9 or num_rows < self.length_y*2 + 5:
                stdscr.clear()
                stdscr.addstr(1, 1, "Screen too small")
                stdscr.refresh()
                continue
            else:
                stdscr.addstr(1, 1, "~MineSweeper TUI~")



            # label lines
            for row in range(self.length_y):
                number = " " * (3 - len(str(row + 1))) + str(row + 1)
                stdscr.addstr(5 + row * 2, 5, number)
            for column in range(self.length_x):
                number = " " * (3 - len(str(column + 1))) + str(column + 1)
                stdscr.addstr(3, 9 + column * 4, number)

            # draw borders
            for row in range(self.length_y + 2):
                stdscr.addstr(2 + row * 2, 4, "+---" *
                              (self.length_x + 1) + "+")
            for row in range(self.length_y + 1):
                for counter in range(self.length_x + 2):
                    stdscr.addstr(3 + row * 2, 4 + counter * 4, "|")

            # remove previous focus marker
            stdscr.addstr(5+self.lastfocus[1]*2, 9+self.lastfocus[0]*4, " ")
            stdscr.addstr(5+self.lastfocus[1]*2, 11+self.lastfocus[0]*4, " ")

            # set mines
            for row in range(self.length_y):
                for column in range(self.length_x):
                    char = self.board[column][row].returnstr()
                    stdscr.addstr(5+row*2, 10+column*4, char)
                    if self.focus == [column, row]:
                        stdscr.addstr(5+row*2, 9+column*4, ">")
                        stdscr.addstr(5+row*2, 11+column*4, "<")



            # refresh screen
            stdscr.refresh()




def main():
    logger = logging.getLogger(__name__)
    length_y: int = 0
    while length_y <= 0:
        try:
            length_y = int(input("length_y of the game: "))
        except ValueError:
            continue
        except Exception as e:
            raise e
    length_x: int = 0
    while length_x <= 0:
        try:
            length_x = int(input("length_x of the game: "))
        except ValueError:
            continue
        except Exception as e:
            raise e
    mines: int = 0
    while mines <= 0 or mines > length_y * length_x:
        try:
            mines = int(input("Mine count of the game: "))
        except ValueError:
            continue
        except Exception as e:
            raise e
    maingame = MineMap(mines=mines, length_y=length_y,
                       length_x=length_x, logger=logger)
    curses.wrapper(maingame.run)


if __name__ == "__main__":
    main()
