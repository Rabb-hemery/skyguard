# SkyGuard

Veille des objets proches de la Terre (astéroïdes, comètes) avec les données
réelles de la NASA (API CNEOS / JPL). Les passages proches sont enregistrés
dans PostgreSQL et des alertes s'affichent quand un seuil est dépassé.

## Démarrage

```bash
# 1. Lancer la base PostgreSQL (Docker)
docker compose up -d

# 2. Créer les tables
docker exec -i skyguard_db psql -U skyguard -d skyguard < schema.sql

# 3. Installer les dépendances Python
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt

# 4. Configurer l'environnement
cp .env.example .env

# 5. Premier relevé
python fetcher.py
```

## Voir les données

```bash
docker exec -it skyguard_db psql -U skyguard -d skyguard

-- Les 10 passages les plus proches :
SELECT a.name, c.approach_date, c.distance_km, c.relative_velocity_kms
FROM close_approach c
JOIN asteroid a ON a.id = c.asteroid_id
ORDER BY c.distance_km ASC
LIMIT 10;
```

## Idées d'amélioration

- [ ] Alerte Discord/webhook au lieu d'un simple print
- [ ] Exécution automatique (cron ou GitHub Actions)
- [ ] Mini API Flask/FastAPI pour consulter les données
- [ ] Ajouter les éruptions solaires (API DONKI de la NASA)
