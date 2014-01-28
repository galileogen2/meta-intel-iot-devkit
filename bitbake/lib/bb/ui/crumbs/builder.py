#!/usr/bin/env python
#
# BitBake Graphical GTK User Interface
#
# Copyright (C) 2011-2012   Intel Corporation
#
# Authored by Joshua Lock <josh@linux.intel.com>
# Authored by Dongxiao Xu <dongxiao.xu@intel.com>
# Authored by Shane Wang <shane.wang@intel.com>
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
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import glib
import gtk, gobject
import copy
import os
import subprocess
import shlex
import re
import logging
import sys
import signal
import time
from bb.ui.crumbs.imageconfigurationpage import ImageConfigurationPage
from bb.ui.crumbs.recipeselectionpage import RecipeSelectionPage
from bb.ui.crumbs.packageselectionpage import PackageSelectionPage
from bb.ui.crumbs.builddetailspage import BuildDetailsPage
from bb.ui.crumbs.imagedetailspage import ImageDetailsPage
from bb.ui.crumbs.sanitycheckpage import SanityCheckPage
from bb.ui.crumbs.hobwidget import hwc, HobButton, HobAltButton
from bb.ui.crumbs.persistenttooltip import PersistentTooltip
import bb.ui.crumbs.utils
from bb.ui.crumbs.hig.crumbsmessagedialog import CrumbsMessageDialog
from bb.ui.crumbs.hig.deployimagedialog import DeployImageDialog
from bb.ui.crumbs.hig.propertydialog import PropertyDialog

hobVer = 20120808

class Configuration:
    '''Represents the data structure of configuration.'''

    @classmethod
    def parse_proxy_string(cls, proxy):
        pattern = "^\s*((http|https|ftp|socks|cvs)://)?((\S+):(\S+)@)?([^\s:]+)(:(\d+))?/?"
        match = re.search(pattern, proxy)
        if match:
            return match.group(2), match.group(4), match.group(5), match.group(6), match.group(8)
        else:
            return None, None, None, "", ""

    @classmethod
    def make_host_string(cls, prot, user, passwd, host, default_prot=""):
        if host == None or host == "":
            return ""

        passwd = passwd or ""

        if user != None and user != "":
            if prot == None or prot == "":
                prot = default_prot
            return prot + "://" + user + ":" + passwd + "@" + host
        else:
            if prot == None or prot == "":
                return host
            else:
                return prot + "://" + host

    @classmethod
    def make_port_string(cls, port):
        port = port or ""
        return port

    @classmethod
    def make_proxy_string(cls, prot, user, passwd, host, port, default_prot=""):
        if host == None or host == "":# or port == None or port == "":
            return ""

        return Configuration.make_host_string(prot, user, passwd, host, default_prot) + (":" + Configuration.make_port_string(port) if port else "")

    def __init__(self):
        self.curr_mach = ""
        self.selected_image = None
        # settings
        self.toolchain_build = True
        self.image_size = None
        self.image_packages = []
        # image/recipes/packages
        self.clear_selection()

        self.user_selected_packages = []

        self.default_task = "build"

    def clear_selection(self):
        self.selected_recipes = []
        self.selected_packages = []
        self.initial_selected_image = None
        self.initial_selected_packages = []
        self.initial_user_selected_packages = []

    def split_proxy(self, protocol, proxy):
        entry = []
        prot, user, passwd, host, port = Configuration.parse_proxy_string(proxy)
        entry.append(prot)
        entry.append(user)
        entry.append(passwd)
        entry.append(host)
        entry.append(port)
        self.proxies[protocol] = entry

    def combine_proxy(self, protocol):
        entry = self.proxies[protocol]
        return Configuration.make_proxy_string(entry[0], entry[1], entry[2], entry[3], entry[4], protocol)

    def combine_host_only(self, protocol):
        entry = self.proxies[protocol]
        return Configuration.make_host_string(entry[0], entry[1], entry[2], entry[3], protocol)

    def combine_port_only(self, protocol):
        entry = self.proxies[protocol]
        return Configuration.make_port_string(entry[4])

    def update(self, params):
        pass

    def save(self, handler, defaults=False):
        pass

    def __str__(self):
        s = "VERSION: '%s', BBLAYERS: '%s', MACHINE: '%s', DISTRO: '%s', DL_DIR: '%s'," % \
            (hobVer, " ".join(self.layers), self.curr_mach, self.curr_distro, self.dldir )
        s += "SSTATE_DIR: '%s', SSTATE_MIRROR: '%s', PARALLEL_MAKE: '-j %s', BB_NUMBER_THREADS: '%s', PACKAGE_CLASSES: '%s', " % \
            (self.sstatedir, self.sstatemirror, self.pmake, self.bbthread, " ".join(["package_" + i for i in self.curr_package_format.split()]))
        s += "IMAGE_ROOTFS_SIZE: '%s', IMAGE_EXTRA_SPACE: '%s', INCOMPATIBLE_LICENSE: '%s', SDKMACHINE: '%s', CONF_VERSION: '%s', " % \
            (self.image_rootfs_size, self.image_extra_size, self.incompat_license, self.curr_sdk_machine, self.conf_version)
        s += "LCONF_VERSION: '%s', EXTRA_SETTING: '%s', TOOLCHAIN_BUILD: '%s', IMAGE_FSTYPES: '%s', __SELECTED_IMAGE__: '%s', " % \
            (self.lconf_version, self.extra_setting, self.toolchain_build, self.image_fstypes, self.selected_image)
        s += "DEPENDS: '%s', IMAGE_INSTALL: '%s', enable_proxy: '%s', use_same_proxy: '%s', http_proxy: '%s', " % \
            (self.selected_recipes, self.user_selected_packages, self.enable_proxy, self.same_proxy, self.combine_proxy("http"))
        s += "https_proxy: '%s', ftp_proxy: '%s', all_proxy: '%s', CVS_PROXY_HOST: '%s', CVS_PROXY_PORT: '%s'" % \
            (self.combine_proxy("https"), self.combine_proxy("ftp"), self.combine_proxy("socks"),
             self.combine_host_only("cvs"), self.combine_port_only("cvs"))
        return s

