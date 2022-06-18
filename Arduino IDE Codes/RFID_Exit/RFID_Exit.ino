#define SS_PIN 0  //D3
#define RST_PIN 16 //D0
#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>


MFRC522 mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance/object.
Servo servo;

int variable = 0;

const char* ssid = "Redmi Note 10";
const char* password = "helloworld";

String serverName = "http://192.168.108.208:5000/exit";
String serverName2 = "http://192.168.108.208:5000/email";


void setup()
{
  Serial.begin(115200);   // Initiate a serial communication

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {

    delay(1000);
    Serial.println("Out of Service..");
    Serial.println("Connecting..");

  }

  Serial.println("Connected!");

  SPI.begin();      // Initiate  SPI bus
  mfrc522.PCD_Init();   // Initiate MFRC522
  servo.attach(2); //D4
  servo.write(0);

}
void loop()
{


  // Look for new cards
  if ( ! mfrc522.PICC_IsNewCardPresent())
  {
    return;
  }
  // Select one of the cards
  if ( ! mfrc522.PICC_ReadCardSerial())
  {
    return;
  }
  //Show UID on serial monitor
  Serial.println();
  Serial.print(" UID tag :");
  String content = "";
  byte letter;
  for (byte i = 0; i < mfrc522.uid.size; i++)
  {
    Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
    Serial.print(mfrc522.uid.uidByte[i], HEX);
    content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " "));
    content.concat(String(mfrc522.uid.uidByte[i], HEX));
  }
  content.toUpperCase();
  Serial.println();




//
  WiFiClient client;
  HTTPClient http;

  http.begin(client, serverName);
  http.addHeader("Content-Type", "application/json");
  int httpCode = http.POST("{\"rfid\":\""+content.substring(1)+"\"}");

  String payload = http.getString();

  Serial.println(payload);
  http.end();
  
  if(payload=="Thank you"){
    servo.write(190);
    delay(5000);
    servo.write(10);
    delay(1000);
    http.begin(client, serverName2);
    http.addHeader("Content-Type", "application/json");
    int httpCode1 = http.POST("{\"rfid\":\""+content.substring(1)+"\"}");
    http.end();
   }
  
  
  delay(1000);
 
}
