# **Product Requirement Document (PRD)**

Project Name: Focus Dashboard CLI

Version: 1.0

Status: Approved for Development

Date: January 8, 2026

---

## **1\. Executive Summary**

### **1.1 Product Overview**

The Focus Dashboard CLI is a terminal-based "Head-Up Display" (HUD) designed to improve productivity, health, and focus for computer-centric workers (developers, writers, students). It runs in a dedicated terminal window/workspace, providing essential utilities without requiring the user to switch context to a GUI browser or heavy application.

It combines task management (The "Big 3"), health tracking (Water & Posture), environmental control (Focus Noise), and time management (Pomodoro) into a single, cohesive Text User Interface (TUI).

### **1.2 The Problem**

* **Context Switching:** Users often lose focus when opening a browser to check the weather, track time, or log tasks.  
* **Health Neglect:** Computer users often forget to drink water or look away from the screen, leading to fatigue and "computer vision syndrome."  
* **Complexity:** Existing dashboards are often bloated, resource-heavy Electron apps, or difficult-to-configure Linux widgets (like Conky).

### **1.3 The Solution**

A Python-based, cross-platform TUI application using the Textual library. It offers:

* **Low Friction:** Keyboard-centric controls.  
* **Low Resource Usage:** Minimal CPU/RAM footprint compared to browser apps.  
* **Aesthetic:** A "Retro/Cyberpunk" aesthetic using ASCII art and borders, appealing to the "ricing" community.

---

## **2\. User Personas & Use Cases**

### **2.1 Primary Persona: "The Deep Worker"**

* **Profile:** A software developer or systems administrator who spends 8+ hours a day in a terminal environment.  
* **Needs:** Wants to keep their hands on the keyboard. Values aesthetics ("cool factor") but demands utility.  
* **Pain Point:** Gets distracted by notifications when opening a web browser for simple tasks.

### **2.2 Secondary Persona: "The Student"**

* **Profile:** Someone studying for exams needing structured focus time.  
* **Needs:** A rigid timer system (Pomodoro) and background noise to block out distractions in a library or dorm.

---

## **3\. Technical Architecture**

### **3.1 Tech Stack**

* **Core Language:** Python 3.10+  
* **UI Framework:** Textual (CSS-grid style layout for TUI, async event loop).  
* **Audio Engine:** playsound or simpleaudio (Cross-platform compatibility layer).  
* **Data Storage:** Local JSON (config.json).  
* **Distribution:** PyPI package (pip install) or Standalone Executable.

### **3.2 System Requirements**

* **OS:** Windows 10/11, macOS, Linux (Debian/Arch/Fedora).  
* **Terminal:** Any standard terminal emulator (Alacritty, iTerm2, Windows Terminal, GNOME Terminal) supporting ANSI colors.  
* **Dependencies:** Python standard library \+ textual \+ audio driver dependencies.

### **3.3 File Structure**

The application will act as a self-contained package.

Plaintext

/focus-dashboard  
│  
├── main.py              \# Entry point & Async Event Loop  
├── layout.tcss          \# Textual CSS (styling the UI)  
├── config.json          \# User settings & persistence  
├── assets/  
│   └── brown\_noise.wav  \# Bundled audio file  
├── modules/  
│   ├── audio\_manager.py \# Handles looping and relative paths  
│   ├── data\_handler.py  \# Reads/Writes JSON  
│   ├── ui\_widgets.py    \# Individual widget components  
│   └── weather\_api.py   \# Fetches weather data  
└── README.md

---

## **4\. Functional Specifications**

### **4.1 Setup & Onboarding Logic**

The application features a "Two-Phase" setup process to ensure a tailored experience without repetitiveness.

#### **4.1.1 Phase A: Global Setup (First Run Only)**

* **Trigger:** Absence of config.json file.  
* **User Flow:**  
  1. **Welcome Screen:** ASCII banner introduction.  
  2. **Unit Selection:** Prompt user for Imperial (oz/F) or Metric (ml/C).  
  3. **Container Setup:** "What is the size of your water vessel?" (Input: Integer).  
  4. **Location:** "Enter City Name" (for Weather API).  
  5. **Audio Config:** System detects bundled brown\_noise.wav. User confirms.  
  6. **Output:** Creates config.json with setup\_complete: true.

#### **4.1.2 Phase B: Daily Routine (New Day Detection)**

