# Risk Assessment Backend

A FastAPI backend application with PostgreSQL database using raw SQL queries (no ORM) and Azure Entra ID authentication.

## Features

- FastAPI framework with automatic API documentation
- PostgreSQL database connection using psycopg2
- Raw SQL queries (no ORM)
- Azure Entra ID (Azure AD) authentication middleware
- JWT token validation and user extraction
- Proper service layer architecture
- RESTful API endpoints with authentication
- CORS middleware enabled
- Comprehensive error handling and logging

## Project Structure

```
RiskAss_Backend/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── database/
│   ├── __init__.py
│   ├── connection.py      # Database connection management
│   └── schema.sql         # Database schema
├── middleware/
│   ├── __init__.py
│   └── auth_middleware.py # Azure AD authentication middleware
├── services/
│   ├── __init__.py
│   └── example_service.py # Business logic layer
└── routers/
    ├── __init__.py
    └── example_router.py  # API endpoints (protected)
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

The application is configured to use a local PostgreSQL database. The database URL is already configured in `config.py`:

```
DATABASE_URL=postgresql://postgres:nivea@localhost:5432/postgres
```

Database Configuration:
- **Host**: localhost
- **Port**: 5432
- **Database**: postgres
- **Username**: postgres
- **Password**: nivea

If you need to use a different database, you can:

1. Set the `DATABASE_URL` environment variable
2. Or update the individual components in `config.py`:
   - `DB_HOST`
   - `DB_PORT`
   - `DB_NAME`
   - `DB_USER`
   - `DB_PASSWORD`

3. Run the schema file to create tables:
   ```bash
   psql -U postgres -d postgres -f database/schema.sql
   ```

### 3. Azure Entra ID Configuration

To use Azure Entra ID authentication, you need to configure your Azure AD app:

1. **Register your application in Azure AD**:
   - Go to Azure Portal → Azure Active Directory → App registrations
   - Create a new registration
   - Note down the Application (client) ID and Directory (tenant) ID

2. **Set environment variables** (optional - already configured):
   ```bash
   AZURE_TENANT_ID=b8869792-ee44-4a05-a4fb-b6323a34ca35
   AZURE_CLIENT_ID=b7fb9a3b-efe3-418d-8fa8-243487a42530
   AZURE_CLIENT_SECRET=your-client-secret
   ```

3. **Configure API permissions**:
   - In your Azure AD app, go to API permissions
   - Add Microsoft Graph permissions (User.Read)
   - Grant admin consent

### 4. Run the Application

```bash
# Development server
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc docs: http://localhost:8000/redoc

## API Endpoints

### Public Endpoints
- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

### Protected Endpoints (Require Azure AD Token)
All endpoints under `/api/v1/` require authentication:

- `GET /api/v1/items` - Get all items
- `GET /api/v1/items/{item_id}` - Get item by ID
- `POST /api/v1/items` - Create new item
- `PUT /api/v1/items/{item_id}` - Update item
- `DELETE /api/v1/items/{item_id}` - Delete item
- `GET /api/v1/me` - Get current user information

### Authentication

All protected endpoints require a valid Azure AD access token in the Authorization header:

```
Authorization: Bearer <your-azure-ad-access-token>
```

### Example Usage with Authentication

#### Get current user info
```bash
curl -H "Authorization: Bearer <your-token>" \
     "http://localhost:8000/api/v1/me"
```

#### Get all items (authenticated)
```bash
curl -H "Authorization: Bearer <your-token>" \
     "http://localhost:8000/api/v1/items"
```

#### Create an item (authenticated)
```bash
curl -X POST "http://localhost:8000/api/v1/items" \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Item", "description": "This is a test item"}'
```

## Authentication Flow

1. **Frontend obtains access token** from Azure AD
2. **Frontend includes token** in Authorization header
3. **Backend validates token** using Azure AD public keys
4. **Backend extracts user information** from token payload
5. **Backend logs user actions** with username

## Token Validation

The middleware validates tokens by:
- Verifying the token signature using Azure AD public keys
- Checking the token audience (client ID)
- Validating the token issuer
- Extracting user information (username, email, roles)

## Database Connection

The application uses a connection pool pattern with psycopg2. The `DatabaseConnection` class in `database/connection.py` handles:

- Connection establishment and management
- Query execution with proper error handling
- Automatic connection cleanup
- Support for both SELECT and non-SELECT queries

## Error Handling

The application includes comprehensive error handling:

- Database connection errors
- Query execution errors
- Authentication errors (401 Unauthorized)
- HTTP status codes (404, 500, etc.)
- Detailed logging for debugging

## Development

### Adding New Protected Endpoints

1. Create a new service in the `services/` directory
2. Create a new router in the `routers/` directory
3. Add the `current_user: Dict[str, Any] = Depends(require_auth())` parameter
4. Include the router in `main.py`

### Adding New Database Tables

1. Add the table schema to `database/schema.sql`
2. Create corresponding service methods
3. Add router endpoints as needed

## Production Considerations

- Update CORS settings in `main.py` for production
- Use environment variables for sensitive configuration
- Implement proper rate limiting and request validation
- Configure proper logging levels
- Use a production-grade ASGI server like Gunicorn
- Store Azure AD configuration securely
- Implement token caching for better performance

## License

This project is for educational and development purposes. 