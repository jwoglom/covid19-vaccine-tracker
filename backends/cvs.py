from . import Backend, VaccineSlots, Availability
from .common import random_user_agent

import requests
import logging
import arrow
import json
import random
import time

logger = logging.getLogger(__name__)

class CVSPharmacyBackend(Backend):
    PUBLIC_URL = 'https://www.cvs.com/vaccine/intake/store/cvd-schedule'
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
    
    def build_stores_data(self, payload=None):
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
            } if not payload else payload
        }
    
    def headers(self, json=True):
        return {
            "accept": "application/json" if json else "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "user-agent": random_user_agent(),
            "Accept-Encoding": "gzip, deflate", 
            "Accept-Language": "en-US,en-GB;q=0.9,en;q=0.8", 
            "Dnt": "1", 
            "Upgrade-Insecure-Requests": "1"
        }
    
    def get_stores_json(self, req):
        r = req.post(self.STORES_API, json=self.build_stores_data(), headers=self.headers())
        if r.status_code != 200:
            logger.error("Error in cvs stores (%s): %s " % (r.status_code, r.text))
            logger.error("Data: %s" % json.dumps(self.build_stores_data()))
        return r.json()
    
    def get_timeslots_json(self, start_date, end_date, store_id, req):
        r = req.get(self.TIMESLOT_API % (start_date, end_date, store_id), headers={
            'x-api-key': 'Q2fDhMdta6oqfkmnGJfh6SP9Mwmn7dd9',
            **self.headers()
        })
        if r.status_code != 200:
            logger.error("Error in cvs timeslots: %s " % r.text)
            logger.error("Data: %s %s %s" % (start_date, end_date, store_id))
        return r.json()
    
    def get_timeslots(self, location, dates, req):
        store_id = location.get('schedulerRefId')
        data = self.get_timeslots_json(dates[0], dates[-1], store_id, req)
        details = data.get('details', [])
        ret = []
        for clinic in details:
            for ts in clinic.get('timeSlots'):
                ret.append(ts)
        
        return ret

    def slots_available(self):
        j = self.get_stores_json(requests.Session())

        status = j.get('responseMetaData', {}).get('statusDesc')
        logger.info("CVS stores status: %s" % status)

        self._cached_store_json = j
        if status in (self.NOT_AVAILABLE, self.NOT_FOUND):
            return False
        
        return True


    def get_slots(self):
        req = requests.Session()

        slots = VaccineSlots("CVS Pharmacy", self.public_url())
        j = self._cached_store_json if self._cached_store_json else self.get_stores_json(req)

        status = j.get('responseMetaData', {}).get('statusDesc')
        if status in (self.NOT_AVAILABLE, self.NOT_FOUND):
            logger.info("CVS stores status: %s" % status)
            return slots
        
        r = j.get('responsePayloadData', {})
        dates = r.get('availableDates', [])
        
        locations = r.get('locations', [])
        for l in locations:
            store = "%s %s, %s %s" % (l.get('addressLine'), l.get('addressCityDescriptionText'), l.get('addressState'), l.get('addressZipCode'))
            avail = ', '.join(l.get('immunizationAvailability', {}).get('available'))
            logger.info("CVS store %s has avail %d: %s" % (store, len(avail), avail))

            if len(avail) > 0:
                time.sleep(random.randint(4, 8))
                timeslots = self.get_timeslots(l, dates, req)
                if timeslots:
                    slots.add_slot(
                        "*%s* has %s available %s between %s and %s (%d timeslots)" % (store, avail, self.humanize_date(timeslots[0]), self.prettify_date(timeslots[0]), self.prettify_date(timeslots[-1]), len(timeslots)),
                        struct=Availability(
                            date=timeslots[0],
                            location=l.get('addressLine'),
                            address=store,
                            count=len(timeslots),
                            vaccine_type=avail,
                            details=None
                        ))
                else:
                    slots.add_slot("*%s* has %s available with unknown timeslots: dates %s" % (store, avail, dates))

        return slots

    def humanize_date(self, d):
        return arrow.get(d).humanize()

    def prettify_date(self, d):
        return arrow.get(d).format('MM/DD hh:mma')