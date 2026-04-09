from collections import OrderedDict

class BufferPool:
    def __init__(self, size, policy="LRU"):
        self.size = size
        self.frames = []
        self.page_table = {}
        self.policy = policy.upper()

        # LRU: ordered dict tracks access order
        if self.policy == "LRU":
            self.lru_order = OrderedDict()

        # Clock: clock hand + reference bits
        elif self.policy == "CLOCK":
            self.clock_hand = 0
            self.ref_bits = {}

    def fetch_page(self, page_id):
        if page_id in self.page_table:
            print(f"HIT  - page {page_id}")
            self._on_hit(page_id)
        else:
            print(f"MISS - page {page_id}")
            if len(self.frames) == self.size:
                self.evict()
            self.frames.append(page_id)
            self.page_table[page_id] = True
            self._on_load(page_id)

    def _on_hit(self, page_id):
        if self.policy == "LRU":
            self.lru_order.move_to_end(page_id)
        elif self.policy == "CLOCK":
            self.ref_bits[page_id] = 1

    def _on_load(self, page_id):
        if self.policy == "LRU":
            self.lru_order[page_id] = True
        elif self.policy == "CLOCK":
            self.ref_bits[page_id] = 1

    def evict(self):
        if self.policy == "LRU":
            victim, _ = self.lru_order.popitem(last=False)
            self.frames.remove(victim)
            del self.page_table[victim]
            print(f"       evicted page {victim} (LRU)")

        elif self.policy == "CLOCK":
            while True:
                candidate = self.frames[self.clock_hand]
                if self.ref_bits[candidate] == 0:
                    # Evict this page
                    self.frames.pop(self.clock_hand)
                    del self.page_table[candidate]
                    del self.ref_bits[candidate]
                    # Don't advance hand
                    # it now points to the next frame naturally
                    if self.clock_hand >= len(self.frames):
                        self.clock_hand = 0
                    print(f"       evicted page {candidate} (CLOCK)")
                    break
                else:
                    # Give a second chance:
                    # - clear ref bit
                    # - the hand will advance for the next iteration
                    self.ref_bits[candidate] = 0
                    self.clock_hand = (self.clock_hand + 1) % len(self.frames)

    def display(self):
        print(f"  frames: {self.frames}")
        if self.policy == "CLOCK":
            bits = [self.ref_bits[p] for p in self.frames]
            hand = self.clock_hand if self.frames else 0
            pointer = ["^" if i == hand else " " for i in range(len(self.frames))]
            print(f"  ref bits: {bits}")
            print(f"  clock:   {'  '.join(pointer)}")
        print()


if __name__ == "__main__":
    accesses = [1, 2, 3, 4, 1, 5, 2, 6, 3, 1]

    for policy in ["LRU", "CLOCK"]:
        print(f"{'='*40}")
        print(f" Policy: {policy}  |  Buffer size: 3")
        print(f"{'='*40}")
        bp = BufferPool(size=3, policy=policy)
        for page in accesses:
            bp.fetch_page(page)
            bp.display()