* **Trigger:** App launch where last\_login\_date \!= current\_date.  
* **User Flow:**  
  1. **Reset:** Internal water\_count variable reset to 0\.  
  2. **Task Prompt:** "Good Morning. Identify your 'Big 3' tasks for today."  
     * *Input:* 3 text fields.  
     * *Skip Option:* User can press Enter on empty fields to skip.  
  3. **Water Goal Check:** "Your goal is {X}. Change for today? (y/n)".  
  4. **Momentum Builder:** "Start Pomodoro Timer immediately? (y/n)".  
* **Persistence:** Updates last\_login\_date in config.json.

#### **4.1.3 Phase C: Session Resume (Same Day)**

* **Trigger:** App launch where last\_login\_date \== current\_date.  
* **Action:** Bypasses all prompts. Loads dashboard with current day's progress preserved.

---

### **4.2 Dashboard Widgets & Features**

#### **4.2.1 The "Big 3" Task List**

* **Display:** Top-left quadrant. Three distinct rows.  
* **State:**  
  * Empty: Displays placeholder text "Task 1...".  
  * Active: Displays user text.  
  * Completed: Strikethrough text styling (toggled via checkmark).  
* **Logic:** Tasks persist only for the current date. They do not roll over (to encourage daily reprioritization).

#### **4.2.2 Pomodoro Timer**

* **Display:** Center prominence. Large ASCII or Bold Text numerals (MM:SS).  
* **Default Settings:** 25 minutes (Focus) / 5 minutes (Break).  
* **Controls:**  
  * P: Start/Pause.  
  * R: Reset.  
* **Notifications:** Visual flash of terminal screen when timer hits 00:00. (No audio beep to avoid jarring the user, unless toggleable).

#### **4.2.3 Audio Manager (Focus Noise)**

* **Asset:** brown\_noise.wav (bundled).  
* **Logic:**  
  * **Relative Pathing:** Code must dynamically determine the script's execution directory to locate the .wav file, preventing File Not Found errors on different machines.  
  * **Looping:** The audio player must detect end-of-file and restart immediately (gapless playback preferred).  
* **Controls:**  
  * N: Toggle On/Off.  
* **UI Indicator:** Small speaker icon 🔈 or text \[NOISE: ON\] in the status bar.

#### **4.2.4 Water Tracker**

* **Display:** Right column.  
  * Visual: A vertical or horizontal progress bar \[|||||.....\].  
  * Text: Current / Goal (e.g., "32 / 64 oz").  
* **Input:**  
  * W: Adds 1x "Container Size" (defined in Setup).  
  * Shift+W (optional): Undo last add.  
* **Gamification:** Bar turns Green when goal is met.

#### **4.2.5 The "Brain Dump"**

* **Display:** Bottom-center text area.  
* **Function:** A scratchpad for transient thoughts.  
* **Persistence:** Saves to a local text file (notes.txt) or config.json instantly on keystroke to prevent data loss if the app crashes.

#### **4.2.6 The "Parking Lot"**

* **Display:** List format.  
* **Function:** Specialized input for URLs.  
* **Interaction:** User pastes a link. It is added to a list.  
* **Action:** Selecting a link and pressing Enter opens it in the system's default web browser.

#### **4.2.7 Health Nag System (The "Vitals")**

* **Stand Up Alarm:** Uses system time. Every 60 minutes of *app runtime*, displays a modal or flashing text: "STAND UP."  
* **20-20-20 Rule:** Every 20 minutes, displays a subtle toast notification: "Look 20ft away."  
* **Override:** User can silence these in settings.

#### **4.2.8 Environment Widgets**

* **Weather:**  
  * API: OpenMeteo (Free, no API key required).  
  * Refresh Rate: Every 30 minutes (to avoid rate limiting).  
  * Display: Temperature \+ Condition (e.g., "Rain, 65°F").  
* **System Vitals:**  
  * Uses psutil library.  
  * Displays CPU % and Battery %.

---

## **5\. User Interface (UI) Design**

### **5.1 Layout Philosophy**

* **Grid System:** The interface uses a 3-column CSS grid.  
  * **Col 1 (Planning):** Big 3, Habits.  
  * **Col 2 (Focus):** Timer, Brain Dump, Parking Lot.  
  * **Col 3 (Bio/Env):** Water, Weather, Vitals.  
* **Responsiveness:**  
  * **Standard Mode:** Full ASCII borders, padding, and art.  
  * **Compact Mode:** Triggered if terminal width \< 80 chars. Hides decorative borders, stacks columns vertically or simplifies to tabbed view.

### **5.2 Input Mapping (Keybindings)**

The app is keyboard-first. Mouse support is enabled but secondary.

