"""
Stores all the state a server has
"""
class ServerState():
    def __init__(self):
        self.running_process = None
        self.extract_folder_path = None
        self.arch_file_path = None
        self.location_info = {}
        self.ids = {}
        self.slotinfos = {}
        self.port = None
        self.restarting = False
        self.admin = None
        self.start = None
        self.released_games = {} # dictionary and not set for json encoding lol