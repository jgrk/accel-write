#include <SPI.h>
#include <SdFat.h>
#include "sdios.h"
#include "FreeStack.h"
#include "FatLib/FatFile.h"
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
const uint32_t TEST_TIME_SEC = 20; // Total data acquisition duration
const uint32_t TOTAL_BLOCK_COUNT = (RATE_B_PER_SEC*TEST_TIME_SEC + 511)/512; // How many 512 byte blocks that are to be written
const uint16_t MAX_BUFFER_SAMPLE = 40; // Number of samples per write


// file system
SdFat sd;

// test file
SdFile file;

volatile uint8_t DataOut[512]; // Array to store accel-data for SD-card

// file extent
uint8_t* pCache; // adress to 512 byte SD-cache
uint32_t bgnBlock, endBlock;


void setup() {
    // put your setup code here, to run once:
    if (DEBUG) {
        Serial.begin(115200);
        while (!Serial) { }
    }

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

    //*********************NOTE**************************************
    // NO SdFile calls are allowed while cache is used for raw writes
    //***************************************************************


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

    debugPrint("Setup done");
}

uint32_t nWrites = 0;


void loop() {
  // put your main code here, to run repeatedly:

    
    // Is there more data to collect?
    if (nWrites < TOTAL_BLOCK_COUNT) {
        // Should execute 80 times.
        // One write per accel 

        // Is accel-cache-data ready?
        if (accelBufferReady) {
            //Collect data
            for (uint16_t i = 0; i < 512; i++) {
                pCache[]
            }

        }


        debugPrint("Writing a block...");
        ++nWrites;
    }

    else {
        debugPrint("Data collection complete.");
        file.close()
        while(1);
    }

    

}

void readAccelBuffer() {
    digitalWrite(A1_CS, LOW);
    digitalWrite(A2_cs, LOW);
    rawOutputData myRawData_1;
    rawOutputData myRawData_2;


    for (int j = 0; j < 40; j++) {
        if (kxAccel_1.getRawAccelBufferData)
    }
    


}

void debugPrint(const String& msg) {
    if (DEBUG) {Serial.println(msg);}
}
