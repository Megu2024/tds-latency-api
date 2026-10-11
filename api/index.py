
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
@app.options("/api/latency")
def latency_options():
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# Allow POST requests from any origin, as required by the assignment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Actual telemetry measurements from q-vercel-latency.json.
# Each tuple contains: (region, latency_ms, uptime_pct)
DATA = [
    ("apac", 211.73, 97.225),
    ("apac", 186.14, 97.400),
    ("apac", 170.33, 97.603),
    ("apac", 213.89, 98.415),
    ("apac", 212.45, 97.863),
    ("apac", 174.05, 99.232),
    ("apac", 236.44, 99.138),
    ("apac", 111.12, 97.285),
    ("apac", 194.72, 97.222),
    ("apac", 147.52, 98.508),
    ("apac", 140.38, 97.949),
    ("apac", 190.35, 99.465),

    ("emea", 174.16, 98.838),
    ("emea", 212.58, 97.518),
    ("emea", 212.43, 98.490),
    ("emea", 170.98, 98.638),
    ("emea", 187.13, 97.201),
    ("emea", 143.33, 99.234),
    ("emea", 199.04, 98.565),
    ("emea", 230.69, 97.193),
    ("emea", 157.68, 98.571),
    ("emea", 198.27, 98.882),
    ("emea", 196.29, 98.293),
    ("emea", 130.53, 99.117),

    ("amer", 175.34, 97.442),
    ("amer", 217.40, 98.090),
    ("amer", 160.80, 97.324),
    ("amer", 207.77, 97.433),
    ("amer", 135.83, 98.303),
    ("amer", 223.57, 97.242),
    ("amer", 211.63, 97.732),
    ("amer", 165.80, 99.110),
    ("amer", 229.34, 97.168),
    ("amer", 110.78, 98.702),
    ("amer", 186.66, 98.478),
    ("amer", 158.97, 99.229),
]


def percentile95(values):
    """Calculate the 95th percentile using linear interpolation."""
    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * 0.95
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    fraction = position - lower

    return values[lower] + (
        values[upper] - values[lower]
    ) * fraction


@app.get("/")
def home():
    return {"message": "Latency analytics API is running"}


@app.post("/api/latency")
def latency(payload: dict, response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    regions = payload.get("regions")
    threshold = payload.get("threshold_ms")

    if not isinstance(regions, list) or not regions:
        raise HTTPException(
            status_code=400,
            detail="regions must be a non-empty list",
        )

    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
    ):
        raise HTTPException(
            status_code=400,
            detail="threshold_ms must be a number",
        )

    results = {}

    for region in regions:
        records = [
            row for row in DATA
            if row[0] == region
        ]

        if not records:
            continue

        latencies = [row[1] for row in records]
        uptimes = [row[2] for row in records]

        results[region] = {
            "avg_latency": round(
                sum(latencies) / len(latencies), 3
            ),
            "p95_latency": round(
                percentile95(latencies), 3
            ),
            "avg_uptime": round(
                sum(uptimes) / len(uptimes), 3
            ),
            "breaches": sum(
                value > threshold for value in latencies
            ),
        }

    return {"regions": results}
