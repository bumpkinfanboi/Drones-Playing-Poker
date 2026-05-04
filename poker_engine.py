import random
from LETMEHAVEMYIFSTATEMENTS import *
from not_flight_stuff.test import InputError


class Players:
    def __init__(self):
        self.player = {}
        self.game_state = {
            "players_turn" : 1,
            "call_amount" : 0,
            "pot" : 0,
            "sb" : 0,
            "bb" : 0,
        }
    def starting_conditions(self, player_count, stack_size, button, drone_pos, small_blind_amount, big_blind_amount):
        for i in range(1,player_count+1):
            self.player[i] = {
                "stack" : stack_size,
                "button" : False,
                "small_blind" : False,
                "big_blind" : False,
                "drone" : False,
                "folded" : False,
            }
        self.game_state["sb"] = small_blind_amount
        self.game_state["bb"] = big_blind_amount
        self.game_state["players_turn"] = button + 1
        if button + 1 > player_count:
            self.game_state["players_turn"] = 1
        self.player[button]["button"] = True
        self.player[button + 1]["small_blind"] = True
        self.player[button + 2]["big_blind"] = True
        self.player[drone_pos]["drone"] = True
        return self.player
players = Players()
def query_conditions():
    _input_players = InputError("How many players? ")
    _stack_size = int(input("How much per stack? "))
    _button_placement = int(input("Which player has button? (usually 1) "))
    _drone_pos = int(input("Which seat is drone? "))
    _small_blind_amount = int(input("How much are small blinds? "))
    _big_blind_amount = int(input("How much are big blinds? "))
    print(players.starting_conditions(_input_players, _stack_size, _button_placement, _drone_pos, _small_blind_amount, _big_blind_amount))
query_conditions()
def player_action(player, action, amount):
    if action == "check":
        if players.game_state["to_call"] == 0:
            players.game_state["players_turn"] += 1
        else: print("fuck off no")
    elif action == "bet":
        if amount < players.player["stack"]:
            players.player[player]["stack"] -= amount
            players.game_state["pot"] += amount
            players.game_state["to_call"] += amount
            players.game_state["players_turn"] += 1
        else:
            raise NameError("UR NOT HIM")
