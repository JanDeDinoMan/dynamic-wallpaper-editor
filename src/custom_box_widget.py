from gi.repository import Gtk

# We extend the ListBox and FlowBox because,
# they don't allow an easy way of getting them all
#
# IMPORTAND: THE get_children() function doesn't guarantee the order of children!
class CustomListBox(Gtk.ListBox):

	def __init__(self, **args):
		super().__init__(**args)
		self._children = []

	def append(self, child):
		super().append(child)
		self._children.append(child)

	def remove(self, child):
		super().remove(child)
		self._children.remove(child)

	def get_children(self):
		return self._children

class CustomFlowBox(Gtk.FlowBox):

	def __init__(self, **args):
		super().__init__(**args)
		self._children = []

	def append(self, child):
		super().append(child)
		self._children.append(child)

	def remove(self, child):
		super().remove(child)
		self._children.remove(child)

	def get_children(self):
		return self._children

  