| Key | Context | Action |
| :---- | :---- | :---- |
| Tab | Global | Cycle focus between widgets (Big 3 \-\> Dump \-\> Parking Lot). |
| N | Global | Toggle Brown Noise (On/Off). |
| W | Global | Add Water (1 unit). |
| P | Global | Toggle Pomodoro (Start/Pause). |
| R | Global | Reset Pomodoro. |
| Q | Global | Quit Application (Auto-save). |
| ? | Global | Show Help Modal. |

### **5.3 Aesthetics**

* **Theme:** "Retro Terminal."  
* **Colors:** High contrast. Green/Amber text on Black background.  
* **Typography:** Monospace only. Headers handled via ASCII art libraries (like pyfiglet if size permits, otherwise standard bold text).

---

## **6\. Data Strategy**

### **6.1 Schema: config.json**

The configuration file is the single source of truth.

JSON

{  
  "user\_profile": {  
    "city": "Seattle",  
    "unit\_system": "imperial",  
    "container\_size": 16,  
    "daily\_water\_goal": 64  
  },  
  "app\_settings": {  
    "audio\_enabled": true,  
    "nag\_stand\_up": true,  
    "nag\_eye\_strain": true  
  },  
  "daily\_state": {  
    "last\_login\_date": "2026-01-08",  
    "current\_water\_intake": 32,  
    "tasks": \[  
      {"id": 1, "text": "Fix API bug", "done": false},  
      {"id": 2, "text": "Write documentation", "done": true},  
      {"id": 3, "text": "", "done": false}  
    \],  
    "habit\_streak": {  
      "code": true,  
      "no\_sugar": false  
    }  
  },  
  "persistent\_data": {  
    "brain\_dump\_content": "Remember to call mom...",  
    "parking\_lot\_links": \["https://github.com/example"\]  
  }  
}

### **6.2 Data Integrity**

* **Save Triggers:** Data is saved on:  
  1. Application Quit.  
  2. Any "Input" event (typing in Brain Dump).  
  3. Every 5 minutes (Auto-save background task).  
* **Corruption Handling:** If config.json is unreadable, the app renames it to config.backup.json and initiates the "Phase A" setup again.

---

## **7\. Risks & Mitigation Strategies**

### **7.1 Cross-Platform Audio**

* **Risk:** Audio drivers vary wildly between Linux (ALSA/Pulse), Mac (CoreAudio), and Windows. playsound is known to be buggy on some modern Python versions.  
* **Mitigation:**  
  1. Use pygame (headless) as a robust fallback if playsound fails.  
  2. Implement a "Silent Mode" that automatically engages if audio drivers fail to load, preventing the app from crashing.

### **7.2 Terminal Sizing**

* **Risk:** User opens the app in a tiny VS Code integrated terminal, breaking the layout.  
* **Mitigation:** Implement a on\_resize event handler. If width \< 60 or height \< 20, clear the screen and display a simple message: "Terminal too small. Please resize." or switch to a "Mobile View" vertical scroll layout.

### **7.3 Dependency Management**

* **Risk:** Textual updates frequently and breaks API compatibility.  
* **Mitigation:** Pin exact versions in requirements.txt (e.g., textual==0.40.0).

---

## **8\. Implementation Roadmap**

### **Phase 1: Skeleton & Setup (Days 1-2)**

* Initialize Git repository.  
* Create file structure.  
* Implement Phase A (Global Setup) and Phase B (Daily Logic) scripts.  
* Verify JSON reading/writing.

### **Phase 2: Core UI Layout (Days 3-4)**

* Build the Textual App class.  
* Define CSS Grid layout (layout.tcss).  
* Create placeholder widgets for all sections (static text).

### **Phase 3: Widget Logic (Days 5-7)**

* Connect "Water" keybind (W) to the progress bar.  
* Build the Pomodoro timer loop (async).  
* Implement the "Big 3" input fields and checkbox logic.

### **Phase 4: Audio & Polish (Days 8-9)**

* Integrate Audio Player with threading/async to prevent UI freezing.  
* Implement loop logic for Brown Noise.  
* Add ASCII art headers and borders.  
* Responsive design checks.

### **Phase 5: Testing & Packaging (Day 10\)**

* Test on Windows, Mac, and Linux VM.  
* Verify "New Day" reset logic works by manually manipulating the JSON date.  
* Write README.md with installation instructions.

---

## **9\. Future Considerations (Post-V1)**

* **Google Calendar Sync:** Fetch first meeting of the day.  
* **Themes:** Allow user to switch color schemes (Cyberpunk, Vaporwave, Matrix).  
* **Statistics:** A command focus \--stats to show a graph of water intake and focus hours over the last month.