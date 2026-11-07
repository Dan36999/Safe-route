SafeRoute - Community Safety Route Planner

CPU4106 Group Project

SafeRoute is a community-focused web application designed to help people identify safer travel routes and report hazards within their local area. The platform allows users to view reported incidents, contribute safety information, and assess route safety using community-generated data.

The project supports UN Sustainable Development Goal 11: Sustainable Cities and Communities by promoting safer and more informed travel within local communities.

Features
User registration and login
Community hazard reporting
Interactive safety map
Route safety assessment
User dashboard with recent activity
Mobile-friendly responsive design
Technology Stack
Backend: Python, Flask
Frontend: HTML, CSS, JavaScript, Bootstrap 5
Templates: Jinja2
Database: MySQL
Mapping: Leaflet.js & OpenStreetMap
Project Structure
SafeRoute/
├── app.py
├── config.py
├── requirements.txt
├── database/
│   └── saferoute.sql
├── templates/
├── static/
│   ├── css/
│   └── js/
└── README.md

Installation
1. Create the Database
mysql -u root -p < database/saferoute.sql

2. Configure MySQL

Edit config.py:

MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "your-password"
MYSQL_DB = "saferoute"

3. Install Dependencies
pip install -r requirements.txt

4. Run the Application
python app.py

5. Open in Browser
http://127.0.0.1:5000

Database

The system stores data across three core tables:

Users - account information
Reports - community hazard reports
Routes - route searches and safety scores

Relationships are maintained through the user ID, allowing reports and route searches to be linked to individual users.

Safety Score

SafeRoute calculates a route safety score using nearby reported incidents.

Safety Score = 100 - (Incidents × 5)

Score	Rating90-100	Safe
70-89	Moderate Risk
0-69	High Risk

The score provides an indication of route safety based on community-reported incidents and should be treated as guidance rather than an official assessment.

Demonstration Flow
Register an account
Log in
View the dashboard
Submit a hazard report
View community reports
Explore the safety map
Search for a route
Review the route safety score
Limitations

This project was developed as a university prototype.

No live GPS navigation
No third-party routing services
Safety scores are based on community reports
Route assessments are estimates only
Accessibility
Responsive design for mobile and desktop devices
Keyboard-accessible navigation
Accessible form labels and controls
Clear colour contrast throughout the interface
Authors

Developed as part of the CPU4106 Level 4 Computing Group Project.

This version looks much more like a professional GitHub README and is what I would submit for a university prototype. It removes a lot of the "assignment report" content while keeping everything a marker, lecturer, or GitHub viewer actually needs.
