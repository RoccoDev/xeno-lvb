from ext import register_mappers
from xeno_lvb import u32, f32, u16

# ENEW (Enemy wave), a single container for an enemy wave instance
class Xc3Enew():
    def __init__(self, entry):
        # Not quite sure
        self.auto_start = entry[4] != 0
        self.start_wave = u16(entry[8:])
        # Seems to be + 1 (e.g. start = 0, final = 4 => 4 waves total).
        # Note that it's not length but it's always end > start
        self.end_wave = u16(entry[10:])

    def to_json(self):
        return {
            'auto_start': self.auto_start,
            'start_wave': self.start_wave,
            'end_wave': self.end_wave,
        }

# ENWP (Enemy wave pop?), wave instances
class Xc3Enwp():
    def __init__(self, entry):
        # Min enemies? Has to do with enemy count
        self.unk_1 = u32(entry)
        # Seconds to automatically start the next wave
        self.max_time = f32(entry[4:])
        self.enemy_member_min = u16(entry[12:])
        self.enemy_member_max = u16(entry[14:])

    def to_json(self):
        return {
            'max_time': self.max_time,
            'enemy_min': self.enemy_member_min,
            'enemy_max': self.enemy_member_max
        }

register_mappers({
    b"ENEW": Xc3Enew,
    b"ENWP": Xc3Enwp
}, xc3=True)
