from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import math, random, time, os

app = Flask(__name__, static_folder=".")
CORS(app)

# حالة اللعبه
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board     = [' '] * 9
        self.hist_x    = []   # هيستوري حركات اكس : النخله
        self.hist_o    = []   # هيستوري حركات او : الفنجال
        self.turn      = 'X'
        self.winner    = None
        self.game_over = False
        self.moves_log = []

    # تطبيق الحركة مع حذف اقدم قطعة لو اللاعب وصل للحد
    def apply_move(self, idx: int, player: str):
        hist = self.hist_x if player == 'X' else self.hist_o
        if len(hist) == 3:
            oldest = hist.pop(0)
            self.board[oldest] = ' '
        self.board[idx] = player
        hist.append(idx)

    def is_valid(self, idx: int) -> bool:
        return 0 <= idx < 9 and self.board[idx] == ' '

    def check_winner(self):
        wins = [(0,1,2),(3,4,5),(6,7,8),
                (0,3,6),(1,4,7),(2,5,8),
                (0,4,8),(2,4,6)]
        b = self.board
        for a, c, d in wins:
            if b[a] == b[c] == b[d] != ' ':
                return b[a], [a, c, d]
        return None, []

    def get_empty_cells(self):
        return [i for i in range(9) if self.board[i] == ' ']

    def valid_moves(self):
        return self.get_empty_cells()

    # نسخة كاملة من الحاله  عشان ما نعدل على الاصل
    def clone(self):
        g = GameState()
        g.board     = self.board[:]
        g.hist_x    = self.hist_x[:]
        g.hist_o    = self.hist_o[:]
        g.turn      = self.turn
        g.winner    = self.winner
        g.game_over = self.game_over
        g.moves_log = self.moves_log[:]
        return g

    # تحول حالة اللعبة لماب يروح للواجهة
    def to_dict(self, winning_cells=None, thinking=False):
        return {
            "board"        : self.board,
            "histX"        : self.hist_x,
            "histO"        : self.hist_o,
            "currentTurn"  : self.turn,
            "winner"       : self.winner,
            "gameOver"     : self.game_over,
            "thinking"     : thinking,
            "winningCells" : winning_cells or [],
            "movesLog"     : self.moves_log,
        }


game   = GameState()
config = {}
game_start_time  = 0
MAX_GAME_SECONDS = 20 * 60   # حد اقصى 20 دقيقة للعبة


# كل الخطوط الممكنه للفوز افقي وعمودي وقطري
WINS = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]


#   فنكشن تقيم البورد لالفا بيتا
def evaluate_board_logic(board, player):
    opponent = "O" if player == "X" else "X"

    # تشييك داخلي للفوز
    def check_win_internal(b, p):
        for line in WINS:
            if all(b[i] == p for i in line):
                return True
        return False

    # لو فاز احد نرجع القيمة مباشرة
    if check_win_internal(board, player):
        return 100
    if check_win_internal(board, opponent):
        return -100

    # نحسب النقاط بناء على شكل الخطوط
    score = 0
    for line in WINS:
        pl_count  = sum(1 for i in line if board[i] == player)
        opp_count = sum(1 for i in line if board[i] == opponent)

        if opp_count == 0:
            score += 10 ** pl_count
        if pl_count == 0:
            score -= 10 ** opp_count

    return score


# تحط القطعه على البورد وتحذف الاقدم لو امتلى الحد
# وترجع ترو لو فاز
def put_piece_logic(board, history, player, cell):
    if len(history[player]) == 3:
        oldest_cell = history[player].pop(0)
        board[oldest_cell] = " "
    board[cell] = player
    history[player].append(cell)

    for line in WINS:
        if all(board[i] == player for i in line):
            return True
    return False

