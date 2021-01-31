class Backend:
    # bool: whether slots are available
    def slots_available(self):
        pass

    # VaccineSlots: returns slot data
    def get_slots(self):
        pass

class VaccineSlots:
    def __init__(self, location, slots=[]):
        self.location = location
        self.slots = slots

    def add_slot(self, slot):
        self.slots.append(slot)