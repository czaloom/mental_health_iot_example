CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS high_stress_users (
  record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  filepath TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  location_id INTEGER NOT NULL,
  temperature_celsius DOUBLE PRECISION NOT NULL,
  humidity_percent DOUBLE PRECISION NOT NULL,
  air_quality_index INTEGER NOT NULL,
  noise_level_db DOUBLE PRECISION NOT NULL,
  lighting_lux DOUBLE PRECISION NOT NULL,
  crowd_density INTEGER NOT NULL,
  stress_level INTEGER NOT NULL,
  sleep_hours DOUBLE PRECISION NOT NULL,
  mood_score DOUBLE PRECISION NOT NULL,
  mental_health_status INTEGER NOT NULL,
  score INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_high_stress_users_score
  ON high_stress_users (score DESC);

CREATE INDEX IF NOT EXISTS idx_high_stress_users_timestamp
  ON high_stress_users (timestamp DESC);
