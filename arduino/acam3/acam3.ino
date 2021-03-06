
/*
 * Sketch to control stepper motors via serial interface
 *
 * Commands implemented with examples:
 * - Q : Query software version
 * - V:500 : Set motor speed to 500 steps/second
 * - A:100 : Set motor acceleration to 100 steps/second^2
 * - G:-1000:50 : Move motor 1 to position -1000 and motor 2 to 50
 * - S : Stop
 * - X : Release motors
 * - P : Query position of motors
 * - R : Query whether motors are running
 */

#include <stdio.h>
/* Adafruit Motor Shield v. 2.3 */
#include <Wire.h>
#include <AccelStepper.h>
#include <Adafruit_MotorShield.h>

#define VERSION "acam 3.1.0"

Adafruit_MotorShield AFMS(0x60);
Adafruit_StepperMotor *motor1 = AFMS.getStepper(200, 1);
Adafruit_StepperMotor *motor2 = AFMS.getStepper(200, 2);

/* String I/O */
const int bufsize = 32;
char cmd[bufsize];    // command string
int len = 0;

/* flags */
boolean command_ready = false; // command string received
boolean is_running = false;    // true if steppers are running
boolean is_running_1, is_running_2;

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
  char *token;
  const char delim = ':';
  float v1, v2;
  
  if (len == 1) {
    v1 = stepper1.maxSpeed();
    v2 = stepper2.maxSpeed();
    Serial.print("V:");
    Serial.print(v1);
    Serial.print(':');
    Serial.println(v2);
  }
  else {
    token = strtok(cmd, &delim);
    token = strtok(NULL, &delim);
    v1 = atof(token);
    token = strtok(NULL, &delim);
    v2 = atof(token);
    stepper1.setMaxSpeed(v1);
    stepper2.setMaxSpeed(v2);
    Serial.println('V');
  }
}

void set_acceleration() {
  char *token;
  const char delim = ':';
  float a1, a2;
  
  token = strtok(cmd, &delim);
  token = strtok(NULL, &delim);
  a1 = atof(token);
  token = strtok(NULL, &delim);
  a2 = atof(token);
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

void query_identity() {
  Serial.println("acam3");
}

void getset_position() {
  if (len == 1) {
    n1 = stepper1.currentPosition();
    n2 = stepper2.currentPosition();
    Serial.print((is_running) ? "R:" : "P:");
    Serial.print(n1);
    Serial.print(':');
    Serial.println(n2);
  }
  else {
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
      Serial.println(VERSION);
      break;
    default:
      Serial.println(cmd);
      break;
  }
  len = 0;
  command_ready = false;
}

void setup() {
    Serial.begin(9600, SERIAL_8N1); // Serial Port at 9600 baud
    while (!Serial) {
      ;                     // Wait for serial port to connect
    }
    Serial.setTimeout(100);
    
    AFMS.begin();           // AccelStepper setup
    stepper1.setMaxSpeed(1000.0);
    stepper2.setMaxSpeed(1000.0);
    stepper1.setCurrentPosition(0);	
    stepper2.setCurrentPosition(0);
    stepper1.setAcceleration(1000.);
    stepper2.setAcceleration(1000.);
}

void loop() {
    if (command_ready) {
      parse_command();
    }
    is_running_1 = stepper1.run();
    is_running_2 = stepper2.run();
    is_running = is_running_1 or is_running_2;
}

void serialEvent() {
  char c;

  if ((Serial.available() > 0) or (command_ready == false)) {
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
