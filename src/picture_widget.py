# picture_widget.py
#
# Copyright 2018-2021 Romain F. T.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, GdkPixbuf, Pango, Gdk, GLib
import math

from .misc import time_to_string
from .misc import get_hms

UI_PATH = '/com/github/maoschanz/DynamicWallpaperEditor/ui/'

class DWEPictureWidget(Gtk.Box):

	def __init__(self, pic_structure, window):
		super().__init__()
		self.pic_id = pic_structure['pic_id']
		self.filename = pic_structure['path']
		self.indx = pic_structure['index']
		self.window = window
		self._static_time_lock = False
		self._transition_time_lock = False

	def build_ui(self, stt, trt, template, w, h):
		print("temlate: ", template)
		builder = Gtk.Builder().new_from_resource(UI_PATH + template)
		pic_box = builder.get_object("pic_box")
		self.time_box = builder.get_object('time_box')

		# Thumbnail
		self.image = builder.get_object('pic_thumbnail')
		# self.generate_thumbnail() will be called later by self.update_for_current_file

		# File name
		self.label_widget = builder.get_object('pic_label')
		self.label_widget.set_ellipsize(Pango.EllipsizeMode.START)
		GLib.timeout_add(500, self.update_for_current_file, {})

		# Schedule labels
		self.static_label = builder.get_object('static_label')
		self.static_label.set_ellipsize(Pango.EllipsizeMode.START)
		self.transition_label = builder.get_object('transition_label')
		self.transition_label.set_ellipsize(Pango.EllipsizeMode.START)

		# Pic controls
		delete_btn = builder.get_object('delete_btn')
		delete_btn.connect('clicked', self.destroy_pic)
		self.menu_btn = builder.get_object('menu_btn')
		builder.add_from_resource(UI_PATH + 'picture_menu.ui')
		self.menu_btn.set_menu_model( builder.get_object('pic-menu') )

		# Picture durations
		self.static_time_btn = builder.get_object('static_btn')
		self.trans_time_btn = builder.get_object('transition_btn')
		self.static_time_btn.set_value(float(stt))
		self.trans_time_btn.set_value(float(trt))
		self.static_time_btn.connect('value-changed', self.on_static_changed)
		self.trans_time_btn.connect('value-changed', self.on_transition_changed)

		#TODO FIX Drag and drop
		# Ability to be dragged
		# pic_box.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, None, Gdk.DragAction.MOVE)
		# pic_box.connect('drag-data-get', self.on_drag_data_get)
		# pic_box.drag_source_add_text_targets()

		# Ability to receive drop
		# self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.MOVE)
		# self.connect('drag-data-received', self.on_drag_data_received)
		# self.drag_dest_add_text_targets()
		print("Picbox:", pic_box)
		self.append(pic_box)
		return builder

	def end_build_ui(self):
		#TODO CHECK IF NESS
		# self.show_all()
		is_global = self.window.lookup_action('same_duration').get_state()
		is_daylight = self.window.lookup_action('total_24').get_state()
		self.update_to_type(is_global, is_daylight)

	############################################################################

	def on_drag_data_get(self, widget, drag_context, data, info, time):
		data.set_text(str(self.indx), -1)

	def on_drag_data_received(self, widget, drag_context, x, y, data, info, time):
		index_from = int(data.get_text())
		self.window.view.move_pic(index_from, self.indx)

	############################################################################

	def update_to_type(self, is_global, is_daylight):
		self.time_box.set_visible(not is_global)
		self.static_label.set_visible(is_daylight)
		self.transition_label.set_visible(is_daylight)

	############################################################################

	def replace(self, searched_str, new_str):
		self.filename = self.filename.replace(searched_str, new_str)
		self.update_for_current_file()

	def update_for_current_file(self, content_params={}):
		self.label_widget.set_label(self.filename)
		# the concrete classes will call generate_thumbnail themselves
		return False

	def generate_thumbnail(self, w, h):
		self.time_box.set_sensitive(True)
		try:
			# This size is totally arbitrary.
			pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(self.filename, w, h, True)
			self.image.set_from_pixbuf(pixbuf)
		except Exception:
			if self.filename[:6] != '/home/':
				self.image.set_from_icon_name('face-uncertain-symbolic', Gtk.IconSize.DIALOG)
				self.set_tooltip_text(_("This picture might exist, but " + \
				             "it isn't in your home folder so I can't see it."))
			else:
				self.image.set_from_icon_name('dialog-error-symbolic', Gtk.IconSize.DIALOG)
				self.set_tooltip_text(_("This picture doesn't exist"))
				self.time_box.set_sensitive(False)

	############################################################################

	def set_new_static(self, new_static):
		if self.static_time_btn.get_value() != new_static:
			self.static_time_btn.set_value(new_static)

	def on_static_changed(self, *args):
		if not self._static_time_lock:
			GLib.timeout_add(500, self._trigger_static_operation, {})
		self._static_time_lock = True

	def _trigger_static_operation(self, *args):
		self._static_time_lock = False

		time = self.static_time_btn.get_value()
		self.static_time_btn.set_tooltip_text(time_to_string(time))
		operation = {
			'type': 'edit',
			'pic_id': self.pic_id,
			'static': time,
		}
		self.window._data_model.do_operation(operation)

	### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ###

	def set_new_transition(self, new_transition):
		if self.trans_time_btn.get_value() != new_transition:
			self.trans_time_btn.set_value(new_transition)

	def on_transition_changed(self, *args):
		if not self._transition_time_lock:
			GLib.timeout_add(500, self._trigger_transition_operation, {})
		self._transition_time_lock = True

	def _trigger_transition_operation(self, *args):
		self._transition_time_lock = False

		time = self.trans_time_btn.get_value()
		self.trans_time_btn.set_tooltip_text(time_to_string(time))
		operation = {
			'type': 'edit',
			'pic_id': self.pic_id,
			'transition': time,
		}
		self.window._data_model.do_operation(operation)

	############################################################################

	def update_static_label(self, prev):
		msg = _("This picture lasts from {0} to {1}")
		msg, new_end = self.update_label_common(prev, self.static_time_btn, msg)
		self.static_label.set_label(msg)
		return new_end

	def update_transition_label(self, prev):
		msg = _("The transition to the next picture lasts from {0} to {1}")
		msg, new_end = self.update_label_common(prev, self.trans_time_btn, msg)
		self.transition_label.set_label(msg)
		return new_end

	def update_label_common(self, prev, btn, msg):
		if btn.get_value() == 0:
			return "", prev

		# Calculate the next time available
		hours, mins, seconds = get_hms(btn.get_value())
		total = ((prev[0] + hours) * 60 + prev[1] + mins) * 60 + prev[2] + seconds
		h, m, s = get_hms(total)
		new_end = [h % 24, m, s]

		# Create strings that show time
		start_time = ':'.join([str(time) if time > 9 else "0" + str(time) for time in prev])
		end_time = ':'.join([str(time) if time > 9 else "0" + str(time) for time in new_end])
		return msg.format(start_time, end_time), new_end

	############################################################################

	def destroy_pic(self, *args):
		operation = {
			'type': 'delete',
			'pic_id': self.pic_id,
		}
		self.window._data_model.do_operation(operation)

	############################################################################
