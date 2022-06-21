class PointBuyer:
    def __init__(self, base: int = 10, min_max=(6, 18), increases=(14, 16)):
        self.base = base
        self.min_max = min_max
        self.increases = increases

    def points(self, score: int):
        if self.min_max[0] <= score <= self.min_max[1]:
            return score - self.base + sum(score - x for x in self.increases if score > x)
