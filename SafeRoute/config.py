# SafeRoute configuration
# CPU4106 — Level 4 Computing Group Project

import os

# Flask
SECRET_KEY = os.environ.get("SAFEROUTE_SECRET_KEY", "change-this-secret-key-for-production")

# MySQL connection (see database/saferoute.sql)
MYSQL_HOST = os.environ.get("SAFEROUTE_DB_HOST", "localhost")
MYSQL_USER = os.environ.get("SAFEROUTE_DB_USER", "root")
MYSQL_PASSWORD = os.environ.get("SAFEROUTE_DB_PASSWORD", "Discover17")
MYSQL_DB = os.environ.get("SAFEROUTE_DB_NAME", "saferoute")

# Route safety model
ROUTE_CORRIDOR_KM = 0.6      # incidents within 600 m of a route are counted
INCIDENTS_PER_POINT = 5      # each incident removes 5 points from the score
