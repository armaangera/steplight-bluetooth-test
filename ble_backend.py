#!/usr/bin/env python3
import dbus, dbus.mainloop.glib
from gi.repository import GLib
import threading

# UUIDs for the custom service and characteristic
SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0'
CHAR_UUID    = 'abcdef01-1234-5678-1234-56789abcdef0'

class Application(dbus.service.Object):
    PATH_BASE = '/org/bluez/example'
    def __init__(self, bus):
        self.path = self.PATH_BASE
        self.bus = bus
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)

    def add_service(self, service):
        self.services.append(service)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_services(self):
        return self.services

    @dbus.service.method("org.bluez.GattApplication1",
                         in_signature="", out_signature="")
    def Release(self):
        print("GATT application released")

class Service(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/service'
    def __init__(self, index, uuid, primary, bus):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_properties(self):
        return {
            "org.bluez.GattService1": {
                "UUID": self.uuid,
                "Primary": self.primary,
            }
        }

    @dbus.service.method("org.freedesktop.DBus.Properties",
                         in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != "org.bluez.GattService1":
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.InvalidArgs: Invalid interface")
        return self.get_properties()

class Characteristic(dbus.service.Object):
    def __init__(self, uuid, flags, service, bus):
        self.path = service.get_path() + '/char0'
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.value = bytearray("Don't Cross", 'utf-8')
        self.notifying = False
        dbus.service.Object.__init__(self, bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {
            "org.bluez.GattCharacteristic1": {
                "UUID": self.uuid,
                "Service": self.service.get_path(),
                "Flags": self.flags,
                "Value": self.value
            }
        }

    @dbus.service.method("org.freedesktop.DBus.Properties",
                         in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != "org.bluez.GattCharacteristic1":
            raise dbus.exceptions.DBusException(
                "org.freedesktop.DBus.Error.InvalidArgs: Invalid interface")
        return self.get_properties()

    @dbus.service.method("org.bluez.GattCharacteristic1",
                         in_signature="", out_signature="ay")
    def ReadValue(self):
        return dbus.ByteArray(self.value)

    def StartNotify(self):
        if self.notifying:
            return
        self.notifying = True
        self.add_timeout()

    def add_timeout(self):
        if self.notifying:
            GLib.timeout_add(1000, self.notify_cb)

    def notify_cb(self):
        if not self.notifying:
            return False
        self.PropertiesChanged("org.bluez.GattCharacteristic1",
                               {"Value": dbus.ByteArray(self.value)}, [])
        return True

    @dbus.service.method("org.bluez.GattCharacteristic1",
                         in_signature="", out_signature="")
    def StopNotify(self):
        self.notifying = False

    @dbus.service.signal("org.freedesktop.DBus.Properties",
                         signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

    def set_crossing_state(self, state_str):
        self.value = bytearray(state_str, 'utf-8')
        if self.notifying:
            self.PropertiesChanged("org.bluez.GattCharacteristic1",
                                   {"Value": dbus.ByteArray(self.value)}, [])

def register_app_cb():
    print("GATT application registered")

def register_app_error_cb(error):
    print("Failed to register application:", str(error))
    mainloop.quit()

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
adapter_path = "/org/bluez/hci0"

app = Application(bus)
service = Service(0, SERVICE_UUID, True, bus)
char = Characteristic(CHAR_UUID, ["read","notify"], service, bus)
service.add_characteristic(char)
app.add_service(service)

manager = dbus.Interface(bus.get_object("org.bluez", "/org/bluez"),
                         "org.bluez.GattManager1")

mainloop = GLib.MainLoop()
manager.RegisterApplication(app.get_path(), {},
                            reply_handler=register_app_cb,
                            error_handler=register_app_error_cb)


threading.Thread(target=mainloop.run).start()
