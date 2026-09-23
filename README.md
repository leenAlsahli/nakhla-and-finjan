<p align="center">
  <img src="assets/logo.png" alt="Nakhla & Finjan Logo" width="240">
</p>

# Nakhla & Finjan 

A Saudi-themed take on classic Tic-Tac-Toe, reimagined with AI search algorithms and local cultural symbols in place of the traditional X and O.

## Overview
Nakhla & Finjan explores how different AI decision-making strategies perform in a constrained game environment. Instead of building a single AI opponent, the project implements and compares two distinct algorithms — Alpha-Beta Pruning and Monte Carlo Tree Search (MCTS) — evaluating their move quality, decision time, and overall performance across three gameplay modes: AI vs. AI, AI vs. Human, and Human vs. Human.

The game also introduces a unique twist on classic Tic-Tac-Toe rules: each player is limited to 3 active pieces on the board at a time — placing a 4th move removes the player's oldest piece — adding a layer of strategic depth beyond the traditional format.

## Features
- Alpha-Beta Pruning and Monte Carlo Tree Search implementations
- Performance benchmarking with visualized execution time and win-rate comparisons
- Three gameplay modes: AI vs. AI, AI vs. Human, and Human vs. Human
- Saudi-themed visual identity (Nakhla/Palm and Finjan/Coffee Cup replacing X and O)
- REST API backend serving a browser-based game interface

## Tech Stack
- **Backend:** Python, Flask, Flask-CORS
- **Frontend:** HTML5, CSS3, JavaScript
- **AI Algorithms:** Alpha-Beta Pruning, Monte Carlo Tree Search (MCTS)
- **Architecture:** REST API (Flask) serving a browser-based game interface
- **Fonts:** Tajawal & Outfit (Google Fonts) for Arabic-first, culturally rooted design

## How It Works
1. The Flask backend maintains game state, validates moves, and runs the selected AI algorithm to determine the next move.
2. The frontend renders the board and sends player moves to the backend via REST API calls.
3. In AI vs. AI mode, both algorithms play against each other while the system logs move times and outcomes for comparison.

## Running Locally
```bash
pip install flask flask-cors
python nakhla_finjan.py
```
Then open `interface.html` in your browser (or navigate to the local server address if served through Flask).

## What I Learned
Beyond implementation, the project focused on comparative analysis — measuring how search depth, pruning efficiency, and simulation count affect both computational cost and decision quality between the two algorithms.

## Author
Leen Alsahli — [LinkedIn](https://linkedin.com/in/leen-alsahli-1064a6305) | [Portfolio](https://leen-portfolio-inky.vercel.app)
