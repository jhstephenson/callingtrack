# CallingTrack

A Django web application for managing and tracking church callings, designed to streamline the calling process from proposal to completion.

## Overview

CallingTrack helps church organizations manage their calling processes by providing:
- Dashboard with active callings overview
- Comprehensive calling status tracking
- Unit and organization management
- Position management with requirements
- User-friendly interface with filtering and search capabilities

## Features

- **Dashboard**: Overview of active callings with quick access to edit forms
- **Calling Management**: Create, edit, and track callings through their lifecycle
- **Status Tracking**: Monitor callings from pending through completion
- **Organization Structure**: Manage units, organizations, and positions
- **User Authentication**: Secure access with role-based permissions
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package installer)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jhstephenson/callingtrack.git
   cd CallingTrack
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   - Copy `.env.example` to `.env`
   - Update database and other settings as needed

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

8. **Access the Application**
   - Open your browser to `http://localhost:8000`
   - Login with your superuser credentials

## Project Structure

```
CallingTrack/
├── callings/           # Main application
│   ├── models.py       # Data models
│   ├── views.py        # View logic
│   ├── forms.py        # Form definitions
│   ├── urls.py         # URL patterns
│   └── templates/      # HTML templates
├── callingtrack/       # Project settings
├── static/            # Static files (CSS, JS, images)
├── media/             # User uploaded files
├── requirements.txt   # Python dependencies
└── manage.py         # Django management script
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please check the documentation in the application or contact the development team.