# الفا بيتا القورثم
# تسوي سيرتش في التري وترجع افضل هيورستك للحركه
def alpha_beta_logic(board, history, depth, alpha, beta, is_maximising, ai_player):
    opponent = "O" if ai_player == "X" else "X"
    def check_win_internal(b, p):
        for line in WINS:
            if all(b[i] == p for i in line):
                return True
        return False

    # الحالات اللي بنوقف فيها
    # سواء كان فوز او وصلنا لاعمق حد
    if check_win_internal(board, ai_player):
        return 100
    if check_win_internal(board, opponent):
        return -100
    if depth == 0:
        return evaluate_board_logic(board, ai_player)

    empty = [i for i in range(9) if board[i] == " "]
    current_player = ai_player if is_maximising else opponent

    if is_maximising:
        best = -math.inf
        for cell in empty:
            board_copy   = board[:]
            history_copy = {"X": history["X"][:], "O": history["O"][:]}
            put_piece_logic(board_copy, history_copy, current_player, cell)
            val  = alpha_beta_logic(board_copy, history_copy, depth - 1, alpha, beta, False, ai_player)
            best  = max(best, val)
            alpha = max(alpha, best)
            if alpha >= beta:
                break   # بنوقف لان ماراح نلاقي افضل
        return best
    else:
        best = math.inf
        for cell in empty:
            board_copy   = board[:]
            history_copy = {"X": history["X"][:], "O": history["O"][:]}
            put_piece_logic(board_copy, history_copy, current_player, cell)
            val  = alpha_beta_logic(board_copy, history_copy, depth - 1, alpha, beta, True, ai_player)
            best  = min(best, val)
            beta  = min(beta, best)
            if alpha >= beta:
                break   # بنوقف لان ماراح نلاقي افضل
        return best


#  تختار افضل حركة للالفا بيتا القورثم
def best_move_ab(g: GameState, depth: int, player: str) -> int:
    best_score = -math.inf
    best_cell  = None

    board   = g.board[:]
    history = {"X": g.hist_x[:], "O": g.hist_o[:]}
    empty_cells = [i for i in range(9) if board[i] == " "]

    if not empty_cells:
        return -1

    best_cell = empty_cells[0]   # fallback لو كل الحركات نفس النتيجه

    for cell in empty_cells:
        board_copy   = board[:]
        history_copy = {"X": history["X"][:], "O": history["O"][:]}
        put_piece_logic(board_copy, history_copy, player, cell)
        score = alpha_beta_logic(board_copy, history_copy, depth - 1, -math.inf, math.inf, False, player)

        if score > best_score:
            best_score = score
            best_cell  = cell

    return best_cell

# مونت كارلو القورثم
class MCTSNodeLogic:
    def __init__(self, board, history, player, parent=None, move=None):
        self.board   = board
        self.history = history
        self.player  = player   # اللاعب اللي دوره يلعب من هذي النود
        self.parent  = parent
        self.move    = move     # الحركة اللي وصلتنا هنا

        self.wins   = 0
        self.visits = 0

        self.untried_moves = [i for i in range(9) if board[i] == " "]
        self.children      = []

# تحسب اليو سي بي لكل نود
def ucb1_score_logic(node, parent_visits, exploration=1.41):
    if node.visits == 0:
        return float("inf")   # ما زرناها — اولويه قصوى
    return (node.wins / node.visits) + exploration * math.sqrt(
        math.log(parent_visits) / node.visits
    )


