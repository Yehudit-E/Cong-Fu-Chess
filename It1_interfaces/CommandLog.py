from Bus.EventBus import Event

class CommandLog:
    def __init__(self):
        self.moves = []

    def handle_command(self, event: Event):
        move = f"{event.data['piece']} {event.data['description']} at {event.data['time']}"
        self.moves.append(move)
        print(f"Move recorded: {move}")