#include <ESP8266WiFi.h>      // For ESP8266 WiFi
#include <ESP8266WebServer.h> // Web server library
#include <SoftwareSerial.h>   // For GPS communication
#include <TinyGPS++.h>        // GPS library

// Motor control pins
int motorPin1 = D0;
int motorPin2 = D1;
int motorPin3 = D2;
int motorPin4 = D3;

// Wi-Fi credentials
const char *ssid = "TRIANGLES3.0";
const char *password = "Podapanni";

// GPS Setup
SoftwareSerial ss(D5, D6); // RX, TX pins for GPS module
TinyGPSPlus gps;

// Web Server Setup
ESP8266WebServer server(80);

// Variables for GPS location
double latitude = 13.356575383985113;
double longitude = 80.14301631035832;


// Motor control functions
void moveForward() {
  analogWrite(motorPin1, 75);
  analogWrite(motorPin2, 0);
  analogWrite(motorPin3, 0);
  analogWrite(motorPin4, 75);
}

void moveBackward() {
  analogWrite(motorPin1, 0);
  analogWrite(motorPin2, 75);
  analogWrite(motorPin3, 75);
  analogWrite(motorPin4, 0);
}

void turnLeft() {
  analogWrite(motorPin1, 0);
  analogWrite(motorPin2, 200);
  analogWrite(motorPin3, 0);
  analogWrite(motorPin4, 200);
  delay(700);  
  stopCar();
}

void turnRight() {
  analogWrite(motorPin1, 200);
  analogWrite(motorPin2, 0);
  analogWrite(motorPin3, 200);
  analogWrite(motorPin4, 0);
  delay(700);  
  stopCar();
}

void stopCar() {
  analogWrite(motorPin1, 0);
  analogWrite(motorPin2, 0);
  analogWrite(motorPin3, 0);
  analogWrite(motorPin4, 0);
}

// Handle commands from webpage
void handleControl() {
  String command = server.arg("command");

  if (command == "forward") moveForward();
  else if (command == "backward") moveBackward();
  else if (command == "left") turnLeft();
  else if (command == "right") turnRight();
  else if (command == "stop") stopCar();

  server.send(200, "text/plain", "OK");
}

// Send GPS data as JSON
void handleGPS() {
  if (gps.location.isUpdated()) {
    latitude = gps.location.lat();
    longitude = gps.location.lng();
  }

  String gpsData = "{\"latitude\": " + String(latitude, 6) + ", \"longitude\": " + String(longitude, 6) + "}";
  server.send(200, "application/json", gpsData);
}

// Webpage for controlling the car and viewing GPS location
void handleLocation() {
  String html = "<html><head>";
  html += "<style>";
  html += "body {font-family: Arial, sans-serif; text-align: center;}";
  html += "button {font-size: 18px; padding: 10px 20px; margin: 5px;}";
  html += "#controls {display: grid; grid-template-columns: auto auto auto; gap: 10px; justify-content: center; align-items: center;}";
  html += "</style>";
  
  html += "<script>";
  html += "function sendCommand(command) {";
  html += "  document.getElementById('commandDisplay').innerText = 'Command: ' + command;";
  html += "  var xhr = new XMLHttpRequest();";
  html += "  xhr.open('GET', '/control?command=' + command, true);";
  html += "  xhr.send();";
  html += "}";

  // GPS tracking update function
  html += "function updateGPS() {";
  html += "  var xhr = new XMLHttpRequest();";
  html += "  xhr.open('GET', '/gps', true);";
  html += "  xhr.onload = function() {";
  html += "    if (xhr.status == 200) {";
  html += "      var gpsData = JSON.parse(xhr.responseText);";
  html += "      document.getElementById('gpsLocation').innerText = 'Lat: ' + gpsData.latitude + ', Lng: ' + gpsData.longitude;";
  html += "      document.getElementById('mapLink').href = 'https://www.google.com/maps?q=' + gpsData.latitude + ',' + gpsData.longitude;";
  html += "    }";
  html += "  };";
  html += "  xhr.send();";
  html += "}";
  html += "setInterval(updateGPS, 5000);"; // Refresh GPS data every 5 seconds

  html += "window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;";
  html += "const recognition = new SpeechRecognition();";
  html += "recognition.continuous = true;";
  html += "recognition.lang = 'en-US';";
  html += "recognition.onresult = function(event) {";
  html += "  let transcript = event.results[event.results.length - 1][0].transcript.toLowerCase();";
  html += "  if (transcript.includes('forward')) sendCommand('forward');";
  html += "  else if (transcript.includes('backward')) sendCommand('backward');";
  html += "  else if (transcript.includes('left')) sendCommand('left');";
  html += "  else if (transcript.includes('right')) sendCommand('right');";
  html += "  else if (transcript.includes('stop')) sendCommand('stop');";
  html += "};";
  html += "function startListening() { recognition.start(); }";
  html += "function stopListening() { recognition.stop(); }";

  html += "</script>";
  html += "</head><body>";

  html += "<h2>Car Control</h2>";
  html += "<h2 id='commandDisplay'>Command: Waiting...</h2>";

  html += "<div id='controls'>";
  html += "<button style='grid-column: 2;' onclick='sendCommand(\"forward\")'>Forward</button>";
  html += "<button style='grid-column: 1;' onclick='sendCommand(\"left\")'>Left</button>";
  html += "<button style='grid-column: 3;' onclick='sendCommand(\"right\")'>Right</button>";
  html += "<button style='grid-column: 2;' onclick='sendCommand(\"backward\")'>Backward</button>";
  html += "</div>";

  html += "<br><button onclick='sendCommand(\"stop\")'>Stop</button>";
  html += "<br><br>";
  html += "<button onclick='startListening()'>Start Voice Control</button>";
  html += "<button onclick='stopListening()'>Stop Voice Control</button>";

  // GPS Display
  html += "<h3>GPS Location</h3>";
  html += "<p id='gpsLocation'>Fetching location...</p>";
  html += "<a id='mapLink' href='#' target='_blank'>View on Google Maps</a>";

  html += "</body></html>";
  server.send(200, "text/html", html);
}

void setup() {
  Serial.begin(115200);
  ss.begin(9600);

  pinMode(motorPin1, OUTPUT);
  pinMode(motorPin2, OUTPUT);
  pinMode(motorPin3, OUTPUT);
  pinMode(motorPin4, OUTPUT);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  server.on("/", HTTP_GET, handleLocation);
  server.on("/control", HTTP_GET, handleControl);
  server.on("/gps", HTTP_GET, handleGPS); // New GPS route

  server.begin();
  Serial.println("Web server started");
}

void loop() {
  while (ss.available() > 0) {
    gps.encode(ss.read());
  }
  server.handleClient();
}
