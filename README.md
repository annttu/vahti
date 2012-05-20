# Vahti #

Host/IP address pool monitoring daemon and visualization.

## Idea ##

The idea is to monitor used/unused pool of IP addresses. If the address
becomes used, it will be recorded. The tool will list hosts and their
DNS names and record changes.

## Requirements ##

The following tools are required.

 * Foreman (only for starting processes)
 * sqlite3 (for development database)

Additionally some Python libs need to be installed  with pip into a virtualenv
environment.

## Usage ##

    $ mkvirtualenv vahti --no-site-packages
    $ workon vahti
    (vahti) $ pip install -r requirements.txt 
    (vahti) $ foreman start

Alternatively, the system can be started without foreman:

    (vahti) $ ./manage.py pinghosts --loop &
    (vahti) $ ./manage.py runserver &    

![Vahti screenshot](http://joneskoo.kapsi.fi/tmp/vahti.png)