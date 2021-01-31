class Backend:
    # bool: whether slots are available
    def slots_available(self):
        pass

    # VaccineSlots: returns slot data
    def get_slots(self):
        pass
    
    # returns public URL
    def public_url(self):
        pass

class VaccineSlots:
    def __init__(self, location, url, slots=[]):
        self.location = location
        self.url = url
        self.slots = slots

    def add_slot(self, slot):
        self.slots.append(slot)