class Parameters:
    '''Represents other variables like available machines, etc.'''

    def __init__(self):
        # Variables
        self.max_threads = 65535
        self.core_base = ""
        self.image_addr = ""
        self.image_types = []
        self.runnable_image_types = []
        self.runnable_machine_patterns = []
        self.deployable_image_types = []
        self.tmpdir = ""
        self.distro = ""
        self.image_list = ""

        self.all_machines = []
        self.all_package_formats = []
        self.all_distros = []
        self.all_sdk_machines = []
        self.all_layers = []
        self.image_names = []

        # for build log to show
        self.bb_version = ""
        self.target_arch = ""
        self.target_os = ""
        self.distro_version = ""
        self.tune_pkgarch = ""

    def update(self, params):
        hob_image_list = params["image_list"].split()
        self.image_list = {}
        for image in hob_image_list:
            self.image_list[image.split(":")[0]] = image.split(":")[1]
        self.image_addr = params["image_addr"]
        self.image_types = params["image_types"].split()
        self.runnable_image_types = params["runnable_image_types"].split()
        self.runnable_machine_patterns = params["runnable_machine_patterns"].split()
        self.deployable_image_types = params["deployable_image_types"].split()

def hob_conf_filter(fn, data):
    if fn.endswith("/local.conf"):
        distro = data.getVar("DISTRO_HOB")
        if distro:
            if distro != "defaultsetup":
                data.setVar("DISTRO", distro)
            else:
                data.delVar("DISTRO")

        keys = ["MACHINE_HOB", "SDKMACHINE_HOB", "PACKAGE_CLASSES_HOB", \
                "BB_NUMBER_THREADS_HOB", "PARALLEL_MAKE_HOB", "DL_DIR_HOB", \
                "SSTATE_DIR_HOB", "SSTATE_MIRRORS_HOB", "INCOMPATIBLE_LICENSE_HOB"]
        for key in keys:
            var_hob = data.getVar(key)
            if var_hob:
                data.setVar(key.split("_HOB")[0], var_hob)
        return

    if fn.endswith("/bblayers.conf"):
        layers = data.getVar("BBLAYERS_HOB")
        if layers:
            data.setVar("BBLAYERS", layers)
        return

class Builder(gtk.Window):

    (INITIAL_CHECKS,
     MACHINE_SELECTION,
     RCPPKGINFO_POPULATING,
     RCPPKGINFO_POPULATED,
     BASEIMG_SELECTED,
     RECIPE_SELECTION,
     PACKAGE_GENERATING,
     PACKAGE_GENERATED,
     PACKAGE_SELECTION,
     FAST_IMAGE_GENERATING,
     IMAGE_GENERATING,
     IMAGE_GENERATED,
     MY_IMAGE_OPENED,
     BACK,
     END_NOOP) = range(15)

    (SANITY_CHECK,
     IMAGE_CONFIGURATION,
     RECIPE_DETAILS,
     BUILD_DETAILS,
     PACKAGE_DETAILS,
     IMAGE_DETAILS,
     END_TAB) = range(7)

    __step2page__ = {
        INITIAL_CHECKS        : SANITY_CHECK,
        MACHINE_SELECTION     : IMAGE_CONFIGURATION,
        RCPPKGINFO_POPULATING : IMAGE_CONFIGURATION,
        RCPPKGINFO_POPULATED  : IMAGE_CONFIGURATION,
        BASEIMG_SELECTED      : IMAGE_CONFIGURATION,
        RECIPE_SELECTION      : RECIPE_DETAILS,
        PACKAGE_GENERATING    : BUILD_DETAILS,
        PACKAGE_GENERATED     : PACKAGE_DETAILS,
        PACKAGE_SELECTION     : PACKAGE_DETAILS,
        FAST_IMAGE_GENERATING : BUILD_DETAILS,
        IMAGE_GENERATING      : BUILD_DETAILS,
        IMAGE_GENERATED       : IMAGE_DETAILS,
        MY_IMAGE_OPENED       : IMAGE_DETAILS,
        END_NOOP              : None,
    }

    SANITY_CHECK_MIN_DISPLAY_TIME = 5

    def __init__(self, hobHandler, recipe_model, package_model):
        super(Builder, self).__init__()

        self.hob_image = "hob-image"

        # handler
        self.handler = hobHandler

        # logger
        self.logger = logging.getLogger("BitBake")
        self.current_logfile = None

        # configuration and parameters
        self.configuration = Configuration()
        self.parameters = Parameters()

        # build step
        self.current_step = None
        self.previous_step = None

        self.stopping = False

        # recipe model and package model
        self.recipe_model = recipe_model
        self.package_model = package_model

        # Indicate whether user has customized the image
        self.customized = False

        # Indicate whether the UI is working
        self.sensitive = True

        # Indicate whether the sanity check ran
        self.sanity_checked = False

        # create visual elements
        self.create_visual_elements()

        # connect the signals to functions
        self.connect("delete-event", self.destroy_window_cb)
        self.recipe_model.connect ("recipe-selection-changed",  self.recipelist_changed_cb)
        self.package_model.connect("package-selection-changed", self.packagelist_changed_cb)
        self.handler.connect("config-updated",           self.handler_config_updated_cb)
        self.handler.connect("package-formats-updated",  self.handler_package_formats_updated_cb)
        self.handler.connect("parsing-started",          self.handler_parsing_started_cb)
        self.handler.connect("parsing",                  self.handler_parsing_cb)
        self.handler.connect("parsing-completed",        self.handler_parsing_completed_cb)
        self.handler.build.connect("build-started",      self.handler_build_started_cb)
        self.handler.build.connect("build-succeeded",    self.handler_build_succeeded_cb)
        self.handler.build.connect("build-failed",       self.handler_build_failed_cb)
        self.handler.build.connect("build-aborted",      self.handler_build_aborted_cb)
        self.handler.build.connect("task-started",       self.handler_task_started_cb)
        self.handler.build.connect("disk-full",          self.handler_disk_full_cb)
        self.handler.build.connect("log-error",          self.handler_build_failure_cb)
        self.handler.build.connect("log-warning",        self.handler_build_failure_cb)
        self.handler.build.connect("log",                self.handler_build_log_cb)
        self.handler.build.connect("no-provider",        self.handler_no_provider_cb)
        self.handler.connect("generating-data",          self.handler_generating_data_cb)
        self.handler.connect("data-generated",           self.handler_data_generated_cb)
        self.handler.connect("command-succeeded",        self.handler_command_succeeded_cb)
        self.handler.connect("command-failed",           self.handler_command_failed_cb)
        self.handler.connect("sanity-failed",            self.handler_sanity_failed_cb)
        self.handler.connect("recipe-populated",         self.handler_recipe_populated_cb)
        self.handler.connect("package-populated",        self.handler_package_populated_cb)

        self.initiate_new_build_async()

        signal.signal(signal.SIGINT, self.event_handle_SIGINT)

    def create_visual_elements(self):
        self.set_title("Hob")
        self.set_icon_name("applications-development")
        self.set_resizable(True)

        window_width = 500
        window_height = 550
        self.set_size_request(window_width, window_height)

        self.vbox = gtk.VBox(False, 0)
        self.vbox.set_border_width(0)
        self.add(self.vbox)

        # create pages
        self.image_configuration_page = ImageConfigurationPage(self)
        self.recipe_details_page      = RecipeSelectionPage(self)
        self.build_details_page       = BuildDetailsPage(self)
        self.package_details_page     = PackageSelectionPage(self)
        self.image_details_page       = ImageDetailsPage(self)
        self.sanity_check_page        = SanityCheckPage(self)
        self.display_sanity_check = False
        self.sanity_check_post_func = False

        self.nb = gtk.Notebook()
        self.nb.set_show_tabs(False)
        self.nb.insert_page(self.sanity_check_page,        None, self.SANITY_CHECK)
        self.nb.insert_page(self.image_configuration_page, None, self.IMAGE_CONFIGURATION)
        self.nb.insert_page(self.recipe_details_page,      None, self.RECIPE_DETAILS)
        self.nb.insert_page(self.build_details_page,       None, self.BUILD_DETAILS)
        self.nb.insert_page(self.package_details_page,     None, self.PACKAGE_DETAILS)
        self.nb.insert_page(self.image_details_page,       None, self.IMAGE_DETAILS)
        self.vbox.pack_start(self.nb, expand=True, fill=True)

        self.show_all()
        self.nb.set_current_page(0)

    def sanity_check_timeout(self):
        # The minimum time for showing the 'sanity check' page has passe
        # If someone set the 'sanity_check_post_step' meanwhile, execute it now
        self.display_sanity_check = False
        if self.sanity_check_post_func:
          temp = self.sanity_check_post_func
          self.sanity_check_post_func = None
          temp()
        return False

    def show_sanity_check_page(self):
        # This window must stay on screen for at least 5 seconds, according to the design document
        self.nb.set_current_page(self.SANITY_CHECK)
        self.sanity_check_post_step = None
        self.display_sanity_check = True
        self.sanity_check_page.start()
        gobject.timeout_add(self.SANITY_CHECK_MIN_DISPLAY_TIME * 1000, self.sanity_check_timeout)

    def execute_after_sanity_check(self, func):
        if not self.display_sanity_check:
          func()
        else:
          self.sanity_check_post_func = func

    def generate_configuration(self):
        if not self.sanity_checked:
            self.show_sanity_check_page()
        self.handler.generate_configuration()

    def initiate_new_build_async(self):
        self.configuration.selected_image = None
        self.handler.init_cooker()
        self.generate_configuration()
        self.switch_page(self.MACHINE_SELECTION)

    def sanity_check(self):
        self.handler.trigger_sanity_check()

    def populate_recipe_package_info_async(self):
        self.configuration.curr_mach = self.handler.runCommand(["getVariable", "MACHINE"]) or "clanton"
        self.switch_page(self.RCPPKGINFO_POPULATING)
        # Parse recipes
        self.set_user_config()
        self.handler.generate_recipes()

    def generate_packages_async(self, log = False):
        self.switch_page(self.PACKAGE_GENERATING)
        # Build packages
        _, all_recipes = self.recipe_model.get_selected_recipes()
        self.set_user_config()
        self.handler.reset_build()
        self.handler.generate_packages(all_recipes, self.configuration.default_task)

    def restore_initial_selected_packages(self):
        self.package_model.set_selected_packages(self.configuration.initial_user_selected_packages, True)
        self.package_model.set_selected_packages(self.configuration.initial_selected_packages)
        for package in self.configuration.selected_packages:
            if package not in self.configuration.initial_selected_packages:
                self.package_model.exclude_item(self.package_model.find_path_for_item(package))

    def fast_generate_image_async(self, log = False):
        self.switch_page(self.FAST_IMAGE_GENERATING)
        # Build packages
        _, all_recipes = self.recipe_model.get_selected_recipes()
        self.set_user_config()
        self.handler.reset_build()
        self.handler.generate_packages(all_recipes, self.configuration.default_task)

    def generate_image_async(self, cont = False):
        self.switch_page(self.IMAGE_GENERATING)
        self.handler.reset_build()
        # Build image
        self.set_user_config()
        toolchain_packages = []
        base_image = None
        if self.configuration.selected_image == self.recipe_model.__custom_image__:
            packages = self.package_model.get_selected_packages()
            image = self.hob_image
            base_image = self.configuration.initial_selected_image
        else:
            packages = []
            image = self.configuration.selected_image
        self.handler.generate_image(image,
                                    base_image,
                                    packages,
                                    self.configuration.toolchain_build,
                                    self.configuration.default_task)

    def generate_new_image(self, image, description):
        base_image = self.configuration.initial_selected_image
        if base_image == self.recipe_model.__custom_image__:
            base_image = None
        packages = self.package_model.get_selected_packages()
        self.handler.generate_new_image(image, base_image, packages, description)

    def ensure_dir(self, directory):
        self.handler.ensure_dir(directory)

    def get_parameters_sync(self):
        return self.handler.get_parameters()

    def request_package_info_async(self):
        self.handler.request_package_info()

    def cancel_build_sync(self, force=False):
        self.handler.cancel_build(force)

    def cancel_parse_sync(self):
        self.handler.cancel_parse()

    def switch_page(self, next_step):
        # Main Workflow (Business Logic)
        self.nb.set_current_page(self.__step2page__[next_step])

        if next_step == self.MACHINE_SELECTION: # init step
            self.image_configuration_page.show_machine()

        elif next_step == self.RCPPKGINFO_POPULATING:
            # MACHINE CHANGED action or SETTINGS CHANGED
            # show the progress bar
            self.image_configuration_page.show_info_populating()

        elif next_step == self.RCPPKGINFO_POPULATED:
            self.image_configuration_page.show_info_populated()

        elif next_step == self.BASEIMG_SELECTED:
            self.image_configuration_page.show_baseimg_selected()

        elif next_step == self.RECIPE_SELECTION:
            self.recipe_details_page.set_recipe_curr_tab(self.recipe_details_page.INCLUDED)

        elif next_step == self.PACKAGE_SELECTION:
            self.configuration.initial_selected_packages = self.configuration.selected_packages
            self.configuration.initial_user_selected_packages = self.configuration.user_selected_packages
            self.package_details_page.set_title("Edit packages")
            self.package_details_page.show_page(self.current_logfile)


        elif next_step == self.PACKAGE_GENERATING or next_step == self.FAST_IMAGE_GENERATING:
            # both PACKAGE_GENERATING and FAST_IMAGE_GENERATING share the same page
            self.build_details_page.show_page(next_step)

        elif next_step == self.PACKAGE_GENERATED:
            self.package_details_page.set_title("Step 2 of 2: Edit packages")
            self.package_details_page.show_page(self.current_logfile)

        elif next_step == self.IMAGE_GENERATING:
            # after packages are generated, selected_packages need to
            # be updated in package_model per selected_image in recipe_model
            self.build_details_page.show_page(next_step)

        elif next_step == self.IMAGE_GENERATED:
            self.image_details_page.show_page(next_step)

        elif next_step == self.MY_IMAGE_OPENED:
            self.image_details_page.show_page(next_step)

        self.previous_step = self.current_step
        self.current_step = next_step

    def set_user_config(self):
        image = self.configuration.selected_image
        if image:
            if image == self.recipe_model.__custom_image__:
                image = self.configuration.initial_selected_image
            self.parameters.distro = self.parameters.image_list[image]
            self.handler.set_distro(self.parameters.distro)

    def update_recipe_model(self, selected_image, selected_recipes):
        self.recipe_model.set_selected_image(selected_image)
        self.recipe_model.set_selected_recipes(selected_recipes)

    def update_package_model(self, selected_packages, user_selected_packages=None):
        if user_selected_packages:
            left = self.package_model.set_selected_packages(user_selected_packages, True)
            self.configuration.user_selected_packages += left
        left = self.package_model.set_selected_packages(selected_packages)
        self.configuration.selected_packages += left

    def update_configuration_parameters(self, params):
        if params:
            self.configuration.update(params)
            self.parameters.update(params)

    def set_base_image(self):
        self.configuration.initial_selected_image = self.configuration.selected_image
        if self.configuration.selected_image != self.recipe_model.__custom_image__:
            self.hob_image = self.configuration.selected_image + "-edited"

    def reset(self):
        self.configuration.curr_mach = ""
        self.configuration.clear_selection()
        self.initiate_new_build_async()

    # Callback Functions
    def handler_config_updated_cb(self, handler, which, values):
        if which == "distro":
            self.parameters.all_distros = values
        elif which == "machine":
            self.parameters.all_machines = values
        elif which == "machine-sdk":
            self.parameters.all_sdk_machines = values

    def handler_package_formats_updated_cb(self, handler, formats):
        self.parameters.all_package_formats = formats

    def handler_command_succeeded_cb(self, handler, initcmd):
        if initcmd == self.handler.GENERATE_CONFIGURATION:
            if not self.configuration.curr_mach:
                self.configuration.curr_mach = self.handler.runCommand(["getVariable", "HOB_MACHINE"]) or ""
            self.update_configuration_parameters(self.get_parameters_sync())
            if not self.sanity_checked:
                self.sanity_check()
                self.sanity_checked = True
        elif initcmd == self.handler.SANITY_CHECK:
            self.execute_after_sanity_check(self.populate_recipe_package_info_async)
        elif initcmd in [self.handler.GENERATE_RECIPES,
                         self.handler.GENERATE_PACKAGES,
                         self.handler.GENERATE_IMAGE]:
            self.update_configuration_parameters(self.get_parameters_sync())
            self.request_package_info_async()
        elif initcmd == self.handler.POPULATE_PACKAGEINFO:
            if self.current_step == self.RCPPKGINFO_POPULATING:
                self.switch_page(self.RCPPKGINFO_POPULATED)
                self.rcppkglist_populated()
                return

            self.rcppkglist_populated()
            if self.current_step == self.FAST_IMAGE_GENERATING:
                self.generate_image_async(True)

    def show_error_dialog(self, msg):
        lbl = "<b>Hob found an error</b>"
        dialog = CrumbsMessageDialog(self, lbl, gtk.MESSAGE_ERROR, msg)
        button = dialog.add_button("Close", gtk.RESPONSE_OK)
        HobButton.style_button(button)
        response = dialog.run()
        dialog.destroy()

    def handler_command_failed_cb(self, handler, msg):
        if msg:
            self.show_error_dialog(msg)
        self.reset()

    def handler_sanity_failed_cb(self, handler, msg):
        self.reset()
        msg = msg.replace("your local.conf", "Settings")
        self.show_error_dialog(msg)
        self.reset()

    def window_sensitive(self, sensitive):
        self.image_configuration_page.image_combo.set_sensitive(sensitive)
        self.image_configuration_page.image_combo.child.set_sensitive(sensitive)
        self.image_configuration_page.config_build_button.set_sensitive(sensitive)

        self.recipe_details_page.set_sensitive(sensitive)
        self.package_details_page.set_sensitive(sensitive)
        self.build_details_page.set_sensitive(sensitive)
        self.image_details_page.set_sensitive(sensitive)

        if sensitive:
            self.window.set_cursor(None)
        else:
            self.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
        self.sensitive = sensitive


    def handler_generating_data_cb(self, handler):
        self.window_sensitive(False)

    def handler_data_generated_cb(self, handler):
        self.window_sensitive(True)

    def rcppkglist_populated(self):
        selected_image = self.configuration.selected_image
        selected_recipes = self.configuration.selected_recipes[:]
        selected_packages = self.configuration.selected_packages[:]
        user_selected_packages = self.configuration.user_selected_packages[:]

        if selected_image != self.recipe_model.__custom_image__:
            self.image_configuration_page.update_image_combo(selected_image)
            self.image_configuration_page.update_image_desc()
        self.update_recipe_model(selected_image, selected_recipes)
        self.update_package_model(selected_packages, user_selected_packages)

    def recipelist_changed_cb(self, recipe_model):
        self.recipe_details_page.refresh_selection()

    def packagelist_changed_cb(self, package_model):
        self.package_details_page.refresh_selection()

    def handler_recipe_populated_cb(self, handler):
        self.image_configuration_page.update_progress_bar("Populating recipes", 0.99)

    def handler_package_populated_cb(self, handler):
        self.image_configuration_page.update_progress_bar("Populating packages", 1.0)

    def handler_parsing_started_cb(self, handler, message):
        if self.current_step != self.RCPPKGINFO_POPULATING:
            return

        fraction = 0
        if message["eventname"] == "TreeDataPreparationStarted":
            fraction = 0.6 + fraction
            self.image_configuration_page.update_progress_bar("Generating dependency tree", fraction)
        else:
            self.image_configuration_page.update_progress_bar(message["title"], fraction)

    def handler_parsing_cb(self, handler, message):
        if self.current_step != self.RCPPKGINFO_POPULATING:
            return

        fraction = message["current"] * 1.0/message["total"]
        if message["eventname"] == "TreeDataPreparationProgress":
            fraction = 0.6 + 0.38 * fraction
            self.image_configuration_page.update_progress_bar("Generating dependency tree", fraction)
        else:
            fraction = 0.6 * fraction
            self.image_configuration_page.update_progress_bar(message["title"], fraction)

    def handler_parsing_completed_cb(self, handler, message):
        if self.current_step != self.RCPPKGINFO_POPULATING:
            return

        if message["eventname"] == "TreeDataPreparationCompleted":
            fraction = 0.98
        else:
            fraction = 0.6
        self.image_configuration_page.update_progress_bar("Generating dependency tree", fraction)

    def handler_build_started_cb(self, running_build):
        if self.current_step == self.FAST_IMAGE_GENERATING:
            fraction = 0
        elif self.current_step == self.IMAGE_GENERATING:
            if self.previous_step == self.FAST_IMAGE_GENERATING:
                fraction = 0.9
            else:
                fraction = 0
        elif self.current_step == self.PACKAGE_GENERATING:
            fraction = 0
        self.build_details_page.update_progress_bar("Build Started: ", fraction)

    def build_succeeded(self):
        if self.current_step == self.FAST_IMAGE_GENERATING:
            fraction = 0.9
        elif self.current_step == self.IMAGE_GENERATING:
            fraction = 1.0
            version = ""
            self.parameters.image_names = []
            selected_image = self.recipe_model.get_selected_image()
            if selected_image == self.recipe_model.__custom_image__:
                if self.configuration.initial_selected_image != selected_image:
                    version = self.recipe_model.get_custom_image_version()
                linkname = self.hob_image + version + "-" + self.configuration.curr_mach
            else:
                linkname = selected_image + '-' + self.configuration.curr_mach
            image_extension = self.get_image_extension()
            for image_type in self.parameters.image_types:
                if image_type in image_extension:
                    real_types = image_extension[image_type]
                else:
                    real_types = [image_type]
                for real_image_type in real_types:
                    linkpath = self.parameters.image_addr + '/' + linkname + '.' + real_image_type
                    if os.path.exists(linkpath):
                        self.parameters.image_names.append(os.readlink(linkpath))
        elif self.current_step == self.PACKAGE_GENERATING:
            fraction = 1.0
        self.build_details_page.update_progress_bar("Build Completed: ", fraction)
        self.handler.build_succeeded_async()
        self.stopping = False

        if self.current_step == self.PACKAGE_GENERATING:
            self.switch_page(self.PACKAGE_GENERATED)
        elif self.current_step == self.IMAGE_GENERATING:
            self.switch_page(self.IMAGE_GENERATED)

    def build_failed(self):
        if self.stopping:
            status = "stop"
            message = "Build stopped: "
            fraction = self.build_details_page.progress_bar.get_fraction()
            stop_to_next_edit = ""
            if self.current_step == self.FAST_IMAGE_GENERATING:
                stop_to_next_edit = "image configuration"
            elif self.current_step == self.IMAGE_GENERATING:
                if self.previous_step == self.FAST_IMAGE_GENERATING:
                    stop_to_next_edit = "image configuration"
                else:
                    stop_to_next_edit = "packages"
            elif self.current_step == self.PACKAGE_GENERATING:
                stop_to_next_edit = "recipes"
            button = self.build_details_page.show_stop_page(stop_to_next_edit.split(' ')[0])
            self.set_default(button)
        else:
            fail_to_next_edit = ""
            if self.current_step == self.FAST_IMAGE_GENERATING:
                fail_to_next_edit = "image configuration"
                fraction = 0.9
            elif self.current_step == self.IMAGE_GENERATING:
                if self.previous_step == self.FAST_IMAGE_GENERATING:
                    fail_to_next_edit = "image configuration"
                else:
                    fail_to_next_edit = "packages"
                fraction = 1.0
            elif self.current_step == self.PACKAGE_GENERATING:
                fail_to_next_edit = "recipes"
                fraction = 1.0
            self.build_details_page.show_fail_page(fail_to_next_edit.split(' ')[0])
            status = "fail"
            message = "Build failed: "
        self.build_details_page.update_progress_bar(message, fraction, status)
        self.build_details_page.show_back_button()
        self.build_details_page.hide_stop_button()
        self.handler.build_failed_async()
        self.stopping = False

    def handler_build_succeeded_cb(self, running_build):
        if not self.stopping:
            self.build_succeeded()
        else:
            self.build_failed()


    def handler_build_failed_cb(self, running_build):
        self.build_failed()

    def handler_build_aborted_cb(self, running_build):
        self.build_failed()

    def handler_no_provider_cb(self, running_build, msg):
        dialog = CrumbsMessageDialog(self, glib.markup_escape_text(msg), gtk.MESSAGE_INFO)
        button = dialog.add_button("Close", gtk.RESPONSE_OK)
        HobButton.style_button(button)
        dialog.run()
        dialog.destroy()
        self.build_failed()

    def handler_task_started_cb(self, running_build, message): 
        fraction = message["current"] * 1.0/message["total"]
        title = "Build packages"
        if self.current_step == self.FAST_IMAGE_GENERATING:
            if message["eventname"] == "sceneQueueTaskStarted":
                fraction = 0.27 * fraction
            elif message["eventname"] == "runQueueTaskStarted":
                fraction = 0.27 + 0.63 * fraction
        elif self.current_step == self.IMAGE_GENERATING:
            title = "Build image"
            if self.previous_step == self.FAST_IMAGE_GENERATING:
                if message["eventname"] == "sceneQueueTaskStarted":
                    fraction = 0.27 + 0.63 + 0.03 * fraction
                elif message["eventname"] == "runQueueTaskStarted":
                    fraction = 0.27 + 0.63 + 0.03 + 0.07 * fraction
            else:
                if message["eventname"] == "sceneQueueTaskStarted":
                    fraction = 0.2 * fraction
                elif message["eventname"] == "runQueueTaskStarted":
                    fraction = 0.2 + 0.8 * fraction
        elif self.current_step == self.PACKAGE_GENERATING:
            if message["eventname"] == "sceneQueueTaskStarted":
                fraction = 0.2 * fraction
            elif message["eventname"] == "runQueueTaskStarted":
                fraction = 0.2 + 0.8 * fraction
        self.build_details_page.update_progress_bar(title + ": ", fraction)

    def handler_disk_full_cb(self, running_build):
        self.disk_full = True

    def handler_build_failure_cb(self, running_build):
        pass

    def handler_build_log_cb(self, running_build, func, obj):
        if hasattr(self.logger, func):
            getattr(self.logger, func)(obj)

    def destroy_window_cb(self, widget, event):
        if not self.sensitive:
            return True
        elif self.handler.building:
            self.stop_build()
            return True
        else:
            gtk.main_quit()

    def event_handle_SIGINT(self, signal, frame):
        for w in gtk.window_list_toplevels():
            if w.get_modal():
                w.response(gtk.RESPONSE_DELETE_EVENT)
        sys.exit(0)

    def build_packages(self):
        _, all_recipes = self.recipe_model.get_selected_recipes()
        if not all_recipes:
            lbl = "<b>No selections made</b>"
            msg = "You have not made any selections"
            msg = msg + " so there isn't anything to bake at this time."
            dialog = CrumbsMessageDialog(self, lbl, gtk.MESSAGE_INFO, msg)
            button = dialog.add_button("Close", gtk.RESPONSE_OK)
            HobButton.style_button(button)
            dialog.run()
            dialog.destroy()
            return
        self.generate_packages_async(True)

    def build_image(self):
        selected_packages = self.package_model.get_selected_packages()
        if not selected_packages:      
            lbl = "<b>No selections made</b>"
            msg = "You have not made any selections"
            msg = msg + " so there isn't anything to bake at this time."
            dialog = CrumbsMessageDialog(self, lbl, gtk.MESSAGE_INFO, msg)
            button = dialog.add_button("Close", gtk.RESPONSE_OK)
            HobButton.style_button(button)
            dialog.run()
            dialog.destroy()
            return
        self.generate_image_async(True)

    def just_bake(self):
        selected_image = self.recipe_model.get_selected_image()
        selected_packages = self.package_model.get_selected_packages() or []

        # If no base image and no selected packages don't build anything
        if not (selected_packages or selected_image != self.recipe_model.__custom_image__):
            lbl = "<b>No selections made</b>"
            msg = "You have not made any selections"
            msg = msg + " so there isn't anything to bake at this time."
            dialog = CrumbsMessageDialog(self, lbl, gtk.MESSAGE_INFO, msg)
            button = dialog.add_button("Close", gtk.RESPONSE_OK)
            HobButton.style_button(button)
            dialog.run()
            dialog.destroy()
            return

        self.fast_generate_image_async(True)

    def show_recipe_property_dialog(self, properties):
        information = {}
        dialog = PropertyDialog(title = properties["name"] +' '+ "properties",
                      parent = self,
                      information = properties,
                      flags = gtk.DIALOG_DESTROY_WITH_PARENT
                          | gtk.DIALOG_NO_SEPARATOR)

        dialog.set_modal(False)

        button = dialog.add_button("Close", gtk.RESPONSE_NO)
        HobAltButton.style_button(button)
        button.connect("clicked", lambda w: dialog.destroy())

        dialog.run()

    def show_packages_property_dialog(self, properties):
        information = {}
        dialog = PropertyDialog(title = properties["name"] +' '+ "properties",
                      parent = self,
                      information = properties,
                      flags = gtk.DIALOG_DESTROY_WITH_PARENT
                          | gtk.DIALOG_NO_SEPARATOR)

        dialog.set_modal(False)

        button = dialog.add_button("Close", gtk.RESPONSE_NO)
        HobAltButton.style_button(button)
        button.connect("clicked", lambda w: dialog.destroy())

        dialog.run()

    def get_image_extension(self):
        image_extension = {}
        for type in self.parameters.image_types:
            ext = self.handler.runCommand(["getVariable", "IMAGE_EXTENSION_%s" % type])
            if ext:
                image_extension[type] = ext.split(' ')

        return image_extension

    def deploy_image(self, image_name):
        if not image_name:
            lbl = "<b>Please select an image to deploy.</b>"
            dialog = CrumbsMessageDialog(self, lbl, gtk.MESSAGE_INFO)
            button = dialog.add_button("Close", gtk.RESPONSE_OK)
            HobButton.style_button(button)
            dialog.run()
            dialog.destroy()
            return

        image_path = os.path.join(self.parameters.image_addr, image_name)
        dialog = DeployImageDialog(title = "Image Maker",
            image_path = image_path,
            parent = self,
            flags = gtk.DIALOG_MODAL
                    | gtk.DIALOG_DESTROY_WITH_PARENT
                    | gtk.DIALOG_NO_SEPARATOR)
        response = dialog.run()
        dialog.destroy()

    def show_load_kernel_dialog(self):
        dialog = gtk.FileChooserDialog("Load Kernel Files", self,
                                       gtk.FILE_CHOOSER_ACTION_SAVE)
        button = dialog.add_button("Cancel", gtk.RESPONSE_NO)
        HobAltButton.style_button(button)
        button = dialog.add_button("Open", gtk.RESPONSE_YES)
        HobButton.style_button(button)
        filter = gtk.FileFilter()
        filter.set_name("Kernel Files")
        filter.add_pattern("*.bin")
        dialog.add_filter(filter)

        dialog.set_current_folder(self.parameters.image_addr)

        response = dialog.run()
        kernel_path = ""
        if response == gtk.RESPONSE_YES:
            kernel_path = dialog.get_filename()

        dialog.destroy()

        return kernel_path

    def runqemu_image(self, image_name, kernel_name):
        if not image_name or not kernel_name:
            lbl = "<b>Please select %s to launch in QEMU.</b>" % ("a kernel" if image_name else "an image")
            dialog = CrumbsMessageDialog(self, lbl, gtk.MESSAGE_INFO)
            button = dialog.add_button("Close", gtk.RESPONSE_OK)
            HobButton.style_button(button)
            dialog.run()
            dialog.destroy()
            return

        kernel_path = os.path.join(self.parameters.image_addr, kernel_name)
        image_path = os.path.join(self.parameters.image_addr, image_name)

        source_env_path = os.path.join(self.parameters.core_base, "oe-init-build-env")
        tmp_path = self.parameters.tmpdir
        cmdline = bb.ui.crumbs.utils.which_terminal()
        if os.path.exists(image_path) and os.path.exists(kernel_path) \
           and os.path.exists(source_env_path) and os.path.exists(tmp_path) \
           and cmdline:
            cmdline += "\' bash -c \"export OE_TMPDIR=" + tmp_path + "; "
            cmdline += "source " + source_env_path + " " + os.getcwd() + "; "
            cmdline += "runqemu " + kernel_path + " " + image_path + "\"\'"
            subprocess.Popen(shlex.split(cmdline))
        else:
            lbl = "<b>Path error</b>"
            msg = "One of your paths is wrong,"
            msg = msg + " please make sure the following paths exist:\n"
            msg = msg + "image path:" + image_path + "\n"
            msg = msg + "kernel path:" + kernel_path + "\n"
            msg = msg + "source environment path:" + source_env_path + "\n"
            msg = msg + "tmp path: " + tmp_path + "."
            msg = msg + "You may be missing either xterm or vte for terminal services."
            dialog = CrumbsMessageDialog(self, lbl, gtk.MESSAGE_ERROR, msg)
            button = dialog.add_button("Close", gtk.RESPONSE_OK)
            HobButton.style_button(button)
            dialog.run()
            dialog.destroy()

    def show_packages(self):
        self.package_details_page.refresh_tables()
        self.switch_page(self.PACKAGE_SELECTION)

    def show_recipes(self):
        self.switch_page(self.RECIPE_SELECTION)

    def show_image_details(self):
        self.switch_page(self.IMAGE_GENERATED)

    def show_configuration(self):
        self.switch_page(self.BASEIMG_SELECTED)

    def stop_build(self):
        if self.stopping:
            lbl = "<b>Force Stop build?</b>"
            msg = "You've already selected Stop once,"
            msg = msg + " would you like to 'Force Stop' the build?\n\n"
            msg = msg + "This will stop the build as quickly as possible but may"
            msg = msg + " well leave your build directory in an  unusable state"
            msg = msg + " that requires manual steps to fix."
            dialog = CrumbsMessageDialog(self, lbl, gtk.MESSAGE_WARNING, msg)
            button = dialog.add_button("Cancel", gtk.RESPONSE_CANCEL)
            HobAltButton.style_button(button)
            button = dialog.add_button("Force Stop", gtk.RESPONSE_YES)
            HobButton.style_button(button)
        else:
            lbl = "<b>Stop build?</b>"
            msg = "Are you sure you want to stop this"
            msg = msg + " build?\n\n'Stop' will stop the build as soon as all in"
            msg = msg + " progress build tasks are finished. However if a"
            msg = msg + " lengthy compilation phase is in progress this may take"
            msg = msg + " some time.\n\n"
            msg = msg + "'Force Stop' will stop the build as quickly as"
            msg = msg + " possible but may well leave your build directory in an"
            msg = msg + " unusable state that requires manual steps to fix."
            dialog = CrumbsMessageDialog(self, lbl, gtk.MESSAGE_WARNING, msg)
            button = dialog.add_button("Cancel", gtk.RESPONSE_CANCEL)
            HobAltButton.style_button(button)
            button = dialog.add_button("Force stop", gtk.RESPONSE_YES)
            HobAltButton.style_button(button)
            button = dialog.add_button("Stop", gtk.RESPONSE_OK)
            HobButton.style_button(button)
        response = dialog.run()
        dialog.destroy()
        if response != gtk.RESPONSE_CANCEL:
            self.stopping = True
        if response == gtk.RESPONSE_OK:
            self.build_details_page.progress_bar.set_stop_title("Stopping the build....")
            self.build_details_page.progress_bar.set_rcstyle("stop")
            self.cancel_build_sync()
        elif response == gtk.RESPONSE_YES:
            self.cancel_build_sync(True)

    def wait(self, delay):
        time_start = time.time()
        time_end = time_start + delay
        while time_end > time.time():
            while gtk.events_pending():
                gtk.main_iteration()
