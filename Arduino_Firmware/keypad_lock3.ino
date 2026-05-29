// ============================================================
//  Keypad Password Lock
//  Board  : Arduino Nano
//  Keypad : 4x4 matrix (R1-R4 → D2-D5, C1-C4 → D6-D9)
//  White LED : D10 (correct password + keypress flash)
//  Red LED   : D11 (wrong password)
//  Buzzer    : D13
//  Confirm   : D key
//  Clear     : * key
// ============================================================

#include <Keypad.h>

#define WHITE_LED_PIN  10
#define RED_LED_PIN    11
#define BUZZER_PIN     13

const String CORRECT_PASSWORD = "1470";

const byte ROWS = 4;
const byte COLS = 4;

char keys[ROWS][COLS] = {
  { '1', '2', '3', 'A' },
  { '4', '5', '6', 'B' },
  { '7', '8', '9', 'C' },
  { '*', '0', '#', 'D' }
};

byte rowPins[ROWS] = { 2, 3, 4, 5 };
byte colPins[COLS] = { 6, 7, 8, 9 };

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

String inputPassword = "";

void setup() {
  pinMode(WHITE_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN,   OUTPUT);
  pinMode(BUZZER_PIN,    OUTPUT);

  Serial.begin(9600);
  Serial.println("=== Keypad Lock Ready ===");
  Serial.println("Enter password then press D to confirm.");
  Serial.println("Press * to clear your input.");

  blinkLED(WHITE_LED_PIN, 2, 150);
}

void loop() {
  char key = keypad.getKey();
  if (!key) return;

  if (key == '*') {
    inputPassword = "";
    Serial.println("Input cleared.");
    beep(100);
    return;
  }

  if (key == 'D') {
    Serial.print("Entered: ");
    for (int i = 0; i < inputPassword.length(); i++) Serial.print('*');
    Serial.println();

    // ── Cinematic verify blink (both LEDs together) ──
    verifyingAnimation();

    if (inputPassword == CORRECT_PASSWORD) {
      accessGranted();
    } else {
      accessDenied();
    }

    inputPassword = "";
    delay(500);
    while (keypad.getKey()) {}
    return;
  }

  inputPassword += key;

  beep(60);
  delay(80);
  digitalWrite(WHITE_LED_PIN, HIGH);
  delay(120);
  digitalWrite(WHITE_LED_PIN, LOW);

  Serial.print("Key pressed: ");
  Serial.println(key);
  Serial.print("Input so far: ");
  Serial.println(inputPassword);
}

// ── Verifying animation: LEDs alternate one after another ────
void verifyingAnimation() {
  Serial.println("Verifying...");
  tone(BUZZER_PIN, 800, 80);
  for (int i = 0; i < 4; i++) {
    // White first
    digitalWrite(WHITE_LED_PIN, HIGH);
    digitalWrite(RED_LED_PIN,   LOW);
    delay(120);
    // Then red
    digitalWrite(WHITE_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN,   HIGH);
    delay(120);
  }
  // Both off at end
  digitalWrite(WHITE_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN,   LOW);
  noTone(BUZZER_PIN);
  delay(100);
}

// ── Access granted ───────────────────────────────────────────
void accessGranted() {
  Serial.println("ACCESS GRANTED");

  digitalWrite(WHITE_LED_PIN, HIGH);
  successTone();
  delay(3000);
  digitalWrite(WHITE_LED_PIN, LOW);
}

// ── Access denied ─────────────────────────────────────────────
void accessDenied() {
  Serial.println("ACCESS DENIED");

  // Start tone and blink simultaneously
  tone(BUZZER_PIN, 300, 600);
  blinkLED(RED_LED_PIN, 3, 200);
  noTone(BUZZER_PIN);
}

// ── Sound helpers ────────────────────────────────────────────
void beep(int duration) {
  tone(BUZZER_PIN, 1000, duration);
}

void successTone() {
  tone(BUZZER_PIN, 1200, 150); delay(180);
  tone(BUZZER_PIN, 1800, 250); delay(280);
  noTone(BUZZER_PIN);
}

// ── LED helper ────────────────────────────────────────────────
void blinkLED(int pin, int times, int ms) {
  for (int i = 0; i < times; i++) {
    digitalWrite(pin, HIGH);
    delay(ms);
    digitalWrite(pin, LOW);
    delay(ms);
  }
}