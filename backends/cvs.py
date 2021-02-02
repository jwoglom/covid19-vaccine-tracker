from . import Backend, VaccineSlots
import requests
import logging

logger = logging.getLogger(__name__)

class CVSPharmacyBackend(Backend):
    PUBLIC_URL = 'https://www.cvs.com/vaccine/intake/store/cvd-store-select/first-dose-select'
    STORES_API = 'https://www.cvs.com/Services/ICEAGPV1/immunization/1.0.0/getIMZStores'
    # YYYY-MM-DD, CVS_xxxx
    TIMESLOT_API = 'https://api.cvshealth.com/scheduler/v3/clinics/availabletimeslots?visitStartDate=%s&visitEndDate=%s&clinicId=%s'

    NOT_FOUND = 'No stores with immunizations found'
    NOT_AVAILABLE = 'Inventory unavailable for all stores'

    def __init__(self, address_zip, radius_miles=25):
        self.address_zip = address_zip
        self.radius_miles = radius_miles

    def __repr__(self):
        return "CVSPharmacyBackend(%s, %s)" % (self.address_zip, self.radius_miles)
    
    def public_url(self):
        return self.PUBLIC_URL
    
    def build_stores_data(self):
        return {
            "requestMetaData": {
                "appName": "CVS_WEB",
                "lineOfBusiness": "RETAIL",
                "channelName": "WEB",
                "deviceType": "DESKTOP",
                "deviceToken": "7777",
                "apiKey": "a2ff75c6-2da7-4299-929d-d670d827ab4a",
                "source": "ICE_WEB",
                "securityType": "apiKey",
                "responseFormat": "JSON",
                "type": "cn-dep"
            },
            "requestPayloadData": {
                "selectedImmunization": ["CVD"],
                "distanceInMiles": int(self.radius_miles),
                "searchCriteria": {
                    "addressLine": "%s" % self.address_zip
                }
            }
        }
    
    def get_stores_json(self):
        r = requests.post(self.STORES_API, json=self.build_stores_data())
        if r.status_code != 200:
            logger.error("Error in cvs stores: %s " % r.text)
            logger.error("Data: %s" % self.build_stores_data())
        return r.json()
    
    def get_timeslots_json(self, start_date, end_date, store_id):
        r = requests.get(self.TIMESLOT_API % (start_date, end_date, store_id), headers={
            'x-api-key': 'Q2fDhMdta6oqfkmnGJfh6SP9Mwmn7dd9'
        })
        if r.status_code != 200:
            logger.error("Error in cvs timeslots: %s " % r.text)
            logger.error("Data: %s %s %s" % (start_date, end_date, store_id))
        return r.json()
    
    def get_timeslots(self, location, dates):
        store_id = location.get('schedulerRefId')
        data = self.get_timeslots_json(dates[0], dates[-1], store_id)
        details = data.get('details', [])
        ret = []
        for clinic in details:
            for ts in clinic.get('timeSlots'):
                ret.append(ts)
        
        return ret
        

    def slots_available(self):
        j = self.get_stores_json()

        status = j.get('responseMetaData', {}).get('statusDesc')
        if status in (self.NOT_AVAILABLE, self.NOT_FOUND):
            return False
        
        return True


    def get_slots(self):
        slots = VaccineSlots("CVS Pharmacy", self.public_url())
        j = self.get_stores_json()

        status = j.get('responseMetaData', {}).get('statusDesc')
        if status in (self.NOT_AVAILABLE, self.NOT_FOUND):
            return slots
        
        r = j.get('responsePayloadData', {})
        dates = r.get('availableDates', [])
        
        locations = r.get('locations', [])
        for l in locations:
            store = "%s %s, %s %s" % (l.get('addressLine'), l.get('addressCityDescriptionText'), l.get('addressState'), l.get('addressZipCode'))
            avail = l.get('immunizationAvailability', {}).get('available')

            if len(avail) > 0:
                timeslots = self.get_timeslots(l, dates)
                if timeslots:
                    slots.add_slot("*%s* has %s available between %s and %s (%d timeslots)" % (store, avail, timeslots[0], timeslots[-1], len(timeslots)))
                else:
                    slots.add_slot("*%s* has %s available with unknown timeslots" % (store, avail))

        return slots
