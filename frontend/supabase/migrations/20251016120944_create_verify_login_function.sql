/*
  # Create login verification function

  1. New Functions
    - `verify_user_login` - Verifies username and password using bcrypt

  2. Security
    - Function is accessible to all users for login purposes
    - Uses bcrypt for secure password comparison
    - Returns user data if credentials are valid

  3. Notes
    - Requires pgcrypto extension for crypt function
    - Returns empty array if credentials are invalid
*/

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION verify_user_login(input_username text, input_password text)
RETURNS TABLE(id uuid, username text) AS $$
BEGIN
  RETURN QUERY
  SELECT u.id, u.username
  FROM users u
  WHERE u.username = input_username
    AND u.password = crypt(input_password, u.password);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;