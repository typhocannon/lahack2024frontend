import asyncio
import websockets
from bleak import BleakClient, BleakScanner

haptic_devices = {}
haptic_definition_client_names = {"Haptic Definition: Hands", "Haptic Definition: Vest"}

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
                # change it to the correct formatting to understand
                if isinstance(message, bytes):
                    # Decode for display purposes only
                    message = message.decode('utf-8')
                print("Received message:", message)
                # determine which device to broadcast the message to
                if message == "ping":

                    # broadcast the message to all haptic devices
                    for device_name, device_info in haptic_devices.items():
                        client = device_info["client"]
                        characteristics = device_info["client_characteristics"]
                        for characteristic in characteristics:
                            await client.write_gatt_char(characteristic.uuid, message.encode('utf-8'), response=False)

                    continue
                # parse the message and see if it is a command to a specific device
                command = message.split("-")
                device_name = ""
                if len(command) == 2:
                    # command is right format
                    action = command[0]
                    part = command[1]

                    # determine body part
                    if part == "chest":
                        device_name = "chest"
                        # hardcode 
                        message = "2"
                        print("Writing to device", device_name, "with message", message)
                        for device in haptic_devices:
                            device_info = haptic_devices[device]
                            client = device_info["client"]
                            characteristics = device_info["client_characteristics"]
                            for characteristic in characteristics:
                                await client.write_gatt_char(characteristic.uuid, message.encode('utf-8'), response=False)
                        continue
                    elif part == "left_hand":
                        device_name = "Haptic Definition: Vest"
                        if action == "hot":
                            message = "1"
                        else:
                            # impact
                            message = "0"
                    elif part == "right_hand":
                        device_name = "Haptic Definition: Hands"
                        if action == "hot":
                            message = "1"
                        else:
                            # impact
                            message = "0"

                    # if action == "hot" and part == "chest":
                    #     # not implemented, skip
                    #     device_name = ""
                    # elif action == "impact":
                    #     if part == "left_hand":
                    #         message = "0"
                    #     elif part == "right_hand" or part == "chest":
                    #         message = "1"
                    # elif action == "hot":
                    #     if part == "left_hand":
                    #         message = "2"
                    #     elif part == "right_hand":
                    #         message = "3"
                    #                 # Check if the message is in bytes, decode for printing, send as is for GATT char
                    print(haptic_devices)
                    print(len(device_name))
                    print(device_name in haptic_devices)
                if len(device_name) > 0 and device_name in haptic_devices:
                    print("Writing to device", device_name, "with message", message)
                    device_info = haptic_devices[device_name]
                    client = device_info["client"]
                    characteristics = device_info["client_characteristics"]
                    for characteristic in characteristics:
                        await client.write_gatt_char(characteristic.uuid, message.encode('utf-8'), response=False)

                

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed by server.")
        finally:
            connection_state["is_open"] = False

uri = "ws://localhost:5000/ws"
asyncio.run(main_client(uri))