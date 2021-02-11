from . import Notifier

import csv
import os
import datetime

class CSVLogNotifier(Notifier):
    def __init__(self, filename):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, 'w') as f:
                cw = csv.writer(f)
                cw.writerow(['Date', 'Location', 'Address', 'Count', 'Vaccine Type', 'Details'])

    def notify(self, slots):
        with open(self.filename, 'a') as f:
            cw = csv.writer(f)
            for s in slots.slots_struct:
                cw.writerow([
                    s.date,
                    s.location,
                    s.address,
                    s.count,
                    s.vaccine_type,
                    s.details
                ])
    
    def notify_problem(self, message):
        print("PROBLEM: %s" % message)