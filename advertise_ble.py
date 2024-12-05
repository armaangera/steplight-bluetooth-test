import bluetooth
from bluetooth.ble import BeaconService

def advertise_ble():
	service = BeaconService()
	uuid = "545528ca-1947-46f2-bd4d-b976f61f081a"  # Replace with a unique UUID
	major = 1  # Major version
	minor = 1  # Minor version
	tx_power = -59  # Signal strength (dBm)
	device_name = "StepLight"
	
	# Start advertising the BLE service
	print(f"Advertising {device_name}...")
	service.start_advertising(uuid, major, minor, tx_power)
	
	try:
		while True:
			pass  # Keep the script running
	except KeyboardInterrupt:
		print("Stopping advertisement...")
		service.stop_advertising()

if __name__ == "__main__":
	advertise_ble()