# تحسب وترجع افضل حركة باستخدام مونت كارلو
def best_move_mcts(g: GameState, simulations: int, player: str) -> int:
    board   = g.board[:]
    history = {"X": g.hist_x[:], "O": g.hist_o[:]}

    root = MCTSNodeLogic(board, {"X": history["X"][:], "O": history["O"][:]}, player)

    def check_win_internal(b, p):
        for line in WINS:
            if all(b[i] == p for i in line):
                return True
        return False

    for _ in range(simulations):
        node = root

        # المرحلة الاولى اننا نختار افضل نود نتحرك لها
        while node.untried_moves == [] and node.children != []:
            node = max(node.children, key=lambda c: ucb1_score_logic(c, node.visits))

        # المرحلة الثانيه نجرب حركه جديدة
        terminal_result = None
        if node.untried_moves:
            cell = random.choice(node.untried_moves)
            node.untried_moves.remove(cell)

            new_board   = node.board[:]
            new_history = {"X": node.history["X"][:], "O": node.history["O"][:]}
            mover       = node.player

            won = put_piece_logic(new_board, new_history, mover, cell)

            next_player = "O" if mover == "X" else "X"
            child = MCTSNodeLogic(new_board, new_history, next_player, parent=node, move=cell)
            node.children.append(child)
            node = child

            if won:
                terminal_result = 1 if mover == player else -1

        # المرحله الثالثه نلعب عشوائي لين نهاية اللعبة
        if terminal_result is None:
            sim_board   = node.board[:]
            sim_history = {"X": node.history["X"][:], "O": node.history["O"][:]}
            sim_player  = node.player
            seen_states = {}
            for _ in range(100):  # حد اقصى للمحاكاة لانها ما تعرف وقت القيم الحقيقي
                state_key = (tuple(sim_board), tuple(sim_history["X"]), tuple(sim_history["O"]))
                seen_states[state_key] = seen_states.get(state_key, 0) + 1

                if seen_states[state_key] > 1:
                    break    # نفس الوضع تكرر يعني اللعبة دخلت في لوب فنرجع تعادل

                empty = [i for i in range(9) if sim_board[i] == " "]
                move = random.choice(empty)
                won  = put_piece_logic(sim_board, sim_history, sim_player, move)
                if won:
                    break
                sim_player = "O" if sim_player == "X" else "X"

            if check_win_internal(sim_board, player):
                result = 1
            elif check_win_internal(sim_board, "O" if player == "X" else "X"):
                result = -1
            else:
                result = 0
        else:
            result = terminal_result

        # المرحله الرابعه نحدث احصائيات كل النودز من الكرنت للروت
        n = node
        while n is not None:
            n.visits += 1
            sign = 1 if n.player != player else -1
            n.wins += sign * result
            n = n.parent

    # لو ما فيه اي تشايلد نرجع حركة عشوائيه لان ماعندنا معلومه عن مين افضل حركه
    if not root.children:
        empty = [i for i in range(9) if board[i] == " "]
        return random.choice(empty) if empty else -1

    # نختار التشايلد الاكثر زيارة معناته هو الافضل
    best_child = max(root.children, key=lambda c: c.visits)
    return best_child.move


#  نشغل حركة الذكاء حسب الالقورثم المختاره
def ai_move(g: GameState, agent_str: str, player: str) -> int:
    algo, param = agent_str.split(':')
    param = int(param)
    if algo == 'ab':
        return best_move_ab(g, param, player)
    else:
        return best_move_mcts(g, param, player)


# نشيك لو اللعبه تجاوزت الوقت المسموح
def is_timeout() -> bool:
    return time.time() - game_start_time > MAX_GAME_SECONDS

