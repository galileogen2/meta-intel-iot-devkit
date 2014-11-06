module_autoload_iwlwifi_iot-devkit = "iwlwifi"
module_autoload_btusb = "btusb"

# swap g_serial for g_acm_ms
module_autoload_pch_udc = " pch_udc g_acm_ms"
module_conf_g_acm_ms = "options g_acm_ms file=/dev/mmcblk0p1 removable=1 idVendor=0x8086 idProduct=0xDEAD"

# PPP module autoload
module_autoload_pppox = "pppox"
module_autoload_pppoe = "pppoe"

# find defconfig path
FILESEXTRAPATHS := "${THISDIR}/${PN}"

SRC_URI += "file://devkitcamera.cfg"
SRC_URI += "file://enable_systemd.cfg"
SRC_URI += "file://enable_mmc.cfg"
SRC_URI += "file://fuse.cfg"
SRC_URI += "file://bridge.cfg"
SRC_URI += "file://netfilter-small-3.8.cfg"
SRC_URI += "file://nfacct.cfg"
SRC_URI += "file://ipv6.cfg"
SRC_URI += "file://nfc.cfg"
SRC_URI += "file://mac80211.cfg"
SRC_URI += "file://rfkill.cfg"
SRC_URI += "file://l2tp.cfg"
SRC_URI += "file://tun-device.cfg"
SRC_URI += "file://usb-serial.cfg"
SRC_URI += "file://nokia-phonet.cfg"
SRC_URI += "file://bluetooth.cfg"
SRC_URI += "file://wlan-intel.cfg"
SRC_URI += "file://wlan-ti.cfg"
SRC_URI += "file://wlan-marwel.cfg"
SRC_URI += "file://wlan-zydas.cfg"
SRC_URI += "file://wlan-broadcom.cfg"
SRC_URI += "file://wlan-realtek.cfg"
SRC_URI += "file://wlan-ralink.cfg"
SRC_URI += "file://wlan-atheros.cfg"
SRC_URI += "file://g_acm_ms.cfg"
SRC_URI += "file://netfilter_redirect.cfg"
SRC_URI += "file://ppp.cfg"
SRC_URI += "file://ftdi_sio.cfg"
SRC_URI += "file://usb_serial.cfg"
