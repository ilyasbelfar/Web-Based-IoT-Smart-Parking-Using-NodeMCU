  

#define SS_PIN 0  //D3
#define RST_PIN 16 //D0
#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>
#include <LiquidCrystal_I2C.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>



MFRC522 mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance/object.
Servo servo;
LiquidCrystal_I2C lcd(0x3F, 16, 2);


int variable = 0;

const char* ssid = "Redmi Note 10";
const char* password = "helloworld";

String serverName = "http://192.168.108.208:5000/entry";


void setup()
{
//  WiFiServer server(80);
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
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.println("                ");
  lcd.setCursor(0 , 1);
  lcd.println("                ");
  lcd.setCursor(1, 0);
  lcd.print("Show your card:");
  servo.attach(2); //D4
  servo.write(0);
  delay(2000);

}
void loop()
{

  lcd.setCursor(0, 0);
  lcd.println("                ");
  lcd.setCursor(0 , 1);
  lcd.println("                ");
  lcd.setCursor(1, 0);
  lcd.print("Show your card:");

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

//  Serial.println(httpCode);

  http.end();
  Serial.println(payload);
  lcd.setCursor(0, 0);
  lcd.println("                ");
  lcd.setCursor(0 , 1);
  lcd.println("                ");
  if (payload != "Tag Not Found" && payload != "Tag Suspended" && payload != "Tag Already Used" && payload != "We are Full"  && payload != NULL ) 
  {
    lcd.setCursor(1, 0);
    lcd.println(" Access Authorized ");
    delay(1000);
    lcd.setCursor(0, 0);
    lcd.println("                ");
    lcd.setCursor(0 , 1);
    lcd.println("                ");
    lcd.setCursor(1, 0);
    lcd.println("Welcome");
    lcd.setCursor(0 , 1);
    lcd.println("Mr " + payload);
    servo.write(190);
    delay(5000);
    servo.write(10);
    lcd.setCursor(0, 0);
    lcd.println("                ");
    lcd.setCursor(0 , 1);
    lcd.println("                ");
  }

  else if (payload == NULL) 
  {
    lcd.setCursor(1, 0);
    lcd.println("Out of Service");
    delay(2000);
    lcd.setCursor(0, 0);
    lcd.println("                ");
    lcd.setCursor(0 , 1);
    lcd.println("                ");
  }
  
  else   {
    lcd.setCursor(0, 0);
    lcd.println("                ");
    lcd.setCursor(0 , 1);
    lcd.println("                ");
    lcd.setCursor(1, 0);
    lcd.println(" Access Denied ");
    lcd.setCursor(0 , 1);
    lcd.println(payload);
    Serial.println( payload );
    delay(3500);
    lcd.setCursor(0, 0);
    lcd.println("                ");
    lcd.setCursor(0 , 1);
    lcd.println("                ");
    delay(3000);
  }
}
