import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import pandas as pd
from collections import Counter
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from sklearn.metrics import RocCurveDisplay, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, RocCurveDisplay, confusion_matrix


# Load datasets
labevents = pd.read_csv('mimic-iii-clinical-database-1.4/LABEVENTS.csv.gz', compression='gzip')
file_path = 'mimic-iii-clinical-database-1.4/DIAGNOSES_ICD.csv.gz'
diagnoses_icd = pd.read_csv(file_path, compression='gzip')
patients = pd.read_csv('mimic-iii-clinical-database-1.4/PATIENTS.csv.gz', compression='gzip')
admissions = pd.read_csv('mimic-iii-clinical-database-1.4/ADMISSIONS.csv.gz', compression='gzip')

patients['DOB'] = pd.to_datetime(patients['DOB'])
admissions['ADMITTIME'] = pd.to_datetime(admissions['ADMITTIME'])

age_df = pd.merge(patients[['SUBJECT_ID', 'DOB']], admissions[['SUBJECT_ID', 'ADMITTIME']], on='SUBJECT_ID', how='left')
age_df['AGE'] = age_df['ADMITTIME'].dt.year - age_df['DOB'].dt.year
age_df['AGE'] -= ((age_df['ADMITTIME'].dt.month < age_df['DOB'].dt.month) | 
                  ((age_df['ADMITTIME'].dt.month == age_df['DOB'].dt.month) & 
                   (age_df['ADMITTIME'].dt.day < age_df['DOB'].dt.day))).astype(int)
age_df.loc[age_df['AGE'] > 89, 'AGE'] = 89
age_df= age_df.drop_duplicates(subset=['SUBJECT_ID'], keep='first')

# Merge admissions and diagnoses to see if diabetes Vorerkrankung or not
diagnoses_icd = diagnoses_icd.merge(admissions[['SUBJECT_ID', 'HADM_ID', 'ADMITTIME']], on=['SUBJECT_ID', 'HADM_ID'], how='left')
diagnoses_icd['ADMITTIME'] = pd.to_datetime(diagnoses_icd['ADMITTIME'])

# Filter for kidney failure and diabetes
kidney_codes = ['584', '5856', '5859', '586']
kidney_patients = diagnoses_icd[diagnoses_icd['ICD9_CODE'].isin(kidney_codes)]
diabetes_patients = diagnoses_icd[diagnoses_icd['ICD9_CODE'].astype(str).str.startswith('250')]

earliest_diabetes = diabetes_patients.groupby('SUBJECT_ID')['ADMITTIME'].min().reset_index()
earliest_diabetes.rename(columns={'ADMITTIME': 'DIABETES_DATE'}, inplace=True)

earliest_kidney = kidney_patients.groupby('SUBJECT_ID')['ADMITTIME'].min().reset_index()
earliest_kidney.rename(columns={'ADMITTIME': 'KIDNEY_DATE'}, inplace=True)

# Merge both dataframes to compare diagnosis dates
both_diagnoses = pd.merge(earliest_diabetes, earliest_kidney, on='SUBJECT_ID', how='inner')

# Add a column to indicate if diabetes before kidney failure
both_diagnoses['DIABETES_BEFORE_KIDNEY'] = both_diagnoses['DIABETES_DATE'] < both_diagnoses['KIDNEY_DATE']

# Get subject IDs where diabetes was diagnosed before kidney failure
diabetes_before_kidney_patients = both_diagnoses[both_diagnoses['DIABETES_BEFORE_KIDNEY']]['SUBJECT_ID'].unique()

lab_admission = labevents.merge(admissions, on=['SUBJECT_ID', 'HADM_ID'], how='inner')
lab_admission['CHARTTIME'] = pd.to_datetime(lab_admission['CHARTTIME'])
lab_admission['HOURS_SINCE_ADMIT'] = (lab_admission['CHARTTIME'] - lab_admission['ADMITTIME']).dt.total_seconds() / 3600
lab_admission['HOURS_SINCE_ADMIT'] = lab_admission['HOURS_SINCE_ADMIT'].round()
lab_admission = lab_admission[lab_admission['HOURS_SINCE_ADMIT'].between(0, 24)]

bun_itemid = 51006 
bun_data = lab_admission[labevents['ITEMID'] == bun_itemid]
bun_data = bun_data[bun_data['VALUENUM'].notna()] 
bun_data = bun_data[(bun_data['VALUENUM'] >= 0.1) & (bun_data['VALUENUM'] <= 150)]

