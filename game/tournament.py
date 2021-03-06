import itertools
import signal, os
from match import Match
from player import Player
from gameboard import GameBoard
from time_to_run import TimeLimitsCalculator
from time_to_run import TimeLimitReached

class NotEnoughStrategies(Exception):
    def __init__(self, number_of_strategies):
        self.number_of_strategies = number_of_strategies

class Tournament(object):
    def __init__(self, strategies, prepare_time_limit=5, play_time_limit=0.5):
        self.prepare_time_limit = prepare_time_limit
        self.play_time_limit = play_time_limit
        if len(strategies) < 3:
            raise NotEnoughStrategies(len(strategies))
        self._pairs_of_strategies = list(itertools.permutations(strategies, 2))
        self._number_of_matches = len(self._pairs_of_strategies)
        self._strategies_names = [type(strategy()).__name__ for strategy in strategies]
        self._scores_dict = {}
        for name in self._strategies_names:
            self._scores_dict[name] = 0
        self._matches_per_strategy = 2 * (self._number_of_matches - 1)
        self._matches = []
        self._timeout = None
        self._results_table = []
        self._generate_matches()

    def _generate_matches(self):
        for pair_of_strategies in self._pairs_of_strategies:
            board = GameBoard()
            player_one = Player('W', pair_of_strategies[0]())
            player_two = Player('B', pair_of_strategies[1]())
            self._matches.append(Match(player_one, player_two, board))

    def get_matches(self):
        return self._matches

    def get_results_table(self):
        return self._results_table

    def get_scores(self):
        return self._scores_dict

    def _timeout_handler(self, arg1, arg2):
        raise TimeLimitReached(self._timeout)

    def run(self):
        for match in self._matches:
            abort_current_match = False
            penalized_player = None
            signal.signal(signal.SIGALRM, self._timeout_handler)
            for player in match.get_players():
                self._timeout = self.prepare_time_limit
                signal.setitimer(signal.ITIMER_REAL,self.prepare_time_limit)
                try:
                    player.prepare()
                except TimeLimitReached:
                    abort_current_match = True
                    penalized_player = player
                    break
                signal.alarm(0)
            players = match.get_players()
            if not abort_current_match:
                while not match.is_over():
                    self._timeout = self.play_time_limit
                    signal.setitimer(signal.ITIMER_REAL,self.play_time_limit)
                    try:
                        match.play_next_turn()
                    except TimeLimitReached:
                        abort_current_match = True
                        penalized_player = match.get_active_player()
                        break
                    signal.alarm(0)
                if not abort_current_match:
                    player_one_strategy_name = players[0].get_strategy_name()
                    player_two_strategy_name = players[1].get_strategy_name()
                    if match.who_won() is not None:
                        self._scores_dict[match.who_won().get_strategy_name()] += 3
                        self._results_table.append((
                            player_one_strategy_name,
                            player_two_strategy_name,
                            match.who_won().get_strategy_name()))
                    else:
                        self._scores_dict[player_one_strategy_name] += 1
                        self._scores_dict[player_two_strategy_name] += 1
                        self._results_table.append([
                            player_one_strategy_name,
                            player_two_strategy_name,
                            None])
            if abort_current_match:
                player_one_strategy_name = players[0].get_strategy_name()
                player_two_strategy_name = players[1].get_strategy_name()
                for index, player in enumerate(players):
                    if penalized_player == player:
                        penalized_player_strategy_name = players[index].get_strategy_name()
                    else:
                        non_penalized_player_strategy_name = players[index].get_strategy_name()
                self._scores_dict[penalized_player_strategy_name] += 0
                self._scores_dict[non_penalized_player_strategy_name] += 3
                self._results_table.append([
                        player_one_strategy_name,
                        player_two_strategy_name,
                        non_penalized_player_strategy_name])
