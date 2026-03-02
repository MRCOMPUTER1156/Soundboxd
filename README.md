YouTube Video Rating Platform

A Django-based web application that allows users to search for YouTube videos and rate them.
The platform stores video entries and user ratings in a relational database, providing a structured interface for content evaluation.

Features

Search for YouTube videos

Store selected videos in the database

Rate videos using a scoring system

View saved videos and ratings

Admin panel for content management

Clean Django MVC architecture

🛠 Tech Stack

Python 3

Django

SQLite (default database)

HTML (Django Templates)

CSS (Static files)

Project Structure
musicrate/
│
├── manage.py
├── musicrate/        # Main project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── videos/           # Main application
    ├── models.py
    ├── views.py
    ├── forms.py
    ├── urls.py
    ├── admin.py
    ├── templates/
    └── static/

    
⚙️ Installation

1 Clone the repository
git clone https://github.com/MRCOMPUTER1156/Soundboxd.git
cd Soundboxd/musicrate
2 Create and activate a virtual environment

Windows:

python -m venv venv
venv\Scripts\activate

macOS / Linux:

python3 -m venv venv
source venv/bin/activate
3️ Install dependencies
pip install django
4️ Apply migrations
python manage.py migrate
5️ Run the development server
python manage.py runserver

Open in browser:

http://127.0.0.1:8000/
🔐 Admin Panel

Create a superuser:

python manage.py createsuperuser

Access:

http://127.0.0.1:8000/admin/


Future Improvements

Integration with YouTube Data API

User authentication system

Like / Dislike system

Sorting and filtering by rating

Pagination

REST API version

Cloud deployment (Render / Railway)


License

This project is intended for educational and portfolio purposes.