sod_itemid = 50983
sod_data = lab_admission[labevents['ITEMID'] == sod_itemid]
sod_data = sod_data[sod_data['VALUENUM'].notna()] 
sod_data = sod_data[(sod_data['VALUENUM'] >= 10) & (sod_data['VALUENUM'] <= 150)]


creatinine = lab_admission[(lab_admission['ITEMID'] == 50912) & lab_admission['VALUENUM'].notna()]
creatinine = creatinine[(creatinine['VALUENUM'] >= 0.1) & (creatinine['VALUENUM'] <= 30)]
print(creatinine)

# Calculate average per patient
avg_creatinine = creatinine.groupby('SUBJECT_ID')['VALUENUM'].mean().reset_index()
avg_creatinine.columns = ['SUBJECT_ID', 'AVG_CREATININE']

avg_bun = bun_data.groupby('SUBJECT_ID')['VALUENUM'].mean().reset_index()
avg_bun.columns = ['SUBJECT_ID', 'AVG_BUN']
avg_bun = avg_bun.merge(avg_creatinine, on='SUBJECT_ID', how='inner')

avg_sod = sod_data.groupby('SUBJECT_ID')['VALUENUM'].mean().reset_index()
avg_sod.columns = ['SUBJECT_ID', 'AVG_SOD']
avg_sod = avg_sod.merge(avg_bun, on='SUBJECT_ID', how='inner')


# Merge with patients to get gender
patients = patients[['SUBJECT_ID', 'GENDER', 'DOB']]
merged_data = pd.merge(avg_sod, patients, on='SUBJECT_ID', how='left')

# Note which patients have been diagnosed with diabetes before being diagnosed with kidney failure
merged_data['DIABETES'] = merged_data['SUBJECT_ID'].apply(lambda sid: 1 if sid in diabetes_before_kidney_patients else 0)
merged_data['GENDER'] = merged_data['GENDER'].map({'M': 0, 'F': 1})

# Create kidney failure indicator
merged_data['KIDNEY_FAILURE'] = merged_data['SUBJECT_ID'].isin(kidney_patients['SUBJECT_ID']).astype(int)
merged_data = merged_data.merge(age_df[['SUBJECT_ID', 'AGE']], on='SUBJECT_ID', how='inner')

# SMOTE for training set
X = merged_data[['AVG_CREATININE', 'GENDER', 'AVG_BUN', 'AVG_SOD', 'DIABETES', 'AGE']]
y = merged_data['KIDNEY_FAILURE']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=16)
print("Original training set class distribution:")
print(Counter(y_train))

smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
print("Resampled training set class distribution:")
print(Counter(y_train_resampled))

# Regression analysis
X_train_resampled = sm.add_constant(X_train_resampled)
X_test = sm.add_constant(X_test)

# Logistic Regression
logreg = LogisticRegression(random_state=16)
logreg.fit(X_train_resampled, y_train_resampled)

y_pred = (logreg.predict_proba(X_test)[:, 1] >= 0.6).astype(int)
conf_matrix = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:\n", conf_matrix)

# ROC Curve
RocCurveDisplay.from_estimator(logreg, X_test, y_test)
plt.title("ROC Curve for Logistic Regression")
plt.show()

# Random forest
rf_clf = RandomForestClassifier(n_estimators=100, random_state=16, class_weight="balanced")
rf_clf.fit(X_train_resampled, y_train_resampled)

# Predict probabilities and classify based on a threshold
y_pred_proba = rf_clf.predict_proba(X_test)[:, 1]
y_pred = (y_pred_proba >= 0.6).astype(int)  # Adjust threshold if necessary

# Confusion Matrix
conf_matrix = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:\n", conf_matrix)

print("Classification Report:\n", classification_report(y_test, y_pred))

# ROC Curve
RocCurveDisplay.from_estimator(rf_clf, X_test, y_test)
plt.title("ROC Curve for Random Forest Classifier")
plt.show()

# heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix,
           annot=True,
           fmt='d',
           cmap='Blues',
           cbar=False,
           annot_kws={'size': 16},
           linewidths=1,
           linecolor='black')

plt.title('Confusion Matrix for Kidney Failure Prediction\n', fontsize=14)
plt.xlabel('Predicted Label', fontsize=12)
plt.ylabel('True Label', fontsize=12)

class_labels = ['No Failure (0)', 'Failure (1)']
tick_positions = [0.5, 1.5]
plt.xticks(tick_positions, class_labels)
plt.yticks(tick_positions, class_labels, rotation=0)

plt.show()