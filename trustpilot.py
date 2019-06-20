"""Implementation of Trustpilot's Pony Challenge"""
import json
import argparse
import random
from collections import defaultdict

import requests

BASE = "https://ponychallenge.trustpilot.com/pony-challenge"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

class Maze:
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


    @staticmethod
    def _new_maze_id(width, height, name, difficulty):
        args = {"maze-width": width,
                "maze-height": height,
                "maze-player-name": name,
                "difficulty": difficulty}
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
        args = {"direction": move}
        data = json.dumps(args)
        _response = requests.post(f"{BASE}/maze/{self.maze_id}", data, headers=HEADERS)
        self._update_state()

    def __getitem__(self, item):
        return self.maze[item]

def bfs(maze):
    return random.sample(maze[maze.pony], 1)[0]

def get_move(maze):
    pony = maze.pony
    move = bfs(maze)
    delta = (move[0] - pony[0], move[1] - pony[1])
    move_map = {( 0,-1): "west",
                ( 1, 0): "south",
                ( 0, 1): "east",
                (-1, 0): "north"}

    return move_map[delta]

def play(width, height, name, difficulty):
    maze = Maze(width, height, name, difficulty)
    while True:
        print(maze)
        move = get_move(maze)
        maze.move(move)

def main():
    parser = argparse.ArgumentParser(
        description="Rescue a pony that Trustpilot is holding hostage in a scary maze."
    )
    parser.add_argument(
        "--width",
        type=int,
        nargs="?",
        default=15,
        help="the width of the maze",
    )
    parser.add_argument(
        "--height",
        type=int,
        nargs="?",
        default=15,
        help="the height of the maze",
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
    play(args.width, args.height, args.name, args.difficulty)


if __name__ == '__main__':
    main()
