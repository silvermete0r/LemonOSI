#include <DHT.h>
#include <dht11esp8266.h>
#include <DHT_U.h>
#include <ESP8266WiFi.h>
 
String apiKey = "03N7TZJVN4XWIMIX";     // API key from ThingSpeak
 
const char *ssid =  "AstanaIT";     // Wi-Fi ssid and WPA2 key
const char *pass =  "astanait";
const char* server = "api.thingspeak.com";
 
#define DHTPIN D1         // Pin where the dht11 is connected
#define SOUND D2          // Pin where the sound sensor
#define LIGHT A0          // Pin where the light sensor connected
#define PIR D4         // Pin where the motion sensor connected
 
DHT dht(DHTPIN, DHT11);

WiFiClient client;

void setup() 
{
      
       Serial.begin(115200);
       delay(10);
       dht.begin();
       pinMode(LIGHT, INPUT);
       pinMode(SOUND, INPUT);
       pinMode(PIR, INPUT);
       
       Serial.println("Connecting to ");
       Serial.println(ssid);
       
       WiFi.begin(ssid, pass);
 
      while (WiFi.status() != WL_CONNECTED) 
     {
            delay(500);
            Serial.print(".");
     }
      Serial.println("");
      Serial.println("WiFi connected");
}
 
void loop() 
{
      int s = digitalRead(SOUND);
      int l = analogRead(LIGHT);
      int m = digitalRead(PIR);
      float h = dht.readHumidity();
      float t = dht.readTemperature();
              if (isnan(l) || isnan(l)) 
                 {
                     Serial.println("Failed to read from light sensor!");
                      return;
                 }
                 
              if (isnan(h) || isnan(t)) 
                 {
                     Serial.println("Failed to read from DHT sensor!");
                      return;
                 }
 
                         if (client.connect(server,80))   //   "184.106.153.149" or api.thingspeak.com
                      {  
                            
                             String postStr = apiKey;
                             postStr +="&field1=";
                             postStr += String(t);
                             postStr +="&field2=";
                             postStr += String(h);
                             postStr +="&field3=";
                             postStr += String(l);
                             postStr +="&field4=";
                             postStr += String(s);
                             postStr +="&field5=";
                             postStr += String(m);
                             postStr += "\r\n\r\n";
 
                             client.print("POST /update HTTP/1.1\n");
                             client.print("Host: api.thingspeak.com\n");
                             client.print("Connection: close\n");
                             client.print("X-THINGSPEAKAPIKEY: "+apiKey+"\n");
                             client.print("Content-Type: application/x-www-form-urlencoded\n");
                             client.print("Content-Length: ");
                             client.print(postStr.length());
                             client.print("\n\n");
                             client.print(postStr);
 
                             Serial.print("Temperature: ");
                             Serial.print(t);
                             Serial.print(" degrees Celcius, Humidity: ");
                             Serial.println(h);
                             Serial.println("Light level: " + String(l));
                             Serial.println("Sound detected: " + String(s));
                             Serial.println("Motion detected: " + String(m));
                             Serial.println("%. Send to Thingspeak.");
                        }
          client.stop();
 
          Serial.println("Waiting...");
  
  delay(1000);
}
