SUMMARY = "Initialization service for ConnMan"
DESCRIPTION = "Initializes necessary ConnMan services. This is \
needed in headless system, otherwise we might not be able to \
connect to device after installation. This service is only run \
once in the first boot.\
"
LICENSE  = "GPLv2"
LIC_FILES_CHKSUM = "file://connman-init-settings.sh;beginline=7;endline=18;md5=95c5d66479370ef3964c4aef9255476f"

SRC_URI = "\
	file://connman-init-settings.sh \
	file://connman-init.service \
"

S = "${WORKDIR}"
PR = "r0"

inherit systemd

SYSTEMD_PACKAGES = "connman-init-systemd"

SYSTEMD_SERVICE_${PN} = " connman-init.service"

FILES_${PN} = " connman-init.service \
		${libdir}/connman/connman-init-settings.sh"

do_install() {
	install -d ${D}${libdir}/connman
	install -d ${D}${nonarch_base_libdir}/systemd/system
	install -m 0755 ${WORKDIR}/connman-init-settings.sh ${D}${libdir}/connman
	install -m 0755 ${WORKDIR}/connman-init.service ${D}${nonarch_base_libdir}/systemd/system
}
