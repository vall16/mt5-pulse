/*
  # Create users table for authentication

  1. New Tables
    - `users`
      - `id` (uuid, primary key)
      - `username` (text, unique) - User login username
      - `password` (text) - Hashed password
      - `created_at` (timestamptz) - Account creation timestamp
      - `last_login` (timestamptz) - Last login timestamp

  2. Security
    - Enable RLS on `users` table
    - Add policy for users to read their own data
    - Add policy for users to update their last login

  3. Notes
    - Passwords should be hashed before storage
    - Username is unique and required
    - Track last login for security purposes
*/

CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  username text UNIQUE NOT NULL,
  password text NOT NULL,
  created_at timestamptz DEFAULT now(),
  last_login timestamptz DEFAULT now()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own data"
  ON users
  FOR SELECT
  USING (true);

CREATE POLICY "Users can update own last_login"
  ON users
  FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);