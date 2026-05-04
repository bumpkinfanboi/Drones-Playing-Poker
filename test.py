"""class Player:
    def __init__(self, name):
        self.name = name
        self.attributes = {}
    def money(self, hand):
        self.attributes["money"] = hand
        return self.attributes
    def speed(self, speed):
        self.attributes["speed"] = speed
        return self.attributes

players = {}

try:
    amount = int(input("How many players? "))
    for i in range(1, amount+1):
        players[i] = Player(i)
except:
    print("Please enter a number")

players[1].speed(100)
players[2].speed(200)
players[3].speed(300)
players[3].money(300)

for i in range(1,len(players)+1):
    print(players[i].attributes)"""

def InputError(message="hello world:",type=int):
    while True:
        try:
            return type(input(message))
        except:
            print("Error")
        else:
            break