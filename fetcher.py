"""SkyGuard — Récupère les passages d'astéroïdes proches de la Terre via l'API CNEOS
de la NASA et les enregistre dans PostgreSQL.

API : https://ssd-api.jpl.nasa.gov/cad.api (aucune clé requise)
Doc : https://ssd-api.jpl.nasa.gov/doc/cad.html
"""

import os
from datetime import date, timedelta

import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://ssd-api.jpl.nasa.gov/cad.api"
AU_IN_KM = 149_597_870.7  # 1 unité astronomique en km

# Seuils d'alerte (à ajuster selon tes critères)
ALERT_DISTANCE_KM = 7_500_000   # ~0.05 UA, très proche en termes spatiaux
ALERT_DIAMETER_KM = 1.0         # objet "grand" (>= 1 km de diamètre)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "skyguard"),
        user=os.getenv("DB_USER", "skyguard"),
        password=os.getenv("DB_PASSWORD", "skyguard"),
    )


def fetch_close_approaches(days=30, max_dist_au=0.2, limit=100):
    """Interroge l'API CNEOS : objets passant à moins de max_dist_au UA
    dans les 'days' prochains jours."""
    params = {
        "date-min": str(date.today()),
        "date-max": str(date.today() + timedelta(days=days)),
        "dist-max": max_dist_au,
        "fullname": "true",
        "limit": limit,
    }
    resp = requests.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # La réponse donne la liste des colonnes, puis les lignes brutes :
    # on reconstruit des dictionnaires proprement.
    fields = data["fields"]
    return [dict(zip(fields, row)) for row in data.get("data", [])]


def should_alert(distance_km, diameter_km):
    if distance_km < ALERT_DISTANCE_KM:
        return True
    if diameter_km is not None and diameter_km >= ALERT_DIAMETER_KM:
        return True
    return False


def save_approaches(approaches):
    conn = get_db_connection()
    cur = conn.cursor()
    alerts = []

    for obj in approaches:
        des = obj["des"]
        name = obj.get("fullname", "").strip() or des
        diameter = float(obj["diameter"]) if obj.get("diameter") else None

        # INSERT ... ON CONFLICT : si l'astéroïde existe déjà, on le met à jour
        cur.execute(
            """
            INSERT INTO asteroid (designation, name, diameter_km)
            VALUES (%s, %s, %s)
            ON CONFLICT (designation) DO UPDATE
                SET name        = EXCLUDED.name,
                    diameter_km = COALESCE(EXCLUDED.diameter_km, asteroid.diameter_km)
            RETURNING id
            """,
            (des, name, diameter),
        )
        asteroid_id = cur.fetchone()[0]

        dist_au = float(obj["dist"])
        dist_km = dist_au * AU_IN_KM
        v_rel = float(obj["v_rel"])

        cur.execute(
            """
            INSERT INTO close_approach
                (asteroid_id, approach_date, distance_au, distance_km, relative_velocity_kms)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (asteroid_id, approach_date) DO NOTHING
            """,
            (asteroid_id, obj["cd"], dist_au, dist_km, v_rel),
        )

        if should_alert(dist_km, diameter):
            alerts.append(
                f"! ALERTE : {name} passe à {dist_km:,.0f} km le {obj['cd']}"
                f" (diamètre : {diameter if diameter else 'inconnu'}, vitesse : {v_rel} km/s)"
            )

    conn.commit()
    cur.close()
    conn.close()
    return alerts


def main():
    print("Interrogation de l'API CNEOS de la NASA...")
    approaches = fetch_close_approaches(days=30, max_dist_au=0.2)
    print(f"{len(approaches)} passages proches trouvés sur 30 jours.")
    alerts = save_approaches(approaches)
    for alert in alerts:
        print(alert)
    if not alerts:
        print("Aucun seuil d'alerte dépassé. Ciel tranquille... pour l'instant.")


if __name__ == "__main__":
    main()
