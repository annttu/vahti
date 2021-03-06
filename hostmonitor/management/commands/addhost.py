import socket
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from iptools import ipv4, ipv6, IpRange

from hostmonitor.models import Host, Network


def resolve_dns(name):
    return set([x[4][0] for x in socket.getaddrinfo(name, 80)])


class Command(BaseCommand):
    args = '<target target ...>'
    help = 'Add the specified hosts or CIDR networks (not network/broadcast)'
    option_list = BaseCommand.option_list + (
        make_option('-n', '--network', dest="network"),
        )

    def add_host(self, ip, network):
        h = Host(ip=ip, network=network)
        self.stdout.write("%s adding\n" % ip)
        try:
            h.save()
        except IntegrityError, e:
            self.stderr.write("%s ERROR %s\n" % (ip, e))

    def handle(self, *args, **options):
        try:
            net = Network.objects.get(slug=options['network'])
        except Network.DoesNotExist, e:
            try:
                net = Network.objects.get(name=options['network'])
            except Network.DoesNotExist, e:
                print("Network %s not found, try ./manage.py addnetwork <network>")
                return
        for target in args:
            if ipv6.validate_ip(target) or ipv4.validate_ip(target):
                self.add_host(target, net)
            elif ipv6.validate_cidr(target) or ipv6.validate_cidr(target):
                hosts = list(IpRange(target))
                print hosts
                for host in hosts[1:-1]:
                    self.add_host(host, net)
            else:
                hosts = resolve_dns(target)
                for host in hosts:
                    self.add_host(host, net)

