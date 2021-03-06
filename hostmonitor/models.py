from django.db import models
from django.core.validators import EMPTY_VALUES
from iptools import ipv4, ipv6, IpRange
from django.core.exceptions import ValidationError
from django.template.defaultfilters import slugify

class IPAddressField(models.GenericIPAddressField):
    __metaclass__ = models.SubfieldBase
    def to_python(self, value):
        if isinstance(value, IPAddressField):
            return value
        if '.' in value or ':' in value:
            return value
        if value in EMPTY_VALUES:
            return ''
        if value[:4] == 'ipv6':
            return ipv6.long2ip(int(value[4:]))
        else:
            return ipv4.long2ip(int(value[4:]))

    def get_prep_value(self, value):
        if ':' in value:
            return 'ipv6' + str(ipv6.ip2long(value.strip()))
        elif '.' in value:
            return 'ipv4' + str(ipv4.ip2long(value.strip()))
        return ''

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.to_python(value)


class Host(models.Model):
    ip = IPAddressField(unpack_ipv4=True, primary_key=True)
    name = models.CharField(max_length=30, editable=False, null=True)
    last_up = models.DateTimeField(null=True, editable=False)
    up_since = models.DateTimeField(null=True, editable=False)
    up = models.BooleanField(default=False, null=None, blank=None)
    monitor = models.BooleanField(default=True, null=None, blank=None)
    network = models.ForeignKey('Network')

    def __unicode__(self):
        if self.name:
            name = self.name
        else:
            name = "unknown"
        return "%s (%s)" % (self.ip, name)

    def save(self, *args, **kwargs):
        try:
            old = Host.objects.get(pk=self.pk)
        except Host.DoesNotExist:
            old = None
        super(Host, self).save(*args, **kwargs)
        if not old or old.up != self.up:
            Event.objects.create(host=self, up=self.up)

class Network(models.Model):
    slug = models.SlugField()
    network = models.CharField(max_length=256, editable=True, unique=True,
                                                    blank=False, null=False)
    name = models.CharField(max_length=30, editable=True, unique=True,
                                                    blank=False, null=False)

    def clean(self):
        try:
            IpRange(self.slug)
        except Exception as e:
            raise ValidationError("%s is not valid IP-network" % self.slug)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Network, self).save(*args, **kwargs)


    def __unicode__(self):
        return "%s" % (self.name)

class Event(models.Model):
    host = models.ForeignKey('Host', editable=False)
    time = models.DateTimeField(auto_now_add=True, editable=False)
    up = models.NullBooleanField(default=None)

    def __unicode__(self):
        return u"%s %s -> %s" % (self.time, self.host.ip, self.up)
