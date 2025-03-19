/*
How the program works:
  SETUP: 
    - Initialize two accels on a sepparate SPI bus and configure SD-card with a contiguous file.
    - Enable buffer reads on accels, raise interuptions and configure number of samples before watermark trigger.
    - Setup SD-cache. The first accel will write 40 samples (reads of 40x6 bytes) to the first half of cache. 
      Second accel will write the same amount to the other half.

        SD-CACHE SETUP (512 BYTES)
        _______________________________________________________________________________________
        [   40-SAMPLES-FROM-ACCEL1   |  16-BYTES  |   40-SAMPLES-FROM-ACCEL2   |   16-BYTES   ]
        ---------------------------------------------------------------------------------------
  
  LOOP:
    - Check if more samples are needed. 
    - Then checks if the accel buffers are ready.
    - If accel buffers are ready, each will write to the SD-cahce and then flushed.

  SPECIFIC REQUIREMENTS:
    SdFat@1.1.0 
*/

#include <SPI.h>
#include <SdFat.h>
#include "sdios.h"
#include "FreeStack.h"
#include "wiring_private.h"
#include <SparkFun_KX13X.h> 



// Run configurations
const bool DEBUG = true;  

// Accels
SparkFun_KX132_SPI kxAccel_1;
SparkFun_KX132_SPI kxAccel_2;


// Chip Selects
const uint8_t A1_CS = 0;
const uint8_t A2_CS = 1;
const uint8_t SD_CS = 10;


// Interrupts 
const uint8_t A1_INT = 5;
const uint8_t A2_INT = 6;


// Accel properties
const uint8_t SIZE_PER_SAMPLE = 6; // 6 bytes per sample 
const uint32_t ODR = 800; // Output data rate at 800 Hz
const uint32_t RATE_B_PER_SEC = ODR * SIZE_PER_SAMPLE; // Acquisition rate in bytes 
const uint32_t TEST_TIME_SEC = 20; // Total data acquisition duration in sec
const uint32_t TOTAL_BLOCK_COUNT = (RATE_B_PER_SEC*TEST_TIME_SEC + 511)/512; // How many 512 byte blocks that are to be written
const uint16_t MAX_BUFFER_SAMPLES = 40; // Number of samples per write


// file system
SdFat sd;

// test file
SdFile file;

volatile uint8_t DataOut[512]; // Array to store accel-data for SD-card

// file extent
uint8_t* pCache; // adress to 512 byte SD-cache
uint32_t bgnBlock, endBlock;

volatile bool accel1BufferReady, accel2BufferReady;

// Second SPI
//              sercom    miso, sck, mosi,  tx   
SPIClass accel_SPI(&sercom4,  4,    A3,  A2,   SPI_PAD_0_SCK_1, SERCOM_RX_PAD_2); 
SPISettings mySetting(2000000, MSBFIRST, SPI_MODE0);


void setup() {
    if (DEBUG) {
        Serial.begin(115200);
        while (!Serial) { }
    }
    ////////////////// PIN-SETUP//////////////////////
    pinMode(A1_CS, OUTPUT);
    pinMode(A2_CS, OUTPUT);
    digitalWrite(A1_CS, HIGH);
    digitalWrite(A2_CS, HIGH);


    ////////////////// ACCEL-SPI-INIT /////////////////////
    accel_SPI.begin();
    pinPeripheral(4, PIO_SERCOM_ALT);
    pinPeripheral(A3, PIO_SERCOM_ALT);
    pinPeripheral(A2, PIO_SERCOM_ALT);
    delay(500);


    ////////////////// SD-SETUP //////////////////////
    // Initialize SD-card at 24 MHz
    if ( !sd.begin(SD_CS, SD_SCK_MHZ(24))) {
        debugPrint("Failed reading SD. Freezing.");
        while(1);
    }
    // Clean SD-card
    sd.remove("accel.DAT");
    // Create a contiguous file
    if (!file.createContiguous("accel.DAT", 512UL*TOTAL_BLOCK_COUNT*2)) {
        debugPrint("createContiguous failed");
    }
    // Get the location of the file blocks
    if (!file.contiguousRange(&bgnBlock, &endBlock)) {
        debugPrint("contiguousRange failed");
    }

    // NO SdFile calls are allowed while cache is used for raw writes

    pCache = (uint8_t*)sd.vol() -> cacheClear(); // clear the SD-cache and store its address in pCache
    memset(pCache, ' ', 512);
    pCache[253] = '1';
    pCache[254] = '\r';
    pCache[255] = '\n';
    pCache[509] = '2';
    pCache[510] = '\r';
    pCache[511] = '\n';

    if (!sd.card()->writeStart(bgnBlock, TOTAL_BLOCK_COUNT)) {
        debugPrint("writeStart failed");
    }


    ////////////////////// ACCEL-SETUP /////////////////////////////

    if (!kxAccel_1.begin(accel_SPI, mySetting, A1_CS)) {
        debugPrint("Accel 1 failed");
        while(500);
    }

    initializeAccel(kxAccel_1, A1_CS);
    
    debugPrint("Accel 1 done");

    if (!kxAccel_2.begin(accel_SPI, mySetting, A2_CS)) {
        debugPrint("Accel 2 failed");
        while(1);
    }
    initializeAccel(kxAccel_2, A2_CS);    
    
    pinMode(A1_INT, INPUT_PULLUP);
    pinMode(A2_INT, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(A1_INT), A1_ready, RISING);
    attachInterrupt(digitalPinToInterrupt(A2_INT), A2_ready, RISING);


    debugPrint("Setup done");
}

