class Backend:
    # bool: whether slots are available
    def slots_available(self):
        pass

    # VaccineSlots: returns slot data
    def get_slots(self):
        pass
    
    def __repr__(self):
        return "%s" % (self.__class__.__name__)

class VaccineSlots:
    def __init__(self, location, url, slots=None):
        self.location = location
        self.url = url
        self.slots = slots or []

    def add_slot(self, slot):
        self.slots.append(slot)