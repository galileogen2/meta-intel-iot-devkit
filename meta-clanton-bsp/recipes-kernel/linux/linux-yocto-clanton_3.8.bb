inherit kernel
require recipes-kernel/linux/linux-yocto.inc

# Override SRC_URI in a bbappend file to point at a different source
# tree if you do not want to build from Linus' tree.

SRC_URI = "git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git;branch=linux-3.8.y"

SRC_URI += "file://clanton.cfg"
SRC_URI += "file://clanton-standard.scc"
SRC_URI += "file://0001-libtraceevent-Remove-hard-coded-include-to-usr-local.patch"
SRC_URI += "file://0001-tty-don-t-deadlock-while-flushing-workqueue-quark.patch"
SRC_URI += "file://0002-driver-core-constify-data-for-class_find_devic-quark.patch"
SRC_URI += "file://0003-TTY-mark-tty_get_device-call-with-the-proper-c-quark.patch"
SRC_URI += "file://0004-pwm-Add-sysfs-interface-quark.patch"
SRC_URI += "file://0005-drivers-pwm-sysfs.c-add-export.h-RTC-50404-quark.patch"
SRC_URI += "file://0006-core-Quark-patch-quark.patch"
SRC_URI += "file://0007-Quark-Platform-Code-quark.patch"
SRC_URI += "file://0008-Quark-UART-quark.patch"
SRC_URI += "file://0009-EFI-capsule-update-quark.patch"
SRC_URI += "file://0010-Quark-SDIO-host-controller-quark.patch"
SRC_URI += "file://0011-Quark-USB-host-quark.patch"
SRC_URI += "file://0012-USB-gadget-serial-quark.patch"
SRC_URI += "file://0013-Quark-stmmac-Ethernet-quark.patch"
SRC_URI += "file://0014-Quark-GPIO-2-2-quark.patch"
SRC_URI += "file://0015-Quark-GPIO-1-2-quark.patch"
SRC_URI += "file://0016-Quark-GIP-Cypress-I-O-expander-quark.patch"
SRC_URI += "file://0017-Quark-I2C-quark.patch"
SRC_URI += "file://0018-Quark-sensors-quark.patch"
SRC_URI += "file://0019-Quark-SC-SPI-quark.patch"
SRC_URI += "file://0020-Quark-IIO-quark.patch"
SRC_URI += "file://0021-Quark-SPI-flash-quark.patch"

LINUX_VERSION ?= "3.8"
LINUX_VERSION_EXTENSION ?= "-clanton"

# Override SRCREV to point to a different commit in a bbappend file to
# build a different release of the Linux kernel.
SRCREV = "531ec28f9f26f78797124b9efcf2138b89794a1e"
SRCREV_machine_clanton = "531ec28f9f26f78797124b9efcf2138b89794a1e"

PR = "r0"
PV = "${LINUX_VERSION}"

# Override COMPATIBLE_MACHINE to include your machine in a bbappend
# file. Leaving it empty here ensures an early explicit build failure.
COMPATIBLE_MACHINE = "clanton"

RDEPENDS_kernel-base=""
