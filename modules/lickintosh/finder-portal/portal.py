"""Lazy native Finder delegate; never starts a GUI backend during portal startup."""
from gi.repository import Gio, GLib

IFACE = 'org.freedesktop.impl.portal.FileChooser'
METHODS = ('OpenFile', 'SaveFile', 'SaveFiles')
ARGS = '<arg type="o" direction="in"/>' + '<arg type="s" direction="in"/>' * 3 + '<arg type="a{sv}" direction="in"/><arg type="u" direction="out"/><arg type="a{sv}" direction="out"/>'
INFO = Gio.DBusNodeInfo.new_for_xml('<node><interface name="'+IFACE+'">' + ''.join('<method name="'+m+'">'+ARGS+'</method>' for m in METHODS) + '</interface></node>').interfaces[0]
REQUEST = Gio.DBusNodeInfo.new_for_xml('<node><interface name="org.freedesktop.impl.portal.Request"><method name="Close"/></interface></node>').interfaces[0]


def method(bus, sender, path, interface, name, parameters, invocation):
    handle = parameters.get_child_value(0).get_string()
    cancel = Gio.Cancellable()
    request_id = 0

    def close(connection, caller, request_path, request_interface, request_method, args, reply):
        connection.call('org.gnome.Nautilus', handle, 'org.freedesktop.impl.portal.Request', 'Close', None, None, Gio.DBusCallFlags.NO_AUTO_START, 3000, None, None, None)
        cancel.cancel()
        reply.return_value(None)

    request_id = bus.register_object(handle, REQUEST, close, None, None)

    def finished(connection, result, unused):
        try:
            invocation.return_value(connection.call_finish(result))
        except GLib.Error:
            # Backend exit/cancellation must complete the frontend request too.
            invocation.return_value(GLib.Variant('(ua{sv})', (2, {})))
        finally:
            bus.unregister_object(request_id)

    bus.call('org.gnome.Nautilus', '/org/freedesktop/portal/desktop', IFACE, name, parameters,
             GLib.VariantType.new('(ua{sv})'), Gio.DBusCallFlags.NONE, 2147483647,
             cancel, finished, None)


def acquired(bus, name):
    bus.register_object('/org/freedesktop/portal/desktop', INFO, method, None, None)


Gio.bus_own_name(Gio.BusType.SESSION, 'org.quickintosh.FinderPortal', Gio.BusNameOwnerFlags.NONE,
                 acquired, None, lambda *_: loop.quit())
loop = GLib.MainLoop()
loop.run()
