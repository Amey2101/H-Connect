# H-Connect

## Healthcare & Emergency Ambulance Backend System

H-Connect is a backend system designed to support healthcare and emergency ambulance coordination. The project provides a REST API for managing healthcare-related data and services, with a focus on reliable backend architecture, database integration, and cloud deployment.

The application was built using **Python, FastAPI, SQLAlchemy, PostgreSQL, and AWS** and deployed on an AWS EC2 instance with Nginx.

---

## Features

- RESTful API built with FastAPI
- Healthcare and emergency-service backend functionality
- PostgreSQL database integration
- SQLAlchemy ORM for database operations
- API request/response validation
- Production deployment on AWS EC2
- Managed PostgreSQL database using AWS RDS
- Nginx reverse proxy
- Uvicorn application server
- Environment-based configuration
- Structured backend architecture

---

## Tech Stack

### Backend
- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic

### Database
- PostgreSQL
- AWS RDS

### Cloud & Deployment
- AWS EC2
- AWS RDS
- Nginx

### Development
- Git
- GitHub
- Linux

---

## Architecture

The deployed application follows this architecture:

```text
                    Internet
                       |
                       v
              AWS EC2 Public IP
                       |
                       v
                     Nginx
                       |
                       v
              127.0.0.1:8000
                       |
                       v
                  Uvicorn
                       |
                       v
                   FastAPI
                       |
                       v
                  SQLAlchemy
                       |
                       v
              PostgreSQL (RDS)
