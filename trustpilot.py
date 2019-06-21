"""
Implementation of Trustpilot's Pony Challenge.

Uses simple BFS to reach the goal. If there is no path to the goal,
the Pony naively tries to take the move that maximizes Manhatten distance
to Domokun.

Code formatted using Black.
"""
import json
import argparse
import curses
from collections import defaultdict
import requests
import _curses

BASE = "https://ponychallenge.trustpilot.com/pony-challenge"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

# pylint: disable=too-many-instance-attributes
class Maze:
    """A wrapper for the Maze in which the action takes place"""

    def __init__(self, width, height, name, difficulty):
        self.width = width
        self.height = height
        self.name = name
        self.difficulty = difficulty
        self.maze_id = self._new_maze_id(width, height, name, difficulty)

        data = self._get_maze_state()
        self.pony = self._coord_from_index(data["pony"][0])
        self.domokun = self._coord_from_index(data["domokun"][0])
        self.goal = self._coord_from_index(data["end-point"][0])
        self.state = "active"

        grid = data["data"]

        # represent maze as an adjacency list
        self.maze = defaultdict(set)
        for idx, walls in enumerate(grid):
            row, column = self._coord_from_index(idx)
            if "west" not in walls:
                self.maze[(row, column)].add((row, column - 1))
                self.maze[(row, column - 1)].add((row, column))
            if "north" not in walls:
                self.maze[(row, column)].add((row - 1, column))
                self.maze[(row - 1, column)].add((row, column))

    def _get_maze_state(self):
        return requests.get(f"{BASE}/maze/{self.maze_id}", headers=HEADERS).json()

    def _update_state(self):
        data = self._get_maze_state()
        self.pony = self._coord_from_index(data["pony"][0])
        self.domokun = self._coord_from_index(data["domokun"][0])
        self.goal = self._coord_from_index(data["end-point"][0])
        self.state = data["game-state"]["state"]

    @staticmethod
    def _new_maze_id(width, height, name, difficulty):
        args = {
            "maze-width": width,
            "maze-height": height,
            "maze-player-name": name,
            "difficulty": difficulty,
        }
        data = json.dumps(args)

        response = requests.post(f"{BASE}/maze", data, headers=HEADERS)
        return response.json()["maze_id"]

    def _coord_from_index(self, index):
        row = index // self.width
        column = index % self.width
        return (row, column)

    def __repr__(self):
        response = requests.get(f"{BASE}/maze/{self.maze_id}/print", headers=HEADERS)
        return response.content.decode()

    def move(self, move):
        """Move the Pony in (north|east|west|south) direction"""
        args = {"direction": move}
        data = json.dumps(args)
        _response = requests.post(f"{BASE}/maze/{self.maze_id}", data, headers=HEADERS)
        self._update_state()

    def __getitem__(self, item):
        return self.maze[item]


def bfs(maze):
    """Basic BFS implementation, viewing Domokun as a wall"""
    queue = [(maze.pony, [maze.pony])]
    while queue:
        (pos, path) = queue.pop()
        for neighbor in maze[pos]:
            if neighbor == maze.goal:
                return path + [neighbor]
            if neighbor in path or neighbor == maze.domokun:
                continue

            queue.append((neighbor, path + [neighbor]))

    # no path to goal
    return []


# pylint: disable=invalid-name
def backup(maze):
    """
    If there is no path to goal, we simply try to escape Domokun.
    We do this by selecting the move resulting in the largest Manhatten
    distance to Domokun. Not the best escape plan, not the worst.
    Sometimes the Pony and Domokun just end up dancing, which is cool.
    """
    moves = maze[maze.pony]
    d = maze.domokun
    return sorted(moves, key=lambda m: abs(m[0] - d[1]) + abs(m[1] - d[1]))[-1]


def get_move(maze):
    """
    Takes shortest path to goal if there is a path.
    If there is no shortest path, tries to move away from Domokun
    """
    pony = maze.pony
    path = bfs(maze)
    move = path[1] if path else backup(maze)
    delta = (move[0] - pony[0], move[1] - pony[1])
    move_map = {(0, -1): "west", (1, 0): "south", (0, 1): "east", (-1, 0): "north"}

    return move_map[delta]


def play(width, height, name, difficulty):
    """Game loop attempting to rescue a cute Pony from Trustpilot's evil maze"""
    maze = Maze(width, height, name, difficulty)
    stdscr = curses.initscr()
    while maze.state == "active":
        stdscr.clear()
        stdscr.addstr(maze.__repr__())
        stdscr.refresh()
        move = get_move(maze)
        maze.move(move)

    curses.endwin()
    if maze.state == "won":
        print(f"\n{name} escaped! Rainbows to all!")
    elif maze.state == "over":
        print(f"\n{name} was killed by Domo and your bad code! Shame!")



def main():
    """Handle arguments and smoothly interrupt game"""
    parser = argparse.ArgumentParser(
        description="Rescue a pony that Trustpilot is holding hostage in a scary maze."
    )
    parser.add_argument(
        "--width", type=int, nargs="?", default=15, help="the width of the maze"
    )
    parser.add_argument(
        "--height", type=int, nargs="?", default=15, help="the height of the maze"
    )
    parser.add_argument(
        "--name",
        type=str,
        nargs="?",
        default="Fluttershy",
        help="the name of the pony to rescue - must be a valid pony",
    )
    parser.add_argument(
        "--difficulty",
        type=int,
        nargs="?",
        default=0,
        help="the difficulty of the adversary in the maze",
    )
    args = parser.parse_args()
    assert 0 <= args.difficulty <= 3, "Only supports difficulty 0-3"
    assert 15 <= args.width <= 25, "Only supports width 15-25"
    assert 15 <= args.height <= 25, "Only supports width 15-25"
    try:
        play(args.width, args.height, args.name, args.difficulty)
    except KeyboardInterrupt:
        pass
    except _curses.error:
        print("Window too small for curses. Reduce font/maze size or resize window.")


if __name__ == "__main__":
    main()
