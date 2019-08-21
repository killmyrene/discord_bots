def format_csv_entries(n):
    entries = n.split(',')
    return [i for i in entries if i]

class PriorityInfo:
    def __init__(self, csv_contents:str):
        print("foo")
        csv_contents_list = csv_contents.split("\r\n")[:6]
        entries = list(map(format_csv_entries, csv_contents_list))

        print(entries)
        
        if len(entries) != 6:
            raise ValueError("Entries length should be exactly 6, with score, star, priority 0 to 3 in them")
        
        self.score = int(entries[0][1])
        self.stars = int(entries[1][1])

        self.priority0 = entries[2][1:]
        self.priority1 = entries[3][1:]
        self.priority2 = entries[4][1:]
        self.priority3 = entries[5][1:]
        
        self.numPriorities = len(self.priority0) + \
            len(self.priority1) + \
            len(self.priority2) + \
            len(self.priority3)