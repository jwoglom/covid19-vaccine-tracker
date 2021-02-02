import argparse
import time
import logging

from config import BACKENDS, NOTIFIERS

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Checks for available vaccination slots")
    parser.add_argument('--interval', '-i', dest='interval', type=int, default=60, help='The interval to check backends for')
    parser.add_argument('--verbose', '-v', action='store_true', help='enable debug output')
    parser.add_argument('--test', '-t', action='store_true', help='use test backends (fake data)')
    parser.add_argument('--console', '-c', action='store_true', help='only use console backend')

    return parser.parse_args()

def main():
    args = parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    def get_backends():
        if args.test:
            from config import TEST_BACKENDS
            return TEST_BACKENDS

        return BACKENDS

    def get_notifiers():
        if args.console:
            from notifiers.console import ConsoleNotifier
            return [ConsoleNotifier()]

        return NOTIFIERS

    def run_backend(b):
        try:
            if b.slots_available():
                logger.warning("Slots available for backend: %s" % b)
                slots = b.get_slots()
                if slots and slots.slots:
                    logger.warning("Available slots: %d" % len(slots.slots))
                    run_notify(slots)
            else:
                logger.info("No slots available for backend: %s" % b)
        except Exception:
            logger.exception("Unable to run backend: %s" % b)

    def run_notify(slots):
        for n in get_notifiers():
            try:
                logger.warning("Running notify for %s (%d)" % (n, len(slots.slots)))
                n.notify(slots)
            except Exception:
                logger.exception("Unable to run notify: %s" % n)

    while True:
        logger.info("Entering loop")
        backends = get_backends()

        for b in backends:
            run_backend(b)

        logger.info("Sleeping for %d sec" % args.interval)
        time.sleep(args.interval)

if __name__ == '__main__':
    main()