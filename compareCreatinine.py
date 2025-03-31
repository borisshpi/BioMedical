import pandas as pd
import matplotlib.pyplot as plt


def plot(data, title, path):

    median_value = data['VALUENUM'].median()
    plt.figure(figsize=(10, 6))
    counts, bins, patches = plt.hist(data['VALUENUM'], bins=50, alpha=0.75, edgecolor='black')

    plt.axvline(median_value, color='red', linestyle='--', linewidth=2)
    plt.text(median_value, plt.ylim()[1], f'Median: {median_value:.2f}', color='red', ha='center', va='bottom', fontsize=10, fontweight='bold')


    plt.yscale('log')
    plt.xlabel('Creatinine Level (mg/dL)')
    plt.ylabel('Frequency (Log Scale)')
    plt.title(title)
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.savefig(path, dpi=300)
    plt.close()


def find_creatinine_kidneyf(kidneyf_patients, kidneyf_creatinine_tests, patients):
    kidneyf_patients_with_creatinine = pd.merge(kidneyf_patients, kidneyf_creatinine_tests, on='SUBJECT_ID', how='inner')
    kidneyf_patients_with_creatinine['VALUENUM'] = pd.to_numeric(kidneyf_patients_with_creatinine['VALUENUM'], errors='coerce')
    kidneyf_patients_with_creatinine = kidneyf_patients_with_creatinine.dropna(subset=['VALUENUM'])

    filtered_data = kidneyf_patients_with_creatinine[kidneyf_patients_with_creatinine['VALUENUM'] < 30]
    filtered_data = filtered_data.drop(columns=['ROW_ID'], errors='ignore')
    filtered_data = pd.merge(filtered_data, patients, on=['SUBJECT_ID'], how='left')

    title = 'Distribution of Creatinine Levels among patients with kidney failure (Values < 30 mg/dL)'
    path = 'Output/kidneyF_creatinine_histogram_filtered_log.png'
    plot(filtered_data, title, path)

    #Difference males vs female
    filtered_data['GENDER'] = filtered_data['GENDER'].astype(str)
    male = filtered_data[filtered_data['GENDER'] == 'M'] 
    title = 'Distribution of Creatinine Levels among male patients with kidney failure (Values < 30 mg/dL)'
    path = 'Output/male_kidneyF_creatinine_histogram_filtered_log.png'
    plot(male, title, path)

    female = filtered_data[filtered_data['GENDER'] == 'F']
    title = 'Distribution of Creatinine Levels among female patients with kidney failure (Values < 30 mg/dL)'
    path = 'Output/female_kidneyF_creatinine_histogram_filtered_log.png'
    plot(female, title, path)


def find_creatinine_non_kidneyf(non_kidneyf_patients, creatinine_tests, patients):
    non_kidneyf_patients_with_creatinine = pd.merge(non_kidneyf_patients, creatinine_tests, on='SUBJECT_ID', how='inner')
    non_kidneyf_patients_with_creatinine['VALUENUM'] = pd.to_numeric(non_kidneyf_patients_with_creatinine['VALUENUM'], errors='coerce')
    non_kidneyf_patients_with_creatinine = non_kidneyf_patients_with_creatinine.dropna(subset=['VALUENUM'])

    filtered_data = non_kidneyf_patients_with_creatinine[non_kidneyf_patients_with_creatinine['VALUENUM'] < 30]
    filtered_data = pd.merge(filtered_data, patients, on=['SUBJECT_ID'], how='left') 

    title = 'Distribution of Creatinine Levels among patients without kidney failure (Values < 30 mg/dL)'
    path = 'Output/non_kidneyF_creatinine_histogram_filtered_log.png'
    plot(filtered_data, title, path)

    #Difference males vs female
    filtered_data['GENDER'] = filtered_data['GENDER'].astype(str)
    male = filtered_data[filtered_data['GENDER'] == 'M'] 
    title = 'Distribution of Creatinine Levels among male patients without kidney failure (Values < 30 mg/dL)'
    path = 'Output/male_non_kidneyF_creatinine_histogram_filtered_log.png'
    plot(male, title, path)

    female = filtered_data[filtered_data['GENDER'] == 'F']
    title = 'Distribution of Creatinine Levels among female patients without kidney failure (Values < 30 mg/dL)'
    path = 'Output/female_non_kidneyF_creatinine_histogram_filtered_log.png'
    plot(female, title, path)


file_path = 'mimic-iii-clinical-database-1.4/DIAGNOSES_ICD.csv.gz'
diagnoses = pd.read_csv(file_path, compression='gzip')
admissions = pd.read_csv('mimic-iii-clinical-database-1.4/ADMISSIONS.csv.gz', compression='gzip')
lab_event = pd.read_csv('mimic-iii-clinical-database-1.4/LABEVENTS.csv.gz', compression='gzip')
patients = pd.read_csv('mimic-iii-clinical-database-1.4/PATIENTS.csv.gz', compression='gzip')

icd_codes = ['5849', '5856', '586', 'N17', 'N186', 'N19']

# Filter rows where the 'ICD9_CODE' column matches any of the codes in the list
kidneyf_diagnoses = diagnoses[diagnoses['ICD9_CODE'].isin(icd_codes)]

# Merge with admissions to get patient data
kidneyf_patients = pd.merge(kidneyf_diagnoses, admissions, on=['SUBJECT_ID', 'HADM_ID'], how='left')
# kidneyf_patients = kidneyf_patients.drop_duplicates(subset=['SUBJECT_ID'])
kidneyf_patients['ADMITTIME'] = pd.to_datetime(kidneyf_patients['ADMITTIME'])
kidneyf_patients['DISCHTIME'] = pd.to_datetime(kidneyf_patients['DISCHTIME'])


non_kidneyf_patients = admissions[~admissions['SUBJECT_ID'].isin(kidneyf_patients['SUBJECT_ID'])]
# non_kidneyf_patients = non_kidneyf_patients.drop_duplicates(subset=['SUBJECT_ID'])

# Find kidney failure patients whose creatinine levels were tested
creatinine_itemids = [50912]
all_creatinine_tests = lab_event[lab_event['ITEMID'].isin(creatinine_itemids)]

kidneyf_creatinine_tests = all_creatinine_tests[
    (all_creatinine_tests['SUBJECT_ID'].isin(kidneyf_patients['SUBJECT_ID']))
]

non_kidneyf_creatinine_tests = all_creatinine_tests[
    ~all_creatinine_tests['SUBJECT_ID'].isin(kidneyf_patients['SUBJECT_ID'])
]

find_creatinine_kidneyf(kidneyf_patients, kidneyf_creatinine_tests, patients)
find_creatinine_non_kidneyf(non_kidneyf_patients, non_kidneyf_creatinine_tests, patients)



