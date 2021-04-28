#include "RTClib.h"
#include <ESP8266WiFi.h>
#include <WiFiClient.h> 
#include <ESP8266WebServer.h>
#include <ESP8266HTTPClient.h>
#include <TinyGPS++.h>
#include <SoftwareSerial.h>
#include <SPI.h>
#include <MFRC522.h>
#include <SD.h>

//region GLOBAL_CONFIGURATION
bool debug = false;
bool simulate_gps = true;
#define SS_PIN 2
#define RST_PIN 0
//endregion

//region VARIABLE_INITIALIZATION
RTC_DS1307 rtc;
MFRC522 mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance.
int out = 0;
//const char *ssid = "APT 902 2g";  //ENTER YOUR WIFI SETTINGS
//const char *password = "mansaolaranja";
String ssid;
String password;
int CS_SD = 16; // D0
const char *host = "http://filipe027.pythonanywhere.com/";
TinyGPSPlus  gps; 
SoftwareSerial  ss(4, 5) ;

float latitude , longitude;
int year , month , day, hour , minute , second;

String date_str , time_str , lat_str , lng_str;

int pm;
int counter;
File file;

String rfid_tag;
String server_time;
String login_id = "null";
String signedin = "dnd";
unsigned long t0;
File login_root;
File location_root;
bool scanning_location_root = true;
File login_file;
File location_file;
String mac;
DateTime now;

//endregion

void setup() {
  
  if(debug == false){
    pinMode(15, OUTPUT);
  }
  lock_relay();
  
  mac = WiFi.macAddress();
  mac.replace(":", "_");
  
  counter = 0;
  SPI.begin();      // Initiate  SPI bus
  mfrc522.PCD_Init();   // Initiate MFRC522
  delay(1000);
  Serial.begin(9600);
  //ss.begin(9600);
  
  if (! rtc.begin()){
    log_debug("RTC não encontrado");
  }
  else{
    log_debug("RTC OK");
  }
  
  
  //Serial.println("Iniciando cartao SD...");
  int sd_tries = 0;
  while (!SD.begin(CS_SD))
  {
    //Serial.println("Falha na inicializacao do SD!");
    sd_tries +=1;
    delay(100);
    if(sd_tries >=10){
      break;
    }
  }

  if (sd_tries <10){
    read_ssid();
  }else{
    ssid = "admin";
    password = "123456";
  }
  long init_backup_timeout = millis();
  rfid_tag = "";
  while (millis() - init_backup_timeout <= 5000){
    if ( mfrc522.PICC_IsNewCardPresent()){
      rfid_tag = read_rfid();
      break;
    }else{
      delay(1);
    }
  }
  if (rfid_tag != ""){
    if (sdcard_check_backup(rtc.now().secondstime(), rfid_tag)){
      unlock_relay();
      log_debug("Rele liberado por criterio de segurança");
    }
  }
  else{
    lock_relay();
  }
  
  WiFi.mode(WIFI_OFF);        //Prevents reconnection issue (taking too long to connect)
  delay(1000);
  WiFi.mode(WIFI_STA);        //This line hides the viewing of ESP as wifi hotspot
  
  
  connect_to_wifi();
  if (WiFi.status() == WL_CONNECTED)
    log_debug("Conectado a rede Wi-Fi");
  else
    log_debug("Falha ao conectar");
  
  
  if( wifi_connected() ){
    server_time = get_server_time();
    log_debug("Hora do servidor: " + server_time);
    //Server time format = 2020-03-07-22-59-58
    int year = server_time.substring(0,4).toInt();
    int month = server_time.substring(5,7).toInt();
    int day = server_time.substring(8,10).toInt();
    int hour = server_time.substring(11,13).toInt();
    int minute = server_time.substring(14,16).toInt();
    int second = server_time.substring(17,19).toInt();
    rtc.adjust(DateTime(year, month, day, hour, minute, second));
    String now_str = get_time_str();
    log_debug("Hora do RTC ajustado para: " + now_str);
  }
  
  if (sd_tries<10){
    login_root = SD.open("/L/");
    location_root = SD.open("/C/");
    login_root.rewindDirectory();
    location_root.rewindDirectory();
    login_file = login_root.openNextFile();
    location_file = location_root.openNextFile();
  }
  t0 = millis();
  
}

void loop() {
  if ( ! wifi_connected()){
    connect_to_wifi();
  }
  if (millis() - t0 >= 5000){
    if (update_gps()){
      
      sdcard_log_location(login_id, lat_str + "_" + lng_str, get_time_str());
      if( wifi_connected() ){
        log_debug("Requisicao de localização HTTP enviada com dados: '"
        "id=" +login_id + "&pos=" + lat_str + "_" + lng_str + "&time=" + get_time_str() + "&mac=" + mac );
        
        post_location(lat_str + "_" + lng_str);
      }
      else{
        log_debug("Dados salvos no cartão SD para envio posterior: "
        "id=" +login_id + "&pos=" + lat_str + "_" + lng_str + "&time=" + get_time_str()+ "&mac=" + mac);
        sdcard_log_location_pending(login_id, lat_str + "_" + lng_str, get_time_str());
      }
    }
    t0 = millis();
  }
  
  if (signedin == "alw"){
    if (scanning_location_root){
      if (location_file.available())
      {
        if (wifi_connected()){
          sdcard_upload_location_pending();
        }
      }
      else{
        String name_file = location_file.name();
        location_file.close();
        SD.remove("/C/" + name_file);
        location_file = location_root.openNextFile();
        if ( !location_file ){
          location_file.close();
          scanning_location_root = false;
        }
      }
    }
    else{
      rewind_locdir_with_timeout();
    }
  }
  else{
    // Look for new cards
    if ( ! mfrc522.PICC_IsNewCardPresent()) 
    {
      return;
    }
    else{
      rfid_tag = read_rfid();
      log_debug("Leitura do cartão RFID" + rfid_tag);
      if( wifi_connected() and rfid_tag != "" ){
        String result = request(rfid_tag);
        signedin = result.substring(0,3);
        login_id = result.substring(4);
        if (signedin == "alw") {
          log_debug("Autenticacao liberada pelo servidor");
          sdcard_store_backup(rtc.now().secondstime(), rfid_tag);
          unlock_relay();
          log_debug("Rele de partida liberado");
        }
        sdcard_log_login(login_id, signedin, get_time_str());
        
      }
    }
  }
  
    
}

//region GPS_UPDATE
String locations[]= {
"-07.142862_-034.850775",
"-07.142106_-034.850902",
"-07.141590_-034.849069",
"-07.138721_-034.849917",
"-07.138009_-034.847697",
"-07.137141_-034.845460",
"-07.135592_-034.845722",
"-07.134171,-034.846300",
"-07.132237,-034.844527",
"-07.131625,-034.844631",
"-07.130739,-034.842246",};
int i_loc = 0, loc_len=10;
bool update_gps() {
  if (simulate_gps){
    if(i_loc <= loc_len){
      lat_str = locations[i_loc].substring(0,10);
      lng_str = locations[i_loc].substring(11);
      i_loc++;
      return true;
    }else{
      return false;
    }
  }
  else {
    if (Serial.available() > 0){
      while (Serial.available() > 0){
        if ( gps.encode( Serial.read() )){
          if (gps.location.isValid())
          {
            latitude = gps.location.lat();
            lat_str = String(latitude , 6);
            longitude = gps.location.lng();
            lng_str = String(longitude , 6);
          }

          if (gps.date.isValid())
          {
            day = gps.date.day();
            month = gps.date.month();
            year = gps.date.year();
            hour = gps.time.hour();
            minute = gps.time.minute();
            second = gps.time.second();
          }
        }
      }
      return true;
    }
    else{
      return false;
    }
  }
}
//endregion

//region HTTP_REQUESTS
String request(String tag){
  HTTPClient http;    //Declare object of class HTTPClient

  
  //Post Data
  String postData = "tag=" +tag + "&location=1353&mac=" + mac;
  
  http.begin("http://filipe027.pythonanywhere.com/post/");              //Specify request destination
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");    //Specify content-type header

  int httpCode = http.POST(postData);   //Send the request
  String payload = http.getString();    //Get the response payload

  

  http.end();  //Close connection
  return payload;
}

String post_location(String pos){
  HTTPClient http;    //Declare object of class HTTPClient

  
  //Post Data
  String postData = "id=" +login_id + "&pos=" + pos + "&time=" + get_time_str() + "&mac=" + mac;
  
  http.begin("http://filipe027.pythonanywhere.com/post-loc/");              //Specify request destination
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");    //Specify content-type header

  int httpCode = http.POST(postData);   //Send the request
  String payload = http.getString();    //Get the response payload

  http.end();  //Close connection
  log_debug(payload);
  return payload;
}

String post_to_url(String path, String postData){
  HTTPClient http;    //Declare object of class HTTPClient
  http.begin("http://filipe027.pythonanywhere.com" + path);              //Specify request destination
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");    //Specify content-type header
  postData.trim();
  log_debug(postData);
  int httpCode = http.POST(postData);   //Send the request
  String payload = http.getString();    //Get the response payload

  http.end();  //Close connection
  return payload;
}

String get_server_time(){
  HTTPClient http;

  http.begin("http://filipe027.pythonanywhere.com/time/" + WiFi.macAddress() + "/");
  int httpCode = http.GET();
  return http.getString();
  http.end();
}
//endregion

//region UTILITY_FUNCTIONS
void log_debug(String message){
  if (debug) {
    Serial.println(message);
  }
}

void unlock_relay(){
  if(debug == false){
    digitalWrite(15, HIGH);
  }
}

void lock_relay(){
  if(debug == false){
    digitalWrite(15, LOW);
  }
}

bool wifi_connected(){
  return (WiFi.status() == WL_CONNECTED);
}

void connect_to_wifi(){
  WiFi.begin(ssid.c_str(), password.c_str());     //Connect to your WiFi router
  // Wait for connection
  int timeout = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    timeout +=1;
    if(timeout == 25){
      break;
    }
  }
}

String read_rfid(){
  if ( ! mfrc522.PICC_ReadCardSerial()){
        return "";
  }
  //Show UID on serial monitor
  //Serial.println();
  //Serial.print(" UID tag :");
  String content= "";
  byte letter;
  for (byte i = 0; i < mfrc522.uid.size; i++) 
  {
     //Serial.print(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " ");
     //Serial.print(mfrc522.uid.uidByte[i], HEX);
     content.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? " 0" : " "));
     content.concat(String(mfrc522.uid.uidByte[i], HEX));
  }
  content.toUpperCase();
  content = content.substring(1);
  return content;
}

File backup_file;
void sdcard_store_backup(long seconds, String UID){
  backup_file = SD.open("backup.txt", FILE_WRITE);
  backup_file.seek(0);
  backup_file.println(String(seconds));
  backup_file.println(UID);
  backup_file.close();
}

bool sdcard_check_backup(long seconds, String UID){
  backup_file = SD.open("backup.txt", FILE_READ);
  backup_file.seek(0);
  long backup_seconds = backup_file.readStringUntil('\n').toInt();
  String sd_uid = backup_file.readStringUntil('\n');
  sd_uid.trim();
  
  //86400 seconds = 24h
  if( seconds - backup_seconds <= 86400 and UID == sd_uid){
    //log_debug("unlocked by backup");
    return true;
  }
  else{
    //:log_debug("backup denied");
    return false;
  }
}

long rewind_timer = 0;
const int REWIND_TIMEOUT = 60000;
void rewind_locdir_with_timeout(){
  if (millis() - rewind_timer >= REWIND_TIMEOUT){
    location_root.rewindDirectory();
    location_file = location_root.openNextFile();
    if (location_file){
      scanning_location_root = true;
    }
    rewind_timer = millis();
  }
}


void read_ssid(){
  if (SD.exists("ssid.txt")){
    File ssid_file = SD.open("ssid.txt", FILE_READ);
    ssid = ssid_file.readStringUntil('\n');
    //next_line(ssid_file);
    password = ssid_file.readStringUntil('\n');
    ssid.trim();
    password.trim();
  }
}

String syear, smonth, sday, shour, sminute, ssecond;
String get_time_str(){
  now = rtc.now();
  syear = String(now.year());
  if(now.month() < 10){
    smonth = String("0") + String(now.month());
  }
  else{
    smonth = String(now.month());
  }
  if(now.day() < 10){
    sday = String("0") + String(now.day());
  }
  else{
    sday = String(now.day());
  }
  if(now.hour() < 10){
    shour = String("0") + String(now.hour());
  }
  else{
    shour = String(now.hour());
  }
  if(now.minute() < 10){
    sminute = String("0") + String(now.minute());
  }
  else{
    sminute = String(now.minute());
  }
  if(now.second() < 10){
    ssecond = String("0") + String(now.second());
  }
  else{
    ssecond = String(now.second());
  }
  
  return syear + "-" + smonth + "-" + sday + "-" + shour + "-" + sminute + "-" + ssecond ;
  
}
//endregion

//region SD_FUNCTIONS
void grava_cartao_SD(String data)
{
  delay(10);
  //Abre arquivo no SD para gravacao
  file = SD.open("sd04.txt", FILE_WRITE);
  //Le as informacoes de data e hora
  file.println(data);
  file.close();
}

// Informação do data logger, arquivo não será apagado
void sdcard_log_location(String login_id, String position, String time){
  File file = SD.open("LOCLOG.txt", FILE_WRITE);
  file.println("id=" + login_id + "&pos=" + position + "&time=" + time + "&mac=" + mac);
  file.close();
}
  
// Informação do data logger, arquivo não será apagado
void sdcard_log_login(String server_id, String auth, String time){
  File file = SD.open("LINLOG.txt", FILE_WRITE);
  file.println("server_id=" + server_id + "&auth=" + auth + "&time=" + time);
  file.close();
}

void sdcard_log_location_pending(String login_id, String position, String time){
  File file = SD.open("/C/"+ login_id + ".txt", FILE_WRITE);
  file.println("id=" + login_id + "&pos=" + position + "&time=" + time + "&mac=" + mac);
  file.close();
}

void sdcard_upload_location_pending(){
  String data = location_file.readStringUntil('\n');
  log_debug("Localização pendente enviada para o servidor: " + data);
  post_to_url("/post-loc/", data);
}
//endregion 
