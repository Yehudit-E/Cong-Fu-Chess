from Bus.EventBus import Event

class ScoreBoard:
    def __init__(self):
        self.piece_values = {
            "P": 1,
            "K": 3,
            "B": 3,
            "R": 5,
            "Q": 9
        }
        self.scoreB = 0
        self.scoreW = 0

    def handle_capture(self, event: Event):
        piece = event.data["piece"]
        piece_type = piece[0]
        if piece[1] == "B":
            self.scoreB += self.piece_values.get(piece_type, 0)
            print(f"Black captured {piece_type}, scoreB: {self.scoreB}")
        else:
            self.scoreW += self.piece_values.get(piece_type, 0)
            print(f"White captured {piece_type}, scoreW: {self.scoreW}")
