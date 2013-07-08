from datetime import datetime
from subprocess import Popen, PIPE
from time import sleep
from optparse import make_option
import socket

from django.core.management.base import BaseCommand, CommandError

from hostmonitor.models import Host

FPING = 'fping'

def ping_hosts(hosts):
    args = [FPING] + hosts
    p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    (fping_out, fping_err) = p.communicate()
    out_lines = fping_out.split("\n")
    err_lines = fping_err.split("\n")
    up = [x.split(" ",1)[0] for x in out_lines if ' is alive' in x]
    down = [x.split(" ",1)[0] for x in out_lines if ' is unreachable' in x]
    #down += [x.split(" ",1)[0] for x in err_lines]
    return (set(up), set(down))

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
        for host in Host.objects.filter(monitor=True):
            hosts.append(host.ip)
        self.stdout.write("Pinging all monitored hosts\n")
        (up, down) = ping_hosts(hosts)
        self.stdout.write("Resolving DNS names\n")
        names = dns_lookup(hosts)
        for ip in up:
            self.stdout.write("%s up\n" % ip)
            h = Host.objects.get(ip=ip)
            h.name = names[ip]
            h.up = True
            h.last_up = datetime.now()
            if not h.up_since:
                h.up_since = datetime.now()
            h.save()
        for ip in down:
            self.stdout.write("%s down\n" % ip)
            h = Host.objects.get(ip=ip)
            h.name = names[ip]
            h.up = False
            h.up_since = None
            h.save()
