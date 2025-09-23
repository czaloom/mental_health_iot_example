import pandas as pd
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


class LogisticRegressionModel:
    def __init__(self):
        self.model = LogisticRegression()
        self.scaler = StandardScaler()
        self.columns = None

    def _preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert timestamp column to numerical features and drop original column.
        """
        ts_col = "timestamp"
        if ts_col in df.columns:
            ts = pd.to_datetime(df[ts_col])
            df = df.copy()
            df["month"] = ts.dt.month
            df["day"] = ts.dt.day
            df["hour"] = ts.dt.hour
            df = df.drop(columns=[ts_col])
        return df

    def train(self, df: pd.DataFrame, target_col: str):
        """
        Train a logistic regression model.
        """
        X = df.drop(columns=[target_col])
        y = df[target_col]

        X = self._preprocess(X)
        self.columns = X.columns

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train model
        self.model.fit(X_scaled, y)

    def predict(
        self,
        timestamp: str,
        location_id: int,
        temperature_celsius: float,
        humidity_percent: float,
        air_quality_index: int,
        noise_level_db: float,
        lighting_lux: float,
        crowd_density: int,
        stress_level: int,
        sleep_hours: float,
        mood_score: float,
        mental_health_status: int,
    ) -> float:
        """
        Predict probability for a single row.

        Returns
        -------
        float
            Probability between 0 and 1
        """
        input_row = dict(
            timestamp=timestamp,
            location_id=location_id,
            temperature_celsius=temperature_celsius,
            humidity_percent=humidity_percent,
            air_quality_index=air_quality_index,
            noise_level_db=noise_level_db,
            lighting_lux=lighting_lux,
            crowd_density=crowd_density,
            stress_level=stress_level,
            sleep_hours=sleep_hours,
            mood_score=mood_score,
            mental_health_status=mental_health_status,
        )
        row_df = pd.DataFrame([input_row])
        row_df = self._preprocess(row_df)
        row_df = row_df.reindex(columns=self.columns, fill_value=0)
        row_scaled = self.scaler.transform(row_df)
        prob = self.model.predict_proba(row_scaled)[0, 1]
        return float(prob)
    

if __name__ == "__main__":
    df = pd.read_csv("py-lambda/university_mental_health_iot_dataset.csv")

    model = LogisticRegressionModel()
    model.train(df, target_col="stress_level")

    prediction = model.predict(
        timestamp="2024-05-02 03:15:00",
        location_id=104,
        temperature_celsius=25.84780682083279,
        humidity_percent=46.54020319753251,
        air_quality_index=144,
        noise_level_db=63.25726362947179,
        lighting_lux=253.6755467649878,
        crowd_density=50,
        stress_level=78,
        sleep_hours=5.08,
        mood_score=2.0,
        mental_health_status=2,
    )

    # prediction = model.predict(
    #     timestamp=datetime.now().isoformat(),
    #     location_id=12,
    #     temperature_celsius=35.3,
    #     humidity_percent=54.1,
    #     air_quality_index=244,
    #     noise_level_db=33.5,
    #     lighting_lux=10.3,
    #     crowd_density=44,
    #     stress_level=100,
    #     sleep_hours=5,
    #     mood_score=0.8,
    #     mental_health_status=10,
    # )
    print("Predicted probability:", prediction)