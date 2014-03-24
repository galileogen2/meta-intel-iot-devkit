PACKAGECONFIG[bluetooth] = "--enable-bluetooth, --disable-bluetooth, bluez5"

RDEPENDS_${PN} = "\
        dbus \
        ${@base_contains('PACKAGECONFIG', 'bluetooth', 'bluez5', '', d)} \
        ${@base_contains('PACKAGECONFIG', 'wifi','wpa-supplicant', '', d)} \
        ${@base_contains('PACKAGECONFIG', '3g','ofono', '', d)} \
        xuser-account \
        "
