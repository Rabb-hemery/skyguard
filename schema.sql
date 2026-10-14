-- SkyGuard — Schéma de la base de données
-- Aucune donnée inventée : tout provient de l'API CNEOS de la NASA.

CREATE TABLE IF NOT EXISTS asteroid (
    id            SERIAL PRIMARY KEY,
    designation   TEXT UNIQUE NOT NULL,          -- identifiant NASA (ex: "2024 YR4")
    name          TEXT,                          -- nom complet si disponible
    diameter_km   DOUBLE PRECISION,              -- diamètre estimé (souvent inconnu)
    first_seen_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS close_approach (
    id                     SERIAL PRIMARY KEY,
    asteroid_id            INTEGER NOT NULL REFERENCES asteroid(id),
    approach_date          TIMESTAMPTZ NOT NULL, -- date du passage près de la Terre
    distance_au            DOUBLE PRECISION,     -- distance en unités astronomiques
    distance_km            DOUBLE PRECISION,     -- distance convertie en km
    relative_velocity_kms  DOUBLE PRECISION,     -- vitesse relative en km/s
    fetched_at             TIMESTAMPTZ DEFAULT now(),
    UNIQUE (asteroid_id, approach_date)          -- évite les doublons à chaque exécution
);

CREATE INDEX IF NOT EXISTS idx_approach_date ON close_approach (approach_date);
