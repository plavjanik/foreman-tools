"""Foreman Tools.

Usage:
  foreman [--url=<url>] list hosts
  foreman [--url=<url>] start host <host>
  foreman [--url=<url>] stop host <host>
  foreman (-h | --help)
  foreman --version

Options:
  -h --help     Show this screen.
  --url=<url>   Set Foreman URL (default is "https://foreman.na.intgdc.com").
  --version     Show version.

"""
from __future__ import division

import logging
import sys
import json
import math
import requests
from datetime import datetime

from docopt import docopt
from humanfriendly import format_timespan
from humanfriendly.terminal import ansi_wrap
from requests.packages import urllib3
from requests_kerberos import HTTPKerberosAuth, OPTIONAL

import foreman_tools

DEFAULT_URL = "https://foreman.na.intgdc.com"


class ForemanError(Exception):
    def __init__(self, response, *args, **kwargs):
        super(ForemanError, self).__init__(*args, **kwargs)
        self.response = response


class ForemanSession(requests.Session):
    def __init__(self, foreman_url):
        super(ForemanSession, self).__init__()
        auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
        self.auth = auth
        self.verify = False
        self.headers.update({
            'Accept': 'application/json; version=2',
            'Content-Type': 'application/json',
        })
        self.base_url = foreman_url

    # noinspection PyMethodMayBeStatic
    def _json_response(self, response):
        if response.status_code != 200:
            raise ForemanError("Failed request", response=response)
        return json.loads(response.text)

    def get_all(self, resource, data=None):
        """Joins paged results into one generator. The response must contains following fields: `total`, `per_page`,
        and `results`. It returns a tuple with total count of results and a generator object that yields results.
        """
        url = self.foreman_url(resource)
        data = data or {"page": 1}
        request_response = self.get(url, data=json.dumps(data), verify=self.verify)
        first_response = self._json_response(request_response)

        total = first_response["total"]
        per_page = first_response["per_page"]

        def hosts_generator():
            for item in first_response["results"]:
                yield item
            for page_number in range(2, int(math.ceil(total / per_page))):
                data["page"] = page_number
                response = self._json_response(self.get(url, data=json.dumps(data), verify=self.verify))
                for item in response["results"]:
                    yield item

        return total, hosts_generator()

    def foreman_url(self, resource):
        return "%s/api/v2/%s" % (self.base_url, resource)

    def power(self, host, action):
        """Run a power operation on host. Valid actions are (on/start), (off/stop), (soft/reboot), (cycle/reset),
        (state/status).

        https://www.theforeman.org/api/1.14/apidoc/v2/hosts/power.html
        """
        response = self.put(self.foreman_url("hosts/%s/power" % host), data=json.dumps({"power_action": action}))
        print(response.text)


def main(argv=None):
    """Command line interface ``foreman`` for Foreman.

    :param argv: Override system arguments (sys.argv[1:]).
    """
    argv = argv or sys.argv[1:]
    args = docopt(__doc__, version="Foreman Tools %s" % foreman_tools.__version__, argv=argv)

    logging.basicConfig(level=logging.INFO)
    urllib3.disable_warnings()

    foreman_url = args["--url"] or DEFAULT_URL
    fs = ForemanSession(foreman_url=foreman_url)

    if args["list"] and args["hosts"]:
        # https://www.theforeman.org/api/1.14/apidoc/v2/hosts.html#description-index
        count, hosts = fs.get_all("hosts")
        for host in hosts:
            last_report = datetime.strptime(host["last_report"], "%Y-%m-%dT%H:%M:%SZ")
            last_report_age = (datetime.utcnow() - last_report).total_seconds()
            if last_report_age <= 60 * 60:
                age_color = "green"
            elif last_report_age <= 2 * 60 * 60:
                age_color = "yellow"
            else:
                age_color = "red"
            print("%-40s %-15s %-10s" % (host["name"],
                                         host["ip"],
                                         ansi_wrap(format_timespan(last_report_age), color=age_color)))

    elif args["start"] and args["<host>"]:
        fs.power(args["<host>"], "start")

    elif args["stop"] and args["<host>"]:
        fs.power(args["<host>"], "stop")


if __name__ == "__main__":
    main()
