# Attendance System

A **Cloud-based Attendance Tracking System** designed to automate record-keeping and simplify attendance management for organizations.  
This project is built with **Flask** (Python), **MySQL**, and deployed on **AWS EC2 (Ubuntu 22.04)** using **Nginx** and **Gunicorn** for production.

---

## 🚀 Features
- 📊 **Automated Attendance Tracking** – Efficiently records and manages attendance data.
- ☁ **Cloud Deployment** – Hosted on AWS EC2 for accessibility from anywhere.
- 🔐 **Secure Login** – User authentication for teachers/admins.
- 🗄 **Database Integration** – MySQL database for storing and retrieving records.
- ⚡ **Fast & Scalable** – Optimized with Nginx and Gunicorn.
- 📱 **Responsive UI** – Works on both desktop and mobile devices.

---

## 🛠 Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL
- **Server:** AWS EC2 (Ubuntu 22.04)
- **Production Setup:** Nginx, Gunicorn
- **Version Control:** Git & GitHub

---

## ⚙️ Deployment Steps (AWS EC2 Ubuntu 22.04)
1. **Launch EC2 Instance** – Ubuntu 22.04 LTS, allow ports 22 & 80.
2. **SSH Connect**  
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-ip

## In Terminal
- sudo apt update && sudo apt upgrade -y
- sudo apt install python3 python3-pip python3-venv mysql-server nginx -y

## Enable & start:
- sudo systemctl start attendance
- sudo systemctl enable attendance

## 🏷 Author
Ayush Kumar Sharma
Project developed as part of the 2025 Cloud Computing Internship – Pinnacle Lab.

