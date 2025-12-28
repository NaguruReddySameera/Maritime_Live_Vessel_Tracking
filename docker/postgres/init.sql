-- Initialize PostgreSQL database for Maritime Tracking System

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_vessels_mmsi ON vessels_vessel(mmsi);
CREATE INDEX IF NOT EXISTS idx_vessels_status ON vessels_vessel(status);
CREATE INDEX IF NOT EXISTS idx_vessels_location ON vessels_vessel USING GIST(current_coordinates);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications_notification(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications_notification(is_read);
CREATE INDEX IF NOT EXISTS idx_auth_user_email ON authentication_user(email);

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE maritime_tracking TO maritime_user;
