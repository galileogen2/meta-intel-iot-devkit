#!/bin/sh
#
# Connection Manager Init Service
#
# Copyright (C) 2012  Intel Corporation. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


CONNMAN_DIR=/var/lib/connman
CONNMAN_SETTINGS=$CONNMAN_DIR/settings

if [ -s $CONNMAN_SETTINGS ]; then
    exit 0
fi

if [ ! -d $CONNMAN_DIR ]; then
    mkdir -p $CONNMAN_DIR
fi

TETHERING="$1"
TETHERING_AP_PASSPHRASE="$2"
TETHERING_AP_SSID="$3"

if [ -z "$TETHERING" ]; then
    TETHERING="true"
fi

# Create main.conf with those values that we need
MAINCONF=/etc/connman/main.conf
cat > $MAINCONF <<EOF
[General]
TetheringTechnologies=wifi,bluetooth,gadget,ethernet
PersistentTetheringMode=true
EOF

function get_mac
{
    # Get the mac address of the first network interface returned by kernel
    IFACE=`head -n 3 /proc/net/dev|tail -n 1|awk '{ print $1 }'|sed 's/://'`
    if [ -z "$IFACE" -o ! -d /sys/class/net/$IFACE ]; then
	echo 010203040506
    else
	sed 's/://g' /sys/class/net/$IFACE/address
    fi
}

if [ -z "$TETHERING_AP_SSID" ]; then
    MAC=`get_mac`
    TETHERING_AP_SSID=eca-$MAC
fi

if [ -z "$TETHERING_AP_PASSPHRASE" ]; then
    if [ -z "$MAC" ]; then
	MAC=`get_mac`
    fi
    TETHERING_AP_PASSPHRASE=$MAC
fi

cat > $CONNMAN_SETTINGS <<EOF
[global]
OfflineMode=false

[Bluetooth]
Enable=true

[Cellular]
Enable=true

[WiFi]
Enable=true
Tethering=$TETHERING
Tethering.Identifier=$TETHERING_AP_SSID
Tethering.Passphrase=$TETHERING_AP_PASSPHRASE


[Wired]
Enable=true
EOF

if [ $? -eq 0 -a -f $CONNMAN_SETTINGS ]; then
    chmod 0600 $CONNMAN_SETTINGS
fi

exit 0
