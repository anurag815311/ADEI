import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os
from db.models import JobListing, SessionLocal

class HiringForecastModel:
    """
    New Time-Series Forecasting Model (Additive Improvement).
    Predicts next week's job posting volume.
    """
    def __init__(self):
        self.model_path = "ml/hiring_forecast_model.joblib"
        self.model = None

    def train(self):
        db = SessionLocal()
        jobs = db.query(JobListing).all()
        db.close()

        if not jobs:
            return

        df = pd.DataFrame([{"posted_at": j.posted_at} for j in jobs])
        df['day'] = df['posted_at'].dt.date
        daily_counts = df.groupby('day').size().reset_index(name='count')
        
        # Convert date to ordinal for simple linear forecasting
        daily_counts['date_ordinal'] = pd.to_datetime(daily_counts['day']).apply(lambda x: x.toordinal())
        
        if len(daily_counts) < 2:
            return

        X = daily_counts[['date_ordinal']]
        y = daily_counts['count']

        self.model = LinearRegression()
        self.model.fit(X, y)

        joblib.dump(self.model, self.model_path)
        print(f"Hiring Forecast Model trained and saved to {self.model_path}")

    def predict_next_week(self):
        if not self.model:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
            else:
                return []

        # Predict for next 7 days
        last_date = datetime.now()
        future_dates = [last_date + timedelta(days=i) for i in range(1, 8)]
        X_future = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        predictions = self.model.predict(X_future)
        
        return [{"date": d.strftime("%Y-%m-%d"), "predicted_count": max(0, round(p))} for d, p in zip(future_dates, predictions)]

if __name__ == "__main__":
    from datetime import datetime, timedelta
    forecaster = HiringForecastModel()
    forecaster.train()
    print(forecaster.predict_next_week())