################################################################################

class DWEPictureRow(DWEPictureWidget):
	__gtype_name__ = 'DWEPictureRow'

	def __init__(self, pic_structure, window):
		super().__init__(pic_structure, window)
		stt = pic_structure['static']
		trt = pic_structure['transition']
		builder = self.build_ui(stt, trt, 'picture_row.ui', 114, 64)
		# ... ?
		self.end_build_ui()

	def update_for_current_file(self, content_params={}):
		super().update_for_current_file()
		self.generate_thumbnail(114, 64)
		return False

	############################################################################
################################################################################

class DWEPictureThumbnail(DWEPictureWidget):
	__gtype_name__ = 'DWEPictureThumbnail'

	def __init__(self, pic_structure, window):
		super().__init__(pic_structure, window)
		stt = pic_structure['static']
		trt = pic_structure['transition']
		builder = self.build_ui(stt, trt, 'picture_thumbnail.ui', 250, 140)

		builder.get_object('time_popover').popdown()
		self.alt_label = builder.get_object('alt_label')
		self.alt_label.set_label("…" + self.filename[-20:])
		self.alt_label.set_ellipsize(Pango.EllipsizeMode.START)
		self.time_btn = builder.get_object('time_btn')

		self.end_build_ui()

	def update_to_type(self, is_global, is_daylight):
		super().update_to_type(is_global, is_daylight)
		self.alt_label.set_visible(is_global)
		self.time_btn.set_visible(not is_global)

	def update_for_current_file(self, content_params={}):
		super().update_for_current_file()
		self.generate_thumbnail(250, 140)
		return False

	def update_static_label(self, prev):
		new_end = super().update_static_label(prev)
		label = self.static_label.get_label()
		label += "\n" + self.transition_label.get_label()
		self.time_btn.set_tooltip_text(label)
		return new_end

	def update_transition_label(self, prev):
		new_end = super().update_transition_label(prev)
		label = self.static_label.get_label()
		label += "\n" + self.transition_label.get_label()
		self.time_btn.set_tooltip_text(label)
		return new_end

	############################################################################
################################################################################

