
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
#include <Wire.h>
#include <AccelStepper.h>
#include <Adafruit_MotorShield.h>

#define VERSION "acam3.5.0"

Adafruit_MotorShield AFMS(0x60);
Adafruit_StepperMotor *motor1 = AFMS.getStepper(200, 1);
Adafruit_StepperMotor *motor2 = AFMS.getStepper(200, 2);

/* String I/O
 * bufsize is large enough for any valid command in the protocol.
 * The longest command is G:-32768:-32768 (17 bytes including null terminator).
 * Buffer overflow is not guarded against; the host is the only client.
 */
const int bufsize = 32;
char cmd[bufsize];
int len = 0;

/* flags */
bool command_ready = false;
bool is_running = false;
bool shield_ok = false;


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
  long n1, n2;
  /* sscanf return value is not checked; Assume Motors.py sends well-formed commands. */
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
  long n1, n2;
  if (len == 1) {
    n1 = stepper1.currentPosition();
    n2 = stepper2.currentPosition();
    Serial.print("P:");
    Serial.print(n1);
    Serial.print(':');
    Serial.print(n2);
    Serial.print(':');
    Serial.println(is_running);
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
    default:
      Serial.println(cmd);
      break;
  }
  len = 0;
  command_ready = false;
}

void setup() {
  Serial.begin(115200, SERIAL_8N1);
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
