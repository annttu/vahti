# encoding: utf-8
from datetime import datetime
from pytz import timezone
import sys
from subprocess import Popen, PIPE
from time import sleep
from optparse import make_option
import socket
from iptools import IpRange
from django.conf import settings

from django.core.management.base import BaseCommand, CommandError

from hostmonitor.models import Host, Network, IPAddressField

FPING = 'fping'
FPING6 = 'fping6'

def _fping_hosts(fping, hosts):
    if not hosts:
        return([], [])
    args = [fping] + hosts
    p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (fping_out, fping_err) = p.communicate()
    out_lines = fping_out.split("\n")
    err_lines = fping_err.split("\n")
    up = [x.split(" ",1)[0] for x in out_lines if ' is alive' in x]
    down = [x.split(" ",1)[0] for x in out_lines if ' is unreachable' in x]
    return (up, down)

def ping_hosts(hosts):
    v6 = []
    v4 = []
    for address in hosts:
        if ':' in address:
            v6.append(address)
        else:
            v4.append(address)
    v6_up, v6_down = _fping_hosts(FPING6, v6)
    v4_up, v4_down = _fping_hosts(FPING, v4)
    return (set(v6_up + v4_up), set(v6_down + v4_down))

def dns_lookup(hosts):
    if hasattr(socket, 'setdefaulttimeout'):
        # Set the default timeout on sockets to 5 seconds
        socket.setdefaulttimeout(5)
    names = []
    for ip in hosts:
        try:
            names.append(socket.gethostbyaddr(ip)[0])
        except (socket.herror, socket.gaierror):
            print ip
            names.append(None)
    return dict(zip(hosts, names))

class Command(BaseCommand):
    args = ''
    help = 'Add the specified hosts or CIDR networks (not network/broadcast)'
    option_list = BaseCommand.option_list + (
        make_option('--loop', action="store_true", dest="loop"),
        )

    def handle(self, *args, **options):
        if len(args) > 0:
            self.stderr.write("This command does not take arguments\n")
            return
        while True:
            self.ping_once()
            if not options['loop']:
                break
            sleep(3600)

    def ping_once(self):
        hosts = []
        for network in Network.objects.all():
            try:
                addresses = list(IpRange(str(network.network)))
            except TypeError:
                sys.stderr.write("Invalid network %s\n" % network)
                continue
            # check if network is /31 or /32
            if len(addresses) > 2:
                addresses = addresses[1:-1]
            for ip in addresses:
                try:
                    host = Host.objects.get(ip=ip)
                except Host.DoesNotExist:
                    host = Host(ip=ip, network=network)
                    try:
                        host.save()
                    except IntegrityError, e:
                        self.stderr.write("%s ERROR %s\n" % (ip, e))
                        continue
                hosts.append(host.ip)
        self.stdout.write("Pinging all monitored hosts on network %s\n" % network)
        (up, down) = ping_hosts(hosts)
        self.stdout.write("Resolving DNS names\n")
        names = dns_lookup(hosts)
        for ip in up:
            self.stdout.write("%s up\n" % ip)
            h = Host.objects.get(ip=ip)
            h.name = names[ip]
            h.up = True
            h.last_up = datetime.now(tz=timezone(settings.TIME_ZONE))
            if not h.up_since:
                h.up_since = datetime.now(tz=timezone(settings.TIME_ZONE))
            h.save()
        for ip in down:
            self.stdout.write("%s down\n" % ip)
            h = Host.objects.get(ip=ip)
            h.name = names[ip]
            h.up = False
            h.up_since = None
            h.save()