@app.route('/')
def index():
    return send_from_directory('.', 'interface.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)


# بدايه القيم
@app.route('/api/start', methods=['POST'])
def api_start():
    global config, game_start_time
    data            = request.json
    config          = data.get('config', {})
    game.reset()
    game.turn       = 'X'
    game_start_time = time.time()

    state_dict = game.to_dict()

    # لو كان الذكاء هو النخله نبدا حركته على طول
    # النخله هي بديل الاكس
    x_agent = config.get('xAgent', 'human')
    if x_agent != 'human':
        state_dict = _do_ai_turn('X')

    return jsonify(state_dict)

# حركة البلاير البشر
@app.route('/api/move', methods=['POST'])
def api_move():
    data   = request.json
    idx    = data.get('cell')
    player = game.turn

    if is_timeout():
        game.game_over = True
        game.winner    = "TIMEOUT"
        return jsonify(game.to_dict())

    if game.game_over:
        return jsonify(game.to_dict()), 400

    if not game.is_valid(idx):
        return jsonify({"error": "حركة غير صالحة"}), 400
    t0 = time.time()
    game.apply_move(idx, player)
    elapsed = time.time() - t0
    game.moves_log.append({
        "player": player,
        "cell"  : idx,
        "agent" : "human",
        "time"  : round(elapsed, 4)
    })
    winner, wcells = game.check_winner()
    if winner:
        game.winner    = winner
        game.game_over = True
        return jsonify(game.to_dict(winning_cells=wcells))

    # نبدل الدور
    opp       = 'O' if player == 'X' else 'X'
    game.turn = opp
    # لو الخصم ذكاء نشغله على طول
    opp_agent = config.get('xAgent') if opp == 'X' else config.get('oAgent')
    if opp_agent and opp_agent != 'human':
        return jsonify(_do_ai_turn(opp))

    return jsonify(game.to_dict())

# دور الذكاء
@app.route('/api/ai_turn', methods=['POST'])
def api_ai_turn():
    if is_timeout():
        game.game_over = True
        game.winner    = "TIMEOUT"
        return jsonify(game.to_dict())

    player = game.turn
    agent  = config.get('xAgent') if player == 'X' else config.get('oAgent')
    if not agent or agent == 'human':
        return jsonify({"error": "ليس دور الذكاء"}), 400
    return jsonify(_do_ai_turn(player))

# الفنكشن اللي تنفذ حركه الذكاء
def _do_ai_turn(player: str) -> dict:
    agent   = config.get('xAgent') if player == 'X' else config.get('oAgent')
    t0      = time.time()
    idx     = ai_move(game, agent, player)
    elapsed = time.time() - t0


    game.apply_move(idx, player)
    game.moves_log.append({
        "player": player,
        "cell"  : idx,
        "agent" : agent,
        "time"  : round(elapsed, 4)
    })

    winner, wcells = game.check_winner()
    if winner:
        game.winner    = winner
        game.game_over = True
        return game.to_dict(winning_cells=wcells)

    # نبدل الدور
    opp       = 'O' if player == 'X' else 'X'
    game.turn = opp

    return game.to_dict()


# ري سيت للعبه
@app.route('/api/reset', methods=['POST'])
def api_reset():
    global game_start_time
    game.reset()
    game_start_time = time.time()
    return jsonify(game.to_dict())

# ترجع الستيت الحالي
@app.route('/api/state', methods=['GET'])
def api_state():
    return jsonify(game.to_dict())

#    تشغل قيم وبس ترجع لنا مين فاز عشان الاكسبرمنتس
def play_simulated_game(x_agent: str, o_agent: str, max_moves: int = 200) -> str:
    board   = [" "] * 9
    history = {"X": [], "O": []}
    current_player = 'X'

    def check_win_internal(b, p):
        for line in WINS:
            if all(b[i] == p for i in line):
                return True
        return False

    # كلاس يحاكي حاله القيم
    class TempState:
        def __init__(self, b, hx, ho, t):
            self.board  = b
            self.hist_x = hx
            self.hist_o = ho
            self.turn   = t
            
    # حد 200 حركة للمحاكاة الوهمية بس ، اللعبة الحقيقيه حدها 20 دقيقة
    for _ in range(max_moves):
        # نتاكد من الفايز قبل كل حركه
        if check_win_internal(board, 'X'): return 'X'
        if check_win_internal(board, 'O'): return 'O'

        agent   = x_agent if current_player == 'X' else o_agent
        t_state = TempState(board[:], history["X"][:], history["O"][:], current_player)
        algo, param = agent.split(':')
        param = int(param)
        if algo == 'ab':
            move = best_move_ab(t_state, param, current_player)
        else:
            move = best_move_mcts(t_state, param, current_player)
        put_piece_logic(board, history, current_player, move)
        if check_win_internal(board, current_player):
            return current_player

        current_player = 'O' if current_player == 'X' else 'X'
    #  لما اللعبة تشتغل 200 حركة بدون ما يفوز احد فترجع تعادل
    return "Draw"

# تسوي رن للاكسبرمنت وترجع الريزلت
def run_experiment(name: str, x_agent: str, o_agent: str, games: int = 5) -> dict:
    results = {"X": 0, "O": 0, "Draw": 0}
    for i in range(games):
        res = play_simulated_game(x_agent, o_agent)
        results[res] += 1
    return results

#    الاكسبرمنتس
@app.route('/api/run_experiment', methods=['POST'])
def api_run_experiment():
    data     = request.json
    exp_type = data.get('experiment_type')
    N        = int(data.get('games', 3))   # عدد الجولات يجي من الفرونت
    if exp_type == 'ai_vs_ai':
        # اكسبرمنت 1 — الفا بيتا ضد الفا بيتا
        ab_ab_1 = run_experiment("AB k=2 vs AB k=5",  "ab:2",  "ab:5",  games=N)
        ab_ab_2 = run_experiment("AB k=2 vs AB k=10", "ab:2",  "ab:10", games=N)
        ab_ab_3 = run_experiment("AB k=10 vs AB k=5", "ab:10", "ab:5",  games=N)
        # اكسبرمنت 2 — الفا بيتا ضد مونت كارلو
        ab_mc_1 = run_experiment("AB k=2 vs MCTS 200",   "ab:2",     "mcts:200",  games=N)
        ab_mc_2 = run_experiment("MCTS 1000 vs AB k=2",  "mcts:1000","ab:2",      games=N)
        ab_mc_3 = run_experiment("AB k=10 vs MCTS 1000", "ab:10",    "mcts:1000", games=N)
        ab_mc_4 = run_experiment("MCTS 500 vs AB k=5",   "mcts:500", "ab:5",      games=N)
        # اكسبرمنت 3 — مونت كارلو ضد مونت كارلو
        mc_mc_1 = run_experiment("MCTS 500 vs MCTS 200",  "mcts:500",  "mcts:200",  games=N)
        mc_mc_2 = run_experiment("MCTS 1000 vs MCTS 200", "mcts:1000", "mcts:200",  games=N)
        mc_mc_3 = run_experiment("MCTS 500 vs MCTS 1000", "mcts:500",  "mcts:1000", games=N)
        return jsonify({
            "success": True,
            "type"   : "ai_vs_ai",
            "note"   : f"{N} games each, random results (no fixed seed)",
            "ab_vs_ab": [
                {"name": "AB k=2 vs AB k=5",  **ab_ab_1},
                {"name": "AB k=2 vs AB k=10", **ab_ab_2},
                {"name": "AB k=10 vs AB k=5", **ab_ab_3},
            ],
            "ab_vs_mcts": [
                {"name": "AB k=2 vs MCTS 200",   **ab_mc_1},
                {"name": "MCTS 1000 vs AB k=2",  **ab_mc_2},
                {"name": "AB k=10 vs MCTS 1000", **ab_mc_3},
                {"name": "MCTS 500 vs AB k=5",   **ab_mc_4},
            ],
            "mcts_vs_mcts": [
                {"name": "MCTS 500 vs MCTS 200",  **mc_mc_1},
                {"name": "MCTS 1000 vs MCTS 200", **mc_mc_2},
                {"name": "MCTS 500 vs MCTS 1000", **mc_mc_3},
            ],
        })
    elif exp_type == 'computation_time':
        # نقيس وقت اول حركة لكل خوارزمية
        ab_times   = {}
        mcts_times = {}
        # الفا بيتا — نجرب ثلاث اعماق
        for k in [2, 5, 10]:
            test_game = GameState()
            t0 = time.time()
            best_move_ab(test_game, k, 'X')
            ab_times[f"k{k}"] = round((time.time() - t0) * 1000, 2)
        # مونت كارلو - نجرب ثلاث احجام محاكاة
        for s in [200, 500, 1000]:
            test_game = GameState()
            t0 = time.time()
            best_move_mcts(test_game, s, 'X')
            mcts_times[f"s{s}"] = round((time.time() - t0) * 1000, 2)
        return jsonify({
            "success"    : True,
            "type"       : "time",
            "note"       : "First move timing on empty board",
            "k2_time"    : ab_times["k2"],
            "k5_time"    : ab_times["k5"],
            "k10_time"   : ab_times["k10"],
            "s200_time"  : mcts_times["s200"],
            "s500_time"  : mcts_times["s500"],
            "s1000_time" : mcts_times["s1000"],
        })
    return jsonify({"success": False, "error": "Unknown experiment"}), 400

#المين
if __name__ == '__main__':
    print(" http://localhost:5000")
    app.run(debug=True, port=5000)