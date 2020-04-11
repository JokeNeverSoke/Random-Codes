

import _curses
import curses
import logging
import random
import sys
import time
from typing import List, Tuple

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
                if self.flagged:
                    return "$"
                return "X"
            if self.number:
                return str(self.number)  # nearby mines
            else:
                return "0"  # checked empty spot
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
            while self.board[pos_y][pos_x].ismine or (pos_y, pos_x) in avoid:
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

    def getsurround(self, x, y):
        """Get the amount of mines surrounding (x, y)"""
        toscan: List[Tuple[int, int]] = [
            (x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
            (x - 1, y), (x, y), (x + 1, y),
            (x - 1, y + 1), (x, y + 1), (x + 1, y + 1)
        ]
        minecount = 0
        for point in toscan:
            if all((
                point[0] >= 0,
                point[1] >= 0,
                point[1] < self.length_x,
                point[0] < self.length_y,
            )):
                try:
                    if self.board[point[1]][point[0]].ismine:
                        minecount += 1
                except IndexError:
                    self.logger.exception(
                        "Failed to scan point {}".format(point))
        return minecount

    def scan(self):
        """Scan board"""
        queue: List[Tuple[int, int]] = []
        self.scanned: List[Tuple[int, int]] = []
        # add all check blocks to queue
        for row in range(len(self.board)):
            for column in range(len(self.board[row])):
                if all((
                        self.board[row][column].checked,
                        not self.board[row][column].number,
                        (column, row) not in self.scanned
                )):
                    queue.append((column, row))
                    self.scanned.append((column, row))
        while queue:
            point: Tuple[int, int] = queue.pop(0)
            # self.logger.debug("Scanning {}".format(point))
            column = point[0]
            row = point[1]
            block: MineBlock = self.board[row][column]
            if block.ismine:
                continue
            self.board[row][column].checked = True
            self.board[row][column].number = self.getsurround(column, row)
            if not self.board[row][column].number:
                for canscan in [
                    (column + 1, row), (column - 1, row),
                    (column, row + 1), (column, row - 1)
                ]:
                    if all((
                        canscan[0] >= 0,
                        canscan[1] >= 0,
                        canscan[1] < self.length_x,
                        canscan[0] < self.length_y,
                        canscan not in self.scanned
                    )):
                        queue.append(canscan)
                        self.scanned.append(canscan)

    def run(self, stdscr: window):
        """Run the game using curses"""
        # add color pairs
        # color for empty checked
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        # color for mines
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        # color for flags
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_GREEN)
        # color for index
        curses.init_pair(10, curses.COLOR_BLUE, curses.COLOR_BLACK)
        # color for 1 mine
        curses.init_pair(21, curses.COLOR_BLUE, curses.COLOR_BLACK)
        # color for 2 mine
        curses.init_pair(22, curses.COLOR_GREEN, curses.COLOR_BLACK)
        # color for 3 mine
        curses.init_pair(23, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        # color for 4 mines
        curses.init_pair(24, curses.COLOR_RED, curses.COLOR_BLACK)
        # color for >=5 mines
        curses.init_pair(25, curses.COLOR_BLACK, curses.COLOR_RED)

        stdscr.nodelay(True)  # non-blocking stuff
        first = True  # first 'space' click check
        quit_verify = 0  # for double verifying when user presses 'q'

        while True:
            try:
                # raises _curses.error when no keypress, so error catching is
                # needed to prevent breakdown
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
                    else:
                        if keypress.lower() == "f":  # flag the current focus
                            self.board[self.focus[0]][self.focus[1]
                                                      ].flagged = not self.board[self.focus[0]][self.focus[1]].flagged
                        elif keypress.lower() == " ":  # explore current focus
                            self.board[self.focus[0]][self.focus[1]
                                                      ].checked = True
                            if first:
                                # place mines if is first click
                                first = False
                                self.placemines(self.mines, avoid=[
                                                tuple(self.focus)])
                            elif self.board[self.focus[0]][self.focus[1]].ismine:
                                self.gameover()
                        self.scan()
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
                stdscr.addstr(5 + row * 2, 5, number, curses.color_pair(10))
            for column in range(self.length_x):
                number = " " * (3 - len(str(column + 1))) + str(column + 1)
                stdscr.addstr(3, 9 + column * 4, number, curses.color_pair(10))

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
                    attrs = []
                    if char == "0":
                        attrs.append(curses.color_pair(1))
                    elif char == "X":
                        attrs.append(curses.color_pair(2))
                    elif char in ["F", "$"]:
                        attrs.append(curses.color_pair(3))
                    elif char == "1":
                        attrs.append(curses.color_pair(21))
                    elif char == "2":
                        attrs.append(curses.color_pair(22))
                    elif char == "3":
                        attrs.append(curses.color_pair(23))
                    elif char == "4":
                        attrs.append(curses.color_pair(24))
                    elif char == "5":
                        attrs.append(curses.color_pair(25))
                    elif char == "6":
                        attrs.append(curses.color_pair(25))
                    elif char == "7":
                        attrs.append(curses.color_pair(25))
                    elif char == "8":
                        attrs.append(curses.color_pair(25))
                    elif char == "9":
                        attrs.append(curses.color_pair(25))
                    stdscr.addstr(5 + row * 2, 10 + column * 4, char, *attrs)
                    if self.focus == [column, row]:  # put focus marker
                        stdscr.addstr(
                            5 + row * 2, 9 + column * 4, ">", curses.A_BLINK)
                        stdscr.addstr(
                            5 + row * 2, 11 + column * 4, "<", curses.A_BLINK)

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
