# Pangolin Compliance Suite

Pangolin Compliance Suite is a comprehensive test automation and compliance verification platform designed to validate and test various kinds of systems including databases, APIs, cloud services, and SSH connections. The platform provides a structured way to create, execute, and verify tests against systems to ensure they comply with expected requirements and operational standards.

## Key Features

- **Test Protocol Management**: Create, configure, and organize test protocols in test suites
- **Multi-Target Support**: Test databases, APIs, SSH connections, Kubernetes, AWS services, and more
- **Flexible Verification**: Robust verification framework with support for string, numeric, JSON, list operations and more
- **Distributed Execution**: Celery-based task queue system for distributed test execution
- **Environment Variable Management**: Secure handling of credentials and configuration values
- **Web Dashboard**: Monitor test runs, view results, and manage verification criteria

## System Architecture

Pangolin Compliance Suite is built as a Django application with the following components:

- **Web Application**: Django-based web interface for management and monitoring
- **Message Queue**: RabbitMQ for task distribution
- **Task Processing**: Celery workers for executing tests
- **Database**: PostgreSQL for storing configurations, test protocols, and results
- **Verification Engine**: Pluggable verification system with various verifier implementations

## Project Structure

```
pangolin_compliance_suite/
├── authentication/        # User authentication
├── dashboard/             # Main dashboard and reporting
├── environments/          # Environment variable management
├── projects/              # Project management
├── test_protocols/        # Core test protocol functionality
│   ├── models.py          # Data models for tests and verification
│   ├── services.py        # Business logic for test execution
│   ├── tasks.py           # Celery tasks for async execution
│   ├── verifiers/         # Verification implementations
│   │   ├── api_verifiers.py
│   │   ├── base.py
│   │   ├── db_verifiers.py
│   │   ├── dict_verifiers.py
│   │   ├── factory.py
│   │   ├── list_verifiers.py
│   │   ├── numeric_verifiers.py
│   │   └── string_verifiers.py
└── utils/                 # Utility functions
```

## Core Components

### Test Protocols

Test protocols are the core units of testing in Pangolin. Each protocol:
- Is associated with a test suite
- Has a connection configuration for a specific target system
- Contains multiple execution steps
- Includes verification methods to validate results

### Verification System

The verification system provides a flexible way to validate test results against expected values:

- **String Verifiers**: Exact match, contains, regex matching, length checking
- **Numeric Verifiers**: Equality, range checking, threshold verification
- **Dictionary Verifiers**: Key checks, schema validation, subset verification
- **List Verifiers**: Length checking, contains elements, uniqueness, sorting
- **API Verifiers**: Status code, response time, headers, content type
- **Database Verifiers**: Row count, column existence, query result, execution time

### Connection Management

Pangolin supports connections to various types of systems:
- Databases (PostgreSQL, MySQL, Oracle, etc.)
- REST APIs
- SSH connections
- Kubernetes clusters
- AWS services
- Azure services

## Deployment

The project is containerized using Docker and can be deployed using docker-compose:

```bash
docker-compose up -d
```

This will start the following services:
- PostgreSQL database
- RabbitMQ message broker
- Django web application
- Protocol execution worker
- Suite execution worker
- Celery beat for scheduled tasks
- Flower for task monitoring
- Nginx for serving static files and as a reverse proxy

## Getting Started

### Prerequisites

- Docker and docker-compose
- Python 3.11+

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-organization/pangolin-compliance-suite.git
   cd pangolin-compliance-suite
   ```

2. Create a `.env` file with necessary environment variables:
   ```
   DB_NAME=pangolin
   DB_USER=pangolin
   DB_PASSWORD=your_secure_password
   RABBITMQ_USER=pangolin
   RABBITMQ_PASSWORD=your_secure_password
   SECRET_KEY=your_django_secret_key
   ALLOWED_HOSTS=localhost,127.0.0.1
   DEBUG=True
   ```

3. Start the services:
   ```bash
   docker-compose up -d
   ```

4. Visit the application:
   ```
   http://localhost:8000
   ```

## Creating Your First Test Protocol

1. Create a project in the web interface
2. Create a test suite within the project
3. Add a test protocol to the suite
4. Configure the connection for the protocol
5. Add execution steps to the protocol
6. Configure verification methods for each step
7. Run the protocol and view results

## Development

### Setting up a development environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

5. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Running Tests

```bash
python manage.py test
```

## License

[MIT License](LICENSE)

## Acknowledgements

- Django - The web framework used
- Celery - Distributed task queue
- RabbitMQ - Message broker
- PostgreSQL - Database system
- Docker - Containerization platform
