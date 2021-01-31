from . import Backend, VaccineSlots
import requests

class CurativeBackend(Backend):
    TESTING_SITES_API = "https://labtools.curativeinc.com/api/v1/testing_sites/%s"

    def __init__(self, locid):
        self.locid = locid

    def __repr__(self):
        return "CurativeBackend(%s)" % self.locid

    def get_testing_sites(self):
        r = requests.get(self.TESTING_SITES_API % self.locid)
        return r.json()

    def get_slots(self):
        sites = self.get_testing_sites()
        s = VaccineSlots("%s (%s, %s, %s %s)" % (sites["name"], sites["street_address_1"], sites["city"], sites["state"], sites["postal_code"]))

        for win in sites["appointment_windows"]:
            if win["slots_available"] > 0:
                s.add_slot(win)

        return s

    def slots_available(self):
        s = self.get_slots()
        return len(s.slots) > 0