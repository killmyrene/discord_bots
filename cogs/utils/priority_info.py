from functools import reduce

def format_csv_entries(n):
    entries = n.split(',')
    return [i for i in entries if i]

class PriorityInfo:
    def __init__(self, csv_contents:str):
        csv_contents_list = csv_contents.split("\r\n")[:6]
        entries = list(map(format_csv_entries, csv_contents_list))

        if len(entries) != 6:
            raise ValueError("Entries length should be exactly 6, with score, star, priority 0 to 3 in them")
        
        self.score = int(entries[0][1])
        self.stars = int(entries[1][1])
        
        self.priority = [[]] * 4
        self.priority[0] = entries[2][1:]
        self.priority[1] = entries[3][1:]
        self.priority[2] = entries[4][1:]
        self.priority[3] = entries[5][1:]
        
        self.numPriorities = len(self.priority[0]) + \
        len(self.priority[1]) + \
        len(self.priority[2]) + \
        len(self.priority[3])