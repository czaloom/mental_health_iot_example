import os
import csv
import json
import time
import logging
from dataclasses import dataclass, field

import psycopg2
from psycopg2 import sql
from psycopg2._psycopg import connection

log = logging.getLogger(__name__)


@dataclass
class Datum:
    timestamp: str
    location_id: int
    temperature_celsius: float
    humidity_percent: float
    air_quality_index: int
    noise_level_db: float
    lighting_lux: float
    crowd_density: int
    stress_level: int
    sleep_hours: float
    mood_score: float
    mental_health_status: int


@dataclass
class ModelParameters:
    threshold: int = field(default=60)


class MentalHealthPredictor:

    def __init__(
        self,
        params: ModelParameters,
    ):
        """
        Initialize a high stress detector.

        Parameters
        ----------
        params : ModelParameters
            Model configuration parameters.
        """
        self._params = params

    @staticmethod
    def _compute_sleep_score(datum: Datum) -> float:
        """
        Score sleep duration based on recommended 8 hours.

        Parameters
        ----------
        datum : Datum
            Input data containing 'sleep_hours' field.

        Returns
        -------
        float
            Sleep score between 0 and 1. A score of 1.0 indicates
            the recommended number of sleep hours has been met. 

        """
        sleep_hours_deviation = 0.0
        if datum.sleep_hours > 8.5:
            sleep_hours_deviation = min(datum.sleep_hours - 8.5, 2.0)
        elif datum.sleep_hours < 7.5:
            sleep_hours_deviation = min(7.5 - datum.sleep_hours, 2.0)
        else:
            sleep_hours_deviation = 0.0
        return (2.0 - sleep_hours_deviation) / 2.0
    
    @staticmethod
    def _normalize_stress_level(datum: Datum) -> float:
        """
        Normalize stress level.

        Parameters
        ----------
        datum : Datum
            Input data containing 'stress_level' field.

        Returns
        -------
        float
            Stress level normalized between 0 and 1.
        """
        stress_level = min(datum.stress_level, 100)
        return stress_level / 100.0

    def predict(self, datum: Datum) -> int:
        """
        Predict the stress score.

        Parameters
        ----------
        datum : Datum
            Input data containing relevant fields.
        
        Returns
        -------
        int
            Prediction score ranging from 0 to 100 with the higher 
            value representing higher stress.
        """
        sleep_score = self._compute_sleep_score(datum)
        normalized_stress_level = self._normalize_stress_level(datum)
        stress_score = (sleep_score + normalized_stress_level) / 2.0
        return int(stress_score * 100.0)


def scan_csv(
    conn: connection,
    filepath: str,
    alert_level: int,
    model: MentalHealthPredictor,
) -> tuple[int, int]:
    """
    Stream a CSV file into DBQL.

    Parameters
    ----------
    conn : connection
        An active database connection.
    filepath : str
        Path to a locally stored CSV file.
    alert_level : int
        Level at which to store a stress alert.
    model : MentalHealthPredictor
        A mental health prediction model.

    Returns
    -------
    tuple[int, int]
        A tuple containing counts of total datums and high stress datums.
    """
    count_all, count_high_stress = 0, 0
    cumulative_computation_time = 0.0
    log.info(f"ingesting '{filepath}'")
    with conn.cursor() as cur, open(filepath, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            count_all += 1
            datum = Datum(
                timestamp=row["timestamp"],
                location_id=int(row["location_id"]),
                temperature_celsius=float(row["temperature_celsius"]),
                humidity_percent=float(row["humidity_percent"]),
                air_quality_index=int(row["air_quality_index"]),
                noise_level_db=float(row["noise_level_db"]),
                lighting_lux=float(row["lighting_lux"]),
                crowd_density=int(row["crowd_density"]),
                stress_level=int(row["stress_level"]),
                sleep_hours=float(row["sleep_hours"]),
                mood_score=float(row["mood_score"]),
                mental_health_status=int(row["mental_health_status"]),
            )

            # mental health prediction logic
            t_start = time.perf_counter()
            score = model.predict(datum)
            t_end = time.perf_counter()
            t_computation = t_end - t_start
            cumulative_computation_time += t_computation
            log.debug(f"computation took {t_computation} seconds")

            # check if mental health score exceeds alert level
            if score <= alert_level:
                continue
            
            # record high stress event
            log.info("detected high stress event")
            count_high_stress += 1
            query = sql.SQL(
                "INSERT INTO high_stress_alerts ("
                "filepath, timestamp, location_id, temperature_celsius, humidity_percent, "
                "air_quality_index, noise_level_db, lighting_lux, crowd_density, "
                "stress_level, sleep_hours, mood_score, mental_health_status, score) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            )
            cur.execute(query, [
                filepath,
                datum.timestamp,
                datum.location_id,
                datum.temperature_celsius,
                datum.humidity_percent,
                datum.air_quality_index,
                datum.noise_level_db,
                datum.lighting_lux,
                datum.crowd_density,
                datum.stress_level,
                datum.sleep_hours,
                datum.mood_score,
                datum.mental_health_status,
                score,
            ])

        log.info(f"average computation time: {cumulative_computation_time / count_all} seconds")
        conn.commit()
    return count_all, count_high_stress



@dataclass
class AgentEvent:
    filepath: str = field(default="university_mental_health_iot_dataset.csv")
    alert_level: int = field(default=70)
    model_params: ModelParameters = field(default_factory=ModelParameters)

    def __post_init__(self):
        validation_errors = []
        if not isinstance(self.filepath, str):
            validation_errors.append(f"received type '{type(self.filepath)}' for 'filepath' field; expected 'str'")
        if not isinstance(self.alert_level, int):
            validation_errors.append(f"received type '{type(self.alert_level)}' for 'alert_level' field; expected 'int'")
        if not isinstance(self.model_params, (dict, ModelParameters)):
            validation_errors.append(f"received '{self.model_params}' for 'model_params' field; expected either 'dict' or 'ModelParameters'")
        if validation_errors:
            raise ValueError(f"agent event validation failed with: {validation_errors}")

        if isinstance(self.model_params, dict):
            self.model_params = ModelParameters(**self.model_params)


def lambda_handler(event, context):
    try:
        # unpack event
        params = AgentEvent(**json.loads(event.get("body", "{}")))

        # initialize model
        model = MentalHealthPredictor(params.model_params)

        with psycopg2.connect(
            host=os.environ["DB_HOST"],
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            port=os.environ.get("DB_PORT", "5432"),
        ) as conn:
            count_all, count_high_stress = scan_csv(
                conn=conn,
                filepath=params.filepath,
                alert_level=params.alert_level,
                model=model,
            )
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": {
                    "scanned": count_all,
                    "high_stress": count_high_stress,
                },
            }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


if __name__ == "__main__":
    x = lambda_handler(
        event={
            "body": json.dumps({
                "filepath": "py-lambda/university_mental_health_iot_dataset.csv" 
            })
        },
        context={},
    )
    print(x)
