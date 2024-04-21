#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

//BLE server name
#define bleServerName "Haptic Definition: Hands"
// #define bleServerName "Haptic Definition: Vest"

// See the following for generating UUIDs:
// https://www.uuidgenerator.net/
// hands
#define SERVICE_UUID "7ce72a1c-aaee-490e-bc6d-abb82854e460"

// vest
// #define SERVICE_UUID "102f11a4-1503-4f0f-b98b-f587bd4bd7f4"


// Timer variables
unsigned long lastTime = 0;
unsigned long timerDelay = 30000;

bool deviceConnected = false;




BLECharacteristic bleTestCharacteristics("cba1d466-344c-4be3-ab3f-189f80dd7518", BLECharacteristic::PROPERTY_WRITE);
BLEDescriptor bleTestDescriptor(BLEUUID((uint16_t)0x2902));

const int vibration = 4;
const int heat = 5;
const int vest = 6;

void triggerPin(int seconds, int pin) {
  // GPIO
  digitalWrite(pin, HIGH);
  delay(seconds * 1000);
  digitalWrite(pin, LOW);
}

//Setup callbacks onConnect and onDisconnect
class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    Serial.println("Successfully connected!");
    deviceConnected = true;
  };
  void onDisconnect(BLEServer* pServer) {
    Serial.println("Disconnected");
    deviceConnected = false;
    BLEDevice::startAdvertising();
  };
};

class MyCallbacks: public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic *pCharacteristic) {
        Serial.println("I got something!");
        std::string value = pCharacteristic->getValue();

        if (value.length() > 0) {
            Serial.println("Received over BLE:");
            for (int i = 0; i < value.length(); i++)
                Serial.print(value[i]);
            Serial.println();
            if (value == "0") {
              Serial.println("Zero");
              triggerPin(1, vibration);
            }
            if (value == "1") {
              Serial.println("One");
              triggerPin(1, heat);
            }
            if (value == "2") {
              Serial.println("Two");
              triggerPin(1, vest);
            }
        }
    }
};

void setup() {
  // Start serial communication 
  Serial.begin(115200);
  Serial.println("Starting BLE application");

  pinMode(vibration, OUTPUT);
  pinMode(heat, OUTPUT);
  pinMode(vest, OUTPUT);

  // Create the BLE Device
  BLEDevice::init(bleServerName);
  Serial.println("Bluetooth device initialized");

  // Create the BLE Server
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());
  Serial.println("Bluetooth server created");

  // Create the BLE Service
  BLEService *bleService = pServer->createService(SERVICE_UUID);
  Serial.println("Bluetooth service created");

  // Create a BLE Characteristic
  BLECharacteristic *pCharacteristic = bleService->createCharacteristic(
                                       "cba1d466-344c-4be3-ab3f-189f80dd7518",
                                       BLECharacteristic::PROPERTY_WRITE
                                     );

  // Adding a descriptor to the characteristic
  pCharacteristic->addDescriptor(new BLE2902());
  pCharacteristic->setCallbacks(new MyCallbacks());

  // Start the service
  bleService->start();
  Serial.println("Service started");

  // Start advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // functions that help with faster connections at the cost of more power consumption
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();
  Serial.println("Now advertising");
}

void loop() {
  // Serial.print(".");
  // delay(1000);
}