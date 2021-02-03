# COVID-19 Vaccine Tracker

<img src="img/slack-msg.png" width=400 />

This is a basic Python project which allows for curation of vaccine sign-up _backends_, as well as _notifiers_, and runs a rudimentary check of each backend at a specified interval and, if there are doses available, alerts via the configured notifiers.

Please be a good citizen by ensuring those who need the vaccine are able to get it first.

Currently, the following services are supported:
* Curative (curative.com/sites/<location_id>)
* RxTouch (<location_id>.rxtouch.com/covid19/Patient/Advisory)
* CVS Pharmacy (cvs.com/vaccine/intake/store/cvd-schedule)
* MAImmunizations (maimmunizations.org)

The following notifiers are supported:
* Console (to stdout, for debugging)
* Slack

Currently a work-in-progress.

## Setup

Rename `config.py.example` to `config.py` and tweak its parameters (e.g., ZIP code, location radius, etc).

Then, run `pipenv run python3 main.py` to run the application using Pipenv.
For verbose logging, add `-v`.
To adjust the check interval, specify `-i <seconds>`.

See `--help` for more options.
