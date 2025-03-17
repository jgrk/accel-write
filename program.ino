#include <SPI.h>
#include "wiring_private.h"
#include <SparkFun_KX13X.h>
#include <RTClib.h>
#include "SdFat.h"
#include "sdios.h"

#define BUFFER_SAMPLE_LIM 42
#define DATA_BLOCK_SIZE (BUFFER_SAMPLE_LIM * 6)  // Each sample (X, Y, Z) is 6 bytes (16-bit)
#define OUTPUT_DATA_RATE 0x0A

// Setup SPI bus for accelerometers
SPIClass accel_SPI(&sercom4, 4, A3, A2, SPI_PAD_0_SCK_1, SERCOM_RX_PAD_2);
SPISettings mySetting(2000000, MSBFIRST, SPI_MODE0);

// Create two separate objects for your two accelerometers.
SparkFun_KX132_SPI kxAccel1;
SparkFun_KX132_SPI kxAccel2;

SdFat sd; // SD File system
SdFile file; // File object for writing data

// File names
char fileName1[12] = "accel_1.DAT";
char fileName2[12] = "accel_2.DAT";
const bool debugMode = true;

// Data buffers
volatile uint8_t DataOut1[DATA_BLOCK_SIZE];
volatile uint8_t DataOut2[DATA_BLOCK_SIZE];
volatile bool newDataReady1 = false;
volatile bool newDataReady2 = false;

// Pin definitions
const byte A1CS = 0;
const byte A2CS = 1;
const byte SDCS = 10;
const byte AccelBufferINT1 = 5;
const byte AccelBufferINT2 = 6;

RTC_PCF8523 rtc; // Real Time Clock

#define SPI_CLOCK SD_SCK_MHZ(2)
#define SD_CONFIG SdSpiConfig(SDCS, SHARED_SPI, SPI_CLOCK)


void setup() {
    if (debugMode) {
        Serial.begin(115200);
        while (!Serial) { }
    }

    // Configure SPI chip select pins
    pinMode(A1CS, OUTPUT);
    pinMode(A2CS, OUTPUT);
    digitalWrite(A1CS, HIGH);
    digitalWrite(A2CS, HIGH);

    // Initialize SPI
    accel_SPI.begin();
    pinPeripheral(4, PIO_SERCOM_ALT);
    pinPeripheral(A3, PIO_SERCOM_ALT);
    pinPeripheral(A2, PIO_SERCOM_ALT);
    delay(500);

    // Initialize accelerometers
    while (!kxAccel1.begin(accel_SPI, mySetting, A1CS)) {
        debugPrint("KX132 #1 communication error");
        delay(500);
    }
    initializeAccel(kxAccel1, A1CS);

    while (!kxAccel2.begin(accel_SPI, mySetting, A2CS)) {
        debugPrint("KX132 #2 communication error!");
        delay(500);
    }
    initializeAccel(kxAccel2, A2CS);

    debugPrint("Both accelerometers initialized.");

    // Initialize SD card
    if (!sd.begin(SD_CONFIG)) {
        debugPrint("SD Card init failed. Freezing.");
        while (1);
    }
    debugPrint("SD Card initialized.");

    // Initialize RTC
    // while (!rtc.begin()) {
    //    debugPrint("RTC not found.");
    //    delay(500);
    //}
    //DateTime now = rtc.now();
    //if (now.year() < 2020) {  // Ensuring valid RTC time
    //    debugPrint("RTC time invalid. Please set the clock.");
    //    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
    //}

    // Format file names properly
    //snprintf(fileName1, sizeof(fileName1), "%02d%02d%02d%02d_1.DAT", now.month(), now.day(), now.hour(), now.minute());
    //snprintf(fileName2, sizeof(fileName2), "%02d%02d%02d%02d_2.DAT", now.month(), now.day(), now.hour(), now.minute());


    createDataFile(fileName1);
    createDataFile(fileName2);

    // Attach buffer interrupts
    pinMode(AccelBufferINT1, INPUT_PULLUP);
    pinMode(AccelBufferINT2, INPUT_PULLUP);

    // When buffer is full, write buffer contents to cpu
    attachInterrupt(digitalPinToInterrupt(AccelBufferINT1), writeAccelData1, RISING);
    attachInterrupt(digitalPinToInterrupt(AccelBufferINT2), writeAccelData2, RISING);

    debugPrint("Setup complete.");
}

void loop() {
    if (newDataReady1) {
        saveToSD(fileName1, DataOut1);
        newDataReady1 = false;
    }

    if (newDataReady2) {
        saveToSD(fileName2, DataOut2);
        newDataReady2 = false;
    }
}


void debugPrint(const String &message) {
    if (debugMode) {
        Serial.println(message);
    }
}

void initializeAccel(SparkFun_KX132_SPI &accel, byte csPin) {
    accel.enableAccel(false);
    accel.enableBufferInt();            //  Enables the Buffer interrupt
    accel.enablePhysInterrupt();        //  Enables interrupt pin 1
    accel.routeHardwareInterrupt(0x40);
    accel.enableSampleBuffer();
    accel.setBufferOperationMode(0x01); // STREAM mode
    accel.setBufferThreshold(BUFFER_SAMPLE_LIM);
    accel.setBufferResolution();
    accel.clearBuffer();
    accel.setRange(SFE_KX132_RANGE16G);
    accel.setOutputDataRate(10);
    accel.enableAccel();
    delay(5);
    digitalWrite(csPin, HIGH);
}

void writeAccelData1() {
    readAccelBuffer(kxAccel1, A1CS, DataOut1);
    newDataReady1 = true;
}

void writeAccelData2() {
    readAccelBuffer(kxAccel2, A2CS, DataOut2);
    newDataReady2 = true;
}

void readAccelBuffer(SparkFun_KX132_SPI &accel, byte csPin, volatile uint8_t *buffer) {
    digitalWrite(csPin, LOW);
    rawOutputData myRawData;
    accel.getRawAccelBufferData(&myRawData, 1);

    for (int i = 0; i < BUFFER_SAMPLE_LIM; i++) {
        if (accel.getRawAccelBufferData(&myRawData, 1)) {
            buffer[6 * i + 0] = lowByte(myRawData.xData);
            buffer[6 * i + 1] = highByte(myRawData.xData);
            buffer[6 * i + 2] = lowByte(myRawData.yData);
            buffer[6 * i + 3] = highByte(myRawData.yData);
            buffer[6 * i + 4] = lowByte(myRawData.zData);
            buffer[6 * i + 5] = highByte(myRawData.zData);

            debugPrint("Sample ");
            debugPrint((const String)i);
            debugPrint(" -> X: ");
            debugPrint((const String)myRawData.xData);
            debugPrint(", Y: ");
            debugPrint((const String)myRawData.yData);
            debugPrint(", Z: ");
            debugPrint((const String)myRawData.zData);
        }
    }
    digitalWrite(csPin, HIGH);
}

void createDataFile(char *filename) {
    if (!file.open(filename, O_RDWR | O_CREAT | O_TRUNC)) {
        debugPrint("Failed to create file: " + String(filename));
    } else {
        debugPrint("File ready: " + String(filename));
        file.close();
    }
}

void saveToSD(const char *filename, volatile uint8_t *buffer) {
    if (!file.open(filename, O_RDWR | O_APPEND)) {
        debugPrint("Failed to open file: " + String(filename));
        return;
    }
    file.write((const uint8_t*)buffer, DATA_BLOCK_SIZE);
    file.close();
}
