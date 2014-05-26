require recipes-connectivity/ofono/ofono.inc

S	= "${WORKDIR}/git"
SRCREV	= "516165c3114471400b4551ff9b04ff9ca7c1fc25"
PV	= "1.14+git${SRCPV}"

SRC_URI = "\
	git://git.kernel.org/pub/scm/network/ofono/ofono.git;protocol=git \
	file://ofono \
"

# We want to use bluez5
DEPENDS := "${@oe_filter_out('bluez4', '${DEPENDS}', d)}"
DEPENDS += "${@base_contains('DISTRO_FEATURES', 'bluetooth','bluez5', '', d)}"

# Test scripts use python3, the dbus module is still missing so the scripts
# do not work as expected.
RDEPENDS_${PN} = "\
	python3 \
	python3-codecs \
	python3-math \
	python3-io \
	python3-misc \
"

do_install_append() {
	# Because python3-dbus module is currently not there, just use
	# python 2.x in the ofono test scripts
	for PYTHSCRIPT in `grep -rIl ${bindir}/python3 ${D}${libdir}/${PN}`; do
		sed -i -e '1s|^#!.*|#!/usr/bin/env python|' $PYTHSCRIPT
	done
}
