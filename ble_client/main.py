import asyncio
import websockets
from bleak import BleakClient, BleakScanner

haptic_devices = {}
haptic_definition_client_names = {"Haptic Definition: Right Hand", "Haptic Definition: Left Hand", "Haptic Definition: Vest"}

async def connect_and_setup_device(device):
    client = BleakClient(device)
    await client.connect()
    client_characteristics = []
    print("Connected to", device.name, "Getting services...")
    client_services_collection = client.services
    client_services = client_services_collection.services
    for service in client_services.values():
        for characteristic in service.characteristics:
            if "write" in characteristic.properties:
                await client.write_gatt_char(characteristic.uuid, "Hello World!".encode(), response=False)
                client_characteristics.append(characteristic)
    return {"client": client, "client_characteristics": client_characteristics}

async def main_client(uri):
    print("looking for bluetooth")
    
    # scan for bluetooth devices once
    print("Scanning for bluetooth devices...")
    devices = await BleakScanner.discover()
    for d in devices:
        if d.name in haptic_definition_client_names:
            device_info = await connect_and_setup_device(d)
            haptic_devices.update({d.name: device_info})
    print(haptic_devices)
    if (len(haptic_devices) == 0):
        print("No haptic devices found")
        return

    # now handle the socket events
    print("Ready to connect to websocket server")
    while True:
        connection_state = {"is_open": True}
        websocket = await websockets.connect(uri)
        try:
            async for message in websocket:
                print("Received message:", message)
                # change it to the correct formatting to send
                # Check if the message is in bytes, decode for printing, send as is for GATT char
                if isinstance(message, bytes):
                    # Decode for display purposes only
                    decoded_message = message.decode('utf-8')
                    print("Received message:", decoded_message)
                    # No need to encode, message is already in bytes
                    message_to_send = message
                else:
                    # Assume message is str and needs encoding
                    print("Received message:", message)
                    message_to_send = message.encode('utf-8')
                # broadcast the message to all haptic devices
                for device_name, device_info in haptic_devices.items():
                    client = device_info["client"]
                    characteristics = device_info["client_characteristics"]
                    for characteristic in characteristics:
                        await client.write_gatt_char(characteristic.uuid, message_to_send, response=False)

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed by server.")
        finally:
            connection_state["is_open"] = False

uri = "ws://localhost:5000"
asyncio.run(main_client(uri))