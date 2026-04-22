import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
import os
from db.models import JobListing, SessionLocal

class DemandModel:
    def __init__(self):
        self.model_path = "ml/job_demand_model.joblib"
        self.encoder_path = "ml/label_encoder.joblib"
        self.model = None
        self.encoder = LabelEncoder()

    def train(self):
        db = SessionLocal()
        jobs = db.query(JobListing).all()
        db.close()

        if not jobs:
            print("No data to train on.")
            return

        df = pd.DataFrame([{
            "posted_at": j.posted_at,
            "source": j.source,
            "remote": j.remote,
            "category": j.category or "Other"
        } for j in jobs])

        # Feature engineering: count jobs per day per category
        df['day'] = df['posted_at'].dt.date
        training_data = df.groupby(['day', 'source', 'remote', 'category']).size().reset_index(name='job_count')
        
        # Convert date to features
        training_data['day_of_week'] = pd.to_datetime(training_data['day']).dt.dayofweek
        training_data['month'] = pd.to_datetime(training_data['day']).dt.month
        
        # Encode categorical
        training_data['cat_encoded'] = self.encoder.fit_transform(training_data['category'])
        training_data['source_encoded'] = LabelEncoder().fit_transform(training_data['source'])

        X = training_data[['day_of_week', 'month', 'cat_encoded', 'source_encoded', 'remote']]
        y = training_data['job_count']

        self.model = RandomForestRegressor(n_estimators=100)
        self.model.fit(X, y)

        joblib.dump(self.model, self.model_path)
        joblib.dump(self.encoder, self.encoder_path)
        print(f"Model trained and saved to {self.model_path}")

    def predict(self, day_of_week, month, category, source, remote):
        if not self.model:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.encoder = joblib.load(self.encoder_path)
            else:
                return 0
        
        try:
            cat_idx = self.encoder.transform([category])[0]
        except:
            cat_idx = 0 # Default/Other

        # Simplified source encoding for prediction
        source_idx = 0 if source == "arbeitnow" else 1

        X = [[day_of_week, month, cat_idx, source_idx, 1 if remote else 0]]
        return self.model.predict(X)[0]

if __name__ == "__main__":
    model = DemandModel()
    model.train()
