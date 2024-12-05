from flask import Flask, request, jsonify
import asyncio
from bleak import BleakScanner, BleakClient

app = Flask(__name__)
loop = asyncio.get_event_loop()

connected_client = None

@app.route('/scan', methods=['GET'])
def scan_devices():
    """Scan for BLE devices."""
    async def scan():
        devices = await BleakScanner.discover()
        return {device.address: device.name for device in devices}

    devices = loop.run_until_complete(scan())
    return jsonify(devices)


@app.route('/connect', methods=['POST'])
def connect_to_device():
    """Connect to a specific BLE device."""
    global connected_client
    address = request.json.get('address')

    if not address:
        return jsonify({"error": "Device address is required"}), 400

    async def connect(address):
        client = BleakClient(address)
        await client.connect()
        return client

    try:
        connected_client = loop.run_until_complete(connect(address))
        return jsonify({"message": f"Connected to {address}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/disconnect', methods=['POST'])
def disconnect_device():
    """Disconnect from the current BLE device."""
    global connected_client
    if connected_client and connected_client.is_connected:
        async def disconnect():
            await connected_client.disconnect()

        loop.run_until_complete(disconnect())
        connected_client = None
        return jsonify({"message": "Disconnected successfully"})
    else:
        return jsonify({"error": "No device connected"}), 400


@app.route('/write', methods=['POST'])
def write_characteristic():
    """Write to a characteristic."""
    global connected_client
    if not connected_client or not connected_client.is_connected:
        return jsonify({"error": "No device connected"}), 400

    characteristic_uuid = request.json.get('characteristic_uuid')
    value = request.json.get('value')

    if not characteristic_uuid or value is None:
        return jsonify({"error": "Characteristic UUID and value are required"}), 400

    async def write(uuid, value):
        await connected_client.write_gatt_char(uuid, bytearray(value, 'utf-8'))

    try:
        loop.run_until_complete(write(characteristic_uuid, value))
        return jsonify({"message": "Write successful"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
