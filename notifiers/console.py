from . import Notifier

class ConsoleNotifier(Notifier):
    def notify(self, slots):
        print("NOTIFY: %s" % slots.location)
        for s in slots.slots:
            print("\t%s" % s)