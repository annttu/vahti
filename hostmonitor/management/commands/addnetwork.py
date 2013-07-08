import socket

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from iptools import IpRange

from hostmonitor.models import Network

def resolve_dns(name):
    return set([x[4][0] for x in socket.getaddrinfo(name, 80)])


class Command(BaseCommand):
    args = '<network> <name>'
    help = 'Add the specified hosts or CIDR networks (not network/broadcast)'

    def handle(self, *args, **options):
        if len(args) == 2:
            try:
                network = args[0]
                IpRange(network)
            except:
                print("Invalid network %s" % network)
                return
            name = args[1]
 
            n = Network(name=name, network=network)
            n.save()
        else:
            self.stderr.write("Invalid usage, try --help\n")

