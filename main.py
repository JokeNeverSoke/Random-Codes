

import curses
import logging
import random
import time
import sys
from typing import List, Tuple
import _curses

try:
    import _curses._CursesWindow as window
except ModuleNotFoundError:
    window = object


class MineBlock(object):
    """docstring for MineBlock."""

    def __init__(self, ismine: bool = False):
        self.ismine = ismine
        self.flagged = False
        self.checked = False
        self.number = False

    def __str__(self) -> str:
        return self.returnstr()

    def returnstr(self) -> str:
        """Get the string representation of the block"""
        if self.checked:
            if self.ismine:
                return "X"
            if self.number:
                return str(self.number)  # nearby mines
            else:
                return "&"  # checked empty spot
        else:
            if self.flagged:
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
        self.length_y: int = length_y  # length of y
        self.length_x: int = length_x  # length of x
        self.end: bool = False  # if the game has ended
        self.logger: logging.Logger = logger  # logger
        self.mines: int = mines  # amount of mines
        # current focus of cursor: list(x, y)
        self.focus: list = [self.length_x // 2, self.length_y // 2]
        self.lastfocus = tuple(self.focus)  # last focus, in tuple form
        self.starttime: float  # recorded start time

        # add logger
        self.logger.setLevel(1)
        self.logger.addHandler(
            logging.FileHandler(
                ".mines.log",
                "w"))  # add a temporary filelogger
        self.logger.debug("Logger initialized")

        # set mine locations
        if mines > length_y * length_x - 1:  # check if mine too much
            raise ValueError("Mine amount can't be larger than square amount!")
        elif mines < 0:
            return ValueError("Mine amount can't be lower than 0")
        self.logger.debug(
            f"Board initialized with length_y {self.length_y} length_x {self.length_x} mines {mines}")

        # generate board
        # to be honest I have no idea how this part works but it just does
        self.board = [[MineBlock() for _ in range(length_y)]
                      for _ in range(length_x)]
        self.logger.debug("Board created")

    def getpos(self, pos_x: int, pos_y: int):
        """Demonstrative function"""
        return self.board[pos_y][pos_x]

    def placemines(self, mines: int, avoid: List[Tuple[int, int]] = []):
        self.minelist = []
        # pick out mines
        self.logger.debug("Placing mines, avoid: {}".format(avoid))
        for _ in range(mines):
            pos_x, pos_y = random.randrange(
                self.length_y), random.randrange(self.length_x)
            while self.board[pos_y][pos_x].ismine or (pos_x, pos_y) in avoid:
                pos_x, pos_y = random.randrange(
                    self.length_y), random.randrange(self.length_x)
            self.board[pos_y][pos_x].ismine = True
            self.minelist.append((pos_x, pos_y))
            self.logger.debug("Mine set at {}-{}".format(pos_x, pos_y))

    def gameover(self):
        """Function to call after mine is pressed or game won"""
        for row in range(len(self.board)):
            for column in range(len(self.board[row])):
                self.board[row][column].checked = True

    def run(self, stdscr: window):
        """Run the game using curses"""
        stdscr.nodelay(True)  # non-blocking stuff
        first = True  # first 'space' click check
        quit_verify = 0  # for double verifying when user presses 'q'

        while True:
            try:
                # raises _curses.error when no keypress, so error catching is
                # needed
                keypress = stdscr.getkey()
                self.logger.debug("Received key {}".format(keypress))
                if keypress.lower() == "q":
                    quit_verify += 1
                    if quit_verify == 2:
                        break
                else:
                    quit_verify = 0
                    if keypress == "KEY_UP":
                        if self.focus[1] > 0:
                            self.lastfocus = tuple(self.focus)
                            self.focus[1] -= 1
                            self.logger.debug(
                                "Focus now at: {} {}".format(
                                    *self.focus))
                    elif keypress == "KEY_DOWN":
                        if self.focus[1] < self.length_y - 1:
                            self.lastfocus = tuple(self.focus)
                            self.focus[1] += 1
                            self.logger.debug(
                                "Focus now at: {} {}".format(
                                    *self.focus))
                    elif keypress == "KEY_LEFT":
                        if self.focus[0] > 0:
                            self.lastfocus = tuple(self.focus)
                            self.focus[0] -= 1
                            self.logger.debug(
                                "Focus now at: {} {}".format(
                                    *self.focus))
                    elif keypress == "KEY_RIGHT":
                        if self.focus[0] < self.length_x - 1:
                            self.lastfocus = tuple(self.focus)
                            self.focus[0] += 1
                            self.logger.debug(
                                "Focus now at: {} {}".format(
                                    *self.focus))
                    elif keypress.lower() == "f":  # flag the current focus
                        self.board[self.focus[0]][self.focus[1]
                                                  ].flagged = not self.board[self.focus[0]][self.focus[1]].flagged
                    elif keypress.lower() == " ":  # explore current focus
                        self.board[self.focus[0]][self.focus[1]
                                                  ].checked = True
                        if first:
                            # place mines if is first click
                            first = False
                            self.placemines(self.mines, [tuple(self.focus)])
                        elif self.board[self.focus[0]][self.focus[1]].ismine:
                            self.gameover()
            except _curses.error:  # ignore emtpy keypress
                pass
            except Exception as exc:
                raise exc

            # check if window too small
            num_rows, num_cols = stdscr.getmaxyx()
            # the condition is currently just some random numbers
            if num_cols < self.length_x * 4 + 9 or num_rows < self.length_y * 2 + 5:
                stdscr.clear()
                stdscr.addstr(1, 1, "Screen too small")
                stdscr.refresh()
                time.sleep(0.1)
                continue

            # display top message
            stdscr.addstr(1, 1, " " * 52)  # clean notification
            if quit_verify == 1:
                stdscr.addstr(
                    1, 1, "Press q again to quit, any other key to continue")
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
            stdscr.addstr(
                5 + self.lastfocus[1] * 2,
                9 + self.lastfocus[0] * 4,
                " ")
            stdscr.addstr(
                5 + self.lastfocus[1] * 2,
                11 + self.lastfocus[0] * 4,
                " ")

            # place blocks
            for row in range(self.length_y):
                for column in range(self.length_x):
                    char = self.board[column][row].returnstr()
                    stdscr.addstr(5 + row * 2, 10 + column * 4, char)
                    if self.focus == [column, row]:  # put focus marker
                        stdscr.addstr(5 + row * 2, 9 + column * 4, ">")
                        stdscr.addstr(5 + row * 2, 11 + column * 4, "<")

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