uint32_t nWrites = 0;


void loop() {
    // Is there more data to collect?
    if (nWrites < TOTAL_BLOCK_COUNT) {
        // Should execute 80 times.
        // One write per accel 
        debugPrint("Writing block number...");
        debugPrint(String(accel1BufferReady && accel2BufferReady));
        

        // Is accel-cache-data ready?
        if ( accel2BufferReady ) {

            debugPrint("Accel-buffer ready. Filling SD-cache...");
            readAccelBuffer();
            for (uint16_t i = 0; i < 512; i++) {
                pCache[i] = DataOut[i];
            }  
            debugPrint("Saving data from SD-cache...");
            
            
            //write data
            if (!sd.card()->writeData(pCache)) {
                debugPrint("writeData failed");
            }
            nWrites++;
            accel1BufferReady = false;
            accel2BufferReady = false;        
        }

        else {
            debugPrint("Accel-buffer not ready..");
        }
    }

    else {
        if (!sd.card()->writeStop()) {
            debugPrint("writeStop failed");
        }
        file.close();
        debugPrint("Data collection complete.");
        
        while(1);
    }
}


void readAccelBuffer() {
    digitalWrite(A1_CS, LOW);
    digitalWrite(A2_CS, LOW);
    rawOutputData myRawData_1;
    rawOutputData myRawData_2;

    // Overwrite DataOut with new content from both accel-buffers
    for (int j = 0; j < MAX_BUFFER_SAMPLES; j++) {
        if (kxAccel_1.getRawAccelBufferData(&myRawData_1, 1) == true) {
            DataOut[6 * j + 0] = lowByte(myRawData_1.xData);
            DataOut[6 * j + 1] = highByte(myRawData_1.xData);
            DataOut[6 * j + 2] = lowByte(myRawData_1.yData);
            DataOut[6 * j + 3] = highByte(myRawData_1.yData);
            DataOut[6 * j + 4] = lowByte(myRawData_1.zData);
            DataOut[6 * j + 5] = highByte(myRawData_1.zData);

        }

        if (kxAccel_2.getRawAccelBufferData(&myRawData_2, 1) == true) {
            DataOut[256 + 6 * j + 0] = lowByte(myRawData_2.xData);
            DataOut[256 + 6 * j + 1] = highByte(myRawData_2.xData);
            DataOut[256 + 6 * j + 2] = lowByte(myRawData_2.yData);
            DataOut[256 + 6 * j + 3] = highByte(myRawData_2.yData);
            DataOut[256 + 6 * j + 4] = lowByte(myRawData_2.zData);
            DataOut[256 + 6 * j + 5] = highByte(myRawData_2.zData);
        }
    }

    digitalWrite(A1_CS, HIGH);
    digitalWrite(A2_CS, HIGH);
}


void A1_ready() {
    accel1BufferReady = true;
}


void A2_ready() {
    accel2BufferReady = true;
}


void debugPrint(const String& msg) {
    if (DEBUG) {
        Serial.println(msg);
        delay(500);
    }
}


void initializeAccel(SparkFun_KX132_SPI &accel, byte csPin) {
    accel.enableAccel(false);
    accel.enableBufferInt();
    accel.enablePhysInterrupt();
    accel.routeHardwareInterrupt(0x40);
    accel.enableSampleBuffer();
    accel.setBufferOperationMode(0x01);
    accel.setBufferThreshold(MAX_BUFFER_SAMPLES);
    accel.setBufferResolution();
    accel.clearBuffer();
    accel.setRange(SFE_KX132_RANGE16G);
    accel.setOutputDataRate(0x0A);
    accel.enableAccel();
    delay(5);
    digitalWrite(csPin, HIGH);
}
