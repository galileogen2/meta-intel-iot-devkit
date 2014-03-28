DESCRIPTION = "NAUI: (Not a UI) A tool to generate a webpage with useful platform information"
SECTION = "utils"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://COPYING;md5=ae9b2c90ad4abb07ea936beca1c75fce"

DEPENDS = "libxml2"

SRC_URI = "http://iotdk.intel.com/misc/${BP}.tar.bz2"

SRC_URI[md5sum] = "86295c60e1372a0bd1aabd60c1016f7f"
SRC_URI[sha256] = "8a76c924d084e076dd351f63f780aecb33b84d6ba8019722487669cd11aa0465"

inherit distutils-base update-rc.d pkgconfig cmake

do_install() {
          install -d ${D}${bindir}
          install -d ${D}${datadir}/naui/

          install -m 0755 naui ${D}${bindir}/
          install -m 0644 index.html ${D}${datadir}/naui/

if ${@base_contains('DISTRO_FEATURES','sysvinit','true','false',d)}; then
          install -d ${D}${sysconfdir}/init.d/
          install -m 0755 ${S}/script/naui ${D}${sysconfdir}/init.d/
else
          install -d ${D}${systemd_unitdir}/system
          install -m 0644 ${S}/script/naui.service ${D}${systemd_unitdir}/system/
fi
}

inherit systemd update-rc.d

INITSCRIPT_NAME = "naui"
INITSCRIPT_PARAMS = "defaults 99"

SYSTEMD_SERVICE_${PN} = "naui.service"

FILES_${PN} = "${bindir}/ \
               ${datadir}/ \
               ${systemd_unitdir}/system/ \
               ${sysconfdir}/init.d/"
