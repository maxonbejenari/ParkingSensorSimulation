# Real-Time Ultrasonic Parking System

A mechatronic prototype that bridges low-level sensing with a high-level Python dashboard. This project simulates a car's parking assistance system using ultrasonic waves to detect obstacles.

---

##  Project Demonstration
![Parking System Demo](https://youtu.be/jHUYzgg3ygQ) 

---

##  Hardware Architecture & Wiring
The system uses a **CH340-based microcontroller** to interface with an **HC-SR04** sensor. 

### Wiring Diagram
![Wiring Diagram](<img width="794" height="632" alt="Screenshot from 2026-03-28 11-34-43" src="https://github.com/user-attachments/assets/40916281-47e7-488f-bca0-e6d70ca34fdd" />)

| Component | Sensor Pin | Microcontroller Pin | Function |
| :--- | :--- | :--- | :--- |
| **HC-SR04** | VCC | 5V | Power Supply |
| **HC-SR04** | Trig | 9 | Ultrasonic Pulse Trigger |
| **HC-SR04** | Echo | 10 | Echo Signal Reception |
| **HC-SR04** | GND | GND | Ground |

---

##  Software Features
* **Asynchronous GUI:** Built with Python (Tkinter) using **Multithreading** to ensure a smooth 60FPS UI while reading serial data.
* **Smart Radar Visualization:** A dynamic radar arc that changes color (Green/Yellow/Red) and shrinks based on real-time distance.
* **Adaptive Audio Feedback:** Integrated `pygame` audio logic that increases beep frequency as the obstacle gets closer.
* **Firmware:** Optimized C++ code with non-blocking delays for precise distance calculation.

---

##  Installation & Setup

### 1. Hardware Setup
1. Connect the HC-SR04 to the pins as shown in the table above.
2. Plug the CH340 board into your PC via USB.

### 2. Firmware Upload
Note! -> you need to create a Project for C++ arduinio code and upload code on Hardware, it can be ArduinoIDE or PlatformIo
1. Open the `/arduino_hardware` folder in **VSCode + PlatformIO**.
2. Build and Upload the code to your board.
3. **Important:** Close the Serial Monitor in VSCode before running the Python GUI.

### 3. Python Environment
Install the required libraries:
```bash
pip install pyserial Pillow pygame
