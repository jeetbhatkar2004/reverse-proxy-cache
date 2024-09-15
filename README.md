# Chart Dashboard Application

## Overview

This project is a full-stack web application featuring a Next.js frontend integrated with a Django API backend. The application displays a dashboard with multiple types of charts (Candlestick, Line, Bar, and Pie) that fetch data from the backend.

## Setup Instructions

### Prerequisites

- **Node.js**: Ensure you have Node.js installed (version 16.x or later recommended).
- **Python**: Python 3.8 or later is required.
- **Django** and **Django REST Framework**: For setting up the backend.
- **Virtual Environment**: Recommended for Python dependencies.

### Backend Setup (Django API)

1. **Navigate to the Backend Directory:**

   ```bash
   cd chartfullstack/chartbackend
   python -m venv venv
    source venv/bin/activate  # On Windows, use: venv\Scripts\activate
    pip install django djangorestframework django-cors-headers
    python manage.py migrate
    python manage.py runserver
    cd ../chart-frontend
    npm install
    npm run dev
Project Structure
Next.js Frontend: Handles the UI/UX with a clean and responsive dashboard that fetches data from the backend.
Django Backend: Provides a simple set of APIs with hardcoded data, designed to be easily extendable for future development.
Design Decisions
Component-based Architecture: Each chart type is encapsulated in its own React component for modularity and reusability.
Data Fetching: Data is fetched dynamically from the Django API, ensuring that the frontend remains decoupled and maintainable.
Error Handling: Basic error handling is included to display messages if the API fails to respond.
Thought Process
The primary goal was to demonstrate the integration of a modern frontend framework (Next.js) with a reliable backend (Django).
Focused on clean, maintainable code that can be easily expanded with more complex features, such as state management or additional data visualizations.
Emphasized a straightforward setup to make the application easy to run and understand, providing clear separation between frontend and backend responsibilities.