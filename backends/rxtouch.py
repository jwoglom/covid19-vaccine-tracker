from . import Backend, VaccineSlots
import requests

class RxTouchBackend(Backend):
    INDEX_URL = "https://%s.rxtouch.com/rbssched/program/covid19/Patient/Advisory"
    CHECK_ZIP_API = "https://%s.rxtouch.com/rbssched/program/covid19/Patient/CheckZipCode"

    NOT_AVAIL_MSG = "There are no locations with available appointments"

    def __init__(self, locid, zip):
        self.locid = locid
        self.zip = zip

    def __repr__(self):
        return "RxTouchBackend(%s, %s)" % (self.locid, self.zip)

    def check_zip(self):
        output = None
        with requests.Session() as s:
            # Initialize cookies
            s.get(self.INDEX_URL % self.locid)
            r = s.post(self.CHECK_ZIP_API % self.locid, data={
                "zip": self.zip,
                "appointmentType": 5957,
                "PatientInterfaceMode": 0
            })
            output = r.text
        return output

    def slots_available(self):
        return self.NOT_AVAIL_MSG not in self.check_zip()

    def get_slots(self):
        return VaccineSlots(self.check_zip())
