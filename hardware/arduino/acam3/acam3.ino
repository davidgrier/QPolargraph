
/*
 * Sketch to control stepper motors via serial interface
 *
 * Commands implemented with examples:
 * - Q          : Query software version
 * - V:500:500  : Set motor speeds to 500 steps/second each
 * - A:100:100  : Set motor accelerations to 100 steps/second^2 each
 * - G:-1000:50 : Move motor 1 to position -1000 and motor 2 to 50
 * - S          : Stop
 * - X          : Release motors
 * - P          : Query position of motors
 * - R          : Query whether motors are running
 */

#include <stdio.h>
/* Adafruit Motor Shield v. 2.3 */
#include <Wire.h>
#include <AccelStepper.h>
#include <Adafruit_MotorShield.h>

#define VERSION "acam3.3.2"

Adafruit_MotorShield AFMS(0x60);
Adafruit_StepperMotor *motor1 = AFMS.getStepper(200, 1);
Adafruit_StepperMotor *motor2 = AFMS.getStepper(200, 2);

/* String I/O */
const int bufsize = 32;
char cmd[bufsize];
int len = 0;

/* flags */
bool command_ready = false;
bool is_running = false;
bool shield_ok = false;

/* motor positions (steps) */
long n1 = 0;
long n2 = 0;

/* Motor configuration */
void forwardstep1() {
  motor1->onestep(FORWARD, DOUBLE);
}

void backwardstep1() {
  motor1->onestep(BACKWARD, DOUBLE);
}

void forwardstep2() {
  motor2->onestep(FORWARD, DOUBLE);
}

void backwardstep2() {
  motor2->onestep(BACKWARD, DOUBLE);
}

AccelStepper stepper1(forwardstep1, backwardstep1);
AccelStepper stepper2(forwardstep2, backwardstep2);

void set_target() {
  sscanf(cmd, "G:%ld:%ld", &n1, &n2);
  stepper1.moveTo(n1);
  stepper2.moveTo(n2);
  Serial.println('G');
}

void getset_speed() {
  char *t1, *t2;
  float v1, v2;

  if (len == 1) {
    v1 = stepper1.maxSpeed();
    v2 = stepper2.maxSpeed();
    Serial.print("V:");
    Serial.print(v1);
    Serial.print(':');
    Serial.println(v2);
  } else {
    strtok(cmd, ":");
    t1 = strtok(NULL, ":");
    t2 = strtok(NULL, ":");
    if (t1 == NULL || t2 == NULL) {
      Serial.println("E:V");
      return;
    }
    v1 = atof(t1);
    v2 = atof(t2);
    stepper1.setMaxSpeed(v1);
    stepper2.setMaxSpeed(v2);
    Serial.println('V');
  }
}

void set_acceleration() {
  char *t1, *t2;
  float a1, a2;

  strtok(cmd, ":");
  t1 = strtok(NULL, ":");
  t2 = strtok(NULL, ":");
  if (t1 == NULL || t2 == NULL) {
    Serial.println("E:A");
    return;
  }
  a1 = atof(t1);
  a2 = atof(t2);
  stepper1.setAcceleration(a1);
  stepper2.setAcceleration(a2);
  Serial.println('A');
}

void stop_motors() {
  stepper1.stop();
  stepper2.stop();
  Serial.println('S');
}

void release_motors() {
  motor1->release();
  motor2->release();
  Serial.println('X');
}

void getset_position() {
  if (len == 1) {
    n1 = stepper1.currentPosition();
    n2 = stepper2.currentPosition();
    Serial.print(is_running ? "R:" : "P:");
    Serial.print(n1);
    Serial.print(':');
    Serial.println(n2);
  } else {
    sscanf(cmd, "P:%ld:%ld", &n1, &n2);
    stepper1.setCurrentPosition(n1);
    stepper2.setCurrentPosition(n2);
    Serial.println('P');
  }
}

void query_isrunning() {
  Serial.print("R:");
  Serial.println(is_running);
}

void scan_i2c() {
  bool first = true;
  Serial.print("I:");
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      if (!first) Serial.print(',');
      Serial.print("0x");
      if (addr < 16) Serial.print('0');
      Serial.print(addr, HEX);
      first = false;
    }
  }
  if (first) Serial.print("NONE");
  Serial.println();
}

/* Dispatch commands */
void parse_command() {
  switch (cmd[0]) {
    case 'R':
      query_isrunning();
      break;
    case 'P':
      getset_position();
      break;
    case 'V':
      getset_speed();
      break;
    case 'A':
      set_acceleration();
      break;
    case 'G':
      set_target();
      break;
    case 'S':
      stop_motors();
      break;
    case 'X':
      release_motors();
      break;
    case 'Q':
      Serial.print(VERSION);
      Serial.println(shield_ok ? ":OK" : ":NOSHIELD");
      break;
    case 'I':
      scan_i2c();
      break;
    default:
      Serial.println(cmd);
      break;
  }
  len = 0;
  command_ready = false;
}

void setup() {
  Serial.begin(9600, SERIAL_8N1);
  while (!Serial) {
    ;                           // wait for serial port to connect
  }
  Serial.setTimeout(100);

  Wire.begin();
  for (int attempt = 0; attempt < 5 && !shield_ok; attempt++) {
    shield_ok = AFMS.begin();
    if (!shield_ok) delay(100);
  }
  stepper1.setMaxSpeed(1000.0);
  stepper2.setMaxSpeed(1000.0);
  stepper1.setCurrentPosition(0);
  stepper2.setCurrentPosition(0);
  stepper1.setAcceleration(1000.0);
  stepper2.setAcceleration(1000.0);
}

void loop() {
  if (command_ready) {
    parse_command();
  }
  bool r1 = stepper1.run();
  bool r2 = stepper2.run();
  is_running = r1 || r2;
}

void serialEvent() {
  char c;

  if (Serial.available() > 0 && !command_ready) {
    c = Serial.read();
    if (c == '\n') {
      cmd[len] = '\0';
      command_ready = true;
    } else {
      cmd[len++] = c;
      if (len >= bufsize) {
        len = bufsize - 1;
      }
    }
  }
}
