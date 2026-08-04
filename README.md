# 🚗 Rido - Carpooling Web Application

Rido is a carpooling web application that I built as my graduation project using Flask and MySQL. The main aim of this project is to make ride sharing simple and convenient. Users can post rides, search for available rides, and book seats. Drivers can manage booking requests, while the admin can manage users, rides, and bookings from a separate dashboard.

This project helped me understand how a full-stack web application works, from designing the database to building the frontend and backend.

---

## Features

### User

- Register and Login
- Secure password storage
- Search rides
- Post rides
- Book rides
- Cancel bookings
- View My Booked Rides
- View My Posted Rides
- Manage booking requests
- View profile

### Admin

- Admin Dashboard
- View all users
- View all rides
- View all bookings
- Search records
- Print reports

### Other

- Chatbot
- Responsive design
- Session management
- Password hashing

---

## Technologies Used

- Python
- Flask
- MySQL
- HTML
- CSS
- JavaScript
- Git & GitHub

---

## Project Structure

```
Rido/
│
├── static/
├── templates/
├── app.py
├── database.py
├── config.py
├── requirements.txt
├── README.md
└── .env.example
```

---

## How to Run

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/Rido.git
```

### 2. Move into the project folder

```bash
cd Rido
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate it

Windows

```bash
venv\Scripts\activate
```

### 5. Install the required packages

```bash
pip install -r requirements.txt
```

### 6. Create a `.env` file

Example:

```
SECRET_KEY=your_secret_key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=carpool
DB_PORT=3306
```

### 7. Import the database

Create the MySQL database using the SQL script included in the project.

### 8. Run the project

```bash
python app.py
```

Open:

```
http://127.0.0.1:5000
```

---

## Database

The project uses three tables:

- Users
- Rides
- Bookings

These tables are connected using foreign keys.

For admin:
UPDATE users
SET role='admin'
WHERE email='admin@gmail.com';

---

## What I Learned

While building this project I learned:

- Flask framework
- MySQL database integration
- Authentication and session management
- Password hashing
- CRUD operations
- Responsive web design
- Git and GitHub
- Project organization

---

## Future Improvements

Some features I would like to add in the future are:

- Google Maps integration
- Online payment gateway
- Further email notifications
- Ride ratings and reviews
- OTP verification
- Live ride tracking

---

## Screenshots

### Home Page

![Home](screenshots/Home_Page.png)

---

### Search Ride

![Search Ride](screenshots/Search_Ride.png)

---

### Post Ride

![Post Ride](screenshots/Post_Ride.png)

---

### Ride Booking

![Ride Booking](screenshots/Ride_Booking.png)

---

### Admin Dashboard

![Admin Dashboard](screenshots/Admin_Dashboard.png)

---

### Admin Users

![Admin Users](screenshots/Admin_Users.png)

---

### Admin Rides

![Admin Rides](screenshots/Admin_Rides.png)

---

### Admin Bookings

![Admin Bookings](screenshots/Admin_Bookings.png)

---

GitHub: https://github.com/Areen1011

LinkedIn: www.linkedin.com/in/areen-mulani-4812bb382

---

Thank you for checking out my project! 😊