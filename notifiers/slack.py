import requests
import json
import logging
import arrow

from . import Notifier

logger = logging.getLogger(__name__)

class SlackNotifier(Notifier):
    ICON_URL = 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/SARS-CoV-2_without_background.png/220px-SARS-CoV-2_without_background.png'

    def __init__(self, slack_token, slack_channel, slack_username, ignore_dates_before=None, min_open_slots=0):
        self.slack_token = slack_token
        self.slack_channel = slack_channel
        self.slack_username = slack_username
        self.ignore_dates_before = ignore_dates_before
        self.min_open_slots = min_open_slots

    def process_slots(self, slots):
        if self.ignore_dates_before:
            new_slots = slots.empty_copy()
            ok = False
            for i in range(len(slots.slots)):
                struct = slots.slots_struct[i]
                if arrow.get(struct.date) >= arrow.get(self.ignore_dates_before):
                    ok = True
                    new_slots.add_slot(slots.slots[i], struct=struct)

            return ok, new_slots
        else:
            return True, slots

    def notify(self, orig_slots):
        ok, slots = self.process_slots(orig_slots)
        if not ok:
            logger.info("Ignoring notify due to config: %s" % orig_slots)
            return

        base_count = len(slots.slots)
        count = 0
        for s in slots.slots_struct:
            if s and s.count:
                count += s.count
        if count == 0:
            count = base_count

        if count < self.min_open_slots:
            logger.info("Ignoring notify due to only %d slots available (required %d)" % (count, self.min_open_slots))
            return

        text = "%d Vaccination appointment%s found for *%s*:" % (count, "s" if count > 1 else "", slots.location)
        sections = [text, {"type": "divider"}] + ["%s" % s for s in slots.slots] + [self.slack_action_block(("Visit Site", slots.url))]
        blocks = self.slack_markdown_blocks(*sections)
        logger.info("Sending notification: %s" % blocks)
        post = self.slack_post("%s %s" % (text, " ".join([s for s in slots.slots])), blocks)
        is_ok = post.get('ok', False)
        if not is_ok:
            logger.error("Problem querying slack API: %s Excluding blocks" % post)
            post = self.slack_post("%s %s" % (text, " ".join([s for s in slots.slots])))
            logger.warning(post)
        else:
            logger.info("Successfully posted to Slack API: %s" % post)


    def notify_problem(self, message):
        logger.warning(self.slack_post(message))

    def slack_markdown_blocks(self, *args):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": t
                }
            } if type(t) == str else t for t in args
        ]

    def slack_action_block(self, *args):
        return {
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": text
					},
					"value": text,
                    "url": url
				} for (text, url) in args
			]
		}


    def slack_post(self, text, blocks=None):
        return requests.post('https://slack.com/api/chat.postMessage', {
            'token': self.slack_token,
            'channel': self.slack_channel,
            'text': text,
            'icon_url': self.ICON_URL,
            'username': self.slack_username,
            'blocks': json.dumps(blocks) if blocks else None
        }).json()