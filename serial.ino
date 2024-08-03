const int ledPin = 13;            // LED connected to digital pin 13
const int motorPin1 = 9;          // Motor driver input pin 1
const int motorPin2 = 10;         // Motor driver input pin 2
const int motorEnablePin = 11;    // Motor driver enable pin

bool ledState = false;            // LED state
bool motorState = false;          // Motor state

unsigned long alertStartTime = 0; // Variable to store alert start time

void setup() {
  pinMode(ledPin, OUTPUT);        // Set the LED pin as an output
  pinMode(motorPin1, OUTPUT);     // Set the motor input pins as outputs
  pinMode(motorPin2, OUTPUT);
  pinMode(motorEnablePin, OUTPUT);// Set the motor enable pin as an output
  digitalWrite(ledPin, LOW);      // Ensure LED is initially off
  digitalWrite(motorPin1, HIGH);   // Ensure motor is initially off
  digitalWrite(motorPin2, HIGH);
  digitalWrite(motorEnablePin, HIGH); // Disable the motor initially
  Serial.begin(9600);             // Initialize serial communication
}

void loop() {
  if (Serial.available() > 0) {   // Check if data is available to read from serial
    char receivedChar = Serial.read();  // Read the incoming byte
    if (receivedChar == 'd') {     // If 'd' is received from Python
      digitalWrite(ledPin, HIGH);  // Turn on the LED
      ledState = true;
      digitalWrite(motorPin1, LOW);   // Ensure motor is off
      digitalWrite(motorPin2, LOW);
      digitalWrite(motorEnablePin, LOW);
    
      alertStartTime = millis();    // Record alert start time
    } else if (receivedChar == 'o') { // If 'o' is received from Python
      digitalWrite(ledPin, LOW);    // Turn off the LED
      ledState = false;
    }
  }

  // Check if alert has been active for more than 10 seconds and turn off motor
  if (ledState && millis() - alertStartTime >= 10000) {
    delay(1500);
    digitalWrite(ledPin, LOW);      // Turn off the LED
    ledState = false;
    digitalWrite(motorPin1, HIGH);   // Ensure motor is initially off
    digitalWrite(motorPin2, HIGH);
    digitalWrite(motorEnablePin, HIGH);
    
    motorState = false;
  }
}