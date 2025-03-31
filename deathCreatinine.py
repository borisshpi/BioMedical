import pandas as pd
from compareCreatinine import plot


def plot_dead_creatinine(kidneyf_patients, all_creatinine_tests):
    #Plot creatinine level of patients with kidney failure that died
    deceased_subject_ids = kidneyf_patients[kidneyf_patients['DEATHTIME'].notna()]['SUBJECT_ID'].unique()
    deceased_kidneyf_patients = admissions[admissions['SUBJECT_ID'].isin(deceased_subject_ids)]
    dead_kidneyf_creatinine_tests = all_creatinine_tests[(all_creatinine_tests['SUBJECT_ID'].isin(deceased_kidneyf_patients['SUBJECT_ID']))]

    dead_kidneyf_patients_test = pd.merge(deceased_kidneyf_patients, dead_kidneyf_creatinine_tests, on='SUBJECT_ID', how='inner')
    dead_kidneyf_patients_test['VALUENUM'] = pd.to_numeric(dead_kidneyf_patients_test['VALUENUM'], errors='coerce')
    dead_kidneyf_patients_test = dead_kidneyf_patients_test[dead_kidneyf_patients_test['VALUENUM'] < 30] 
    title = 'Distribution of Creatinine Levels among patients with kidney failure that died (Values < 30 mg/dL)'
    path = 'Output/kidneyF_dead_creatinine.png'
    plot(dead_kidneyf_patients_test, title, path)


def plot_alive_creatinine(kidneyf_patients, all_creatinine_tests):
    #Plot creatinine level of patients with kidney failure that did not die
    alive_kidneyf_patients = kidneyf_patients[kidneyf_patients['DEATHTIME'].isna()]
    # alive_kidneyf_patients = alive_kidneyf_patients.drop_duplicates(subset=['SUBJECT_ID'])

    alive_kidneyf_creatinine_tests = all_creatinine_tests[(all_creatinine_tests['SUBJECT_ID'].isin(alive_kidneyf_patients['SUBJECT_ID']))]
    alive_kidneyf_patients_test = pd.merge(alive_kidneyf_patients, alive_kidneyf_creatinine_tests, on='SUBJECT_ID', how='inner')
    alive_kidneyf_patients_test['VALUENUM'] = pd.to_numeric(alive_kidneyf_patients_test['VALUENUM'], errors='coerce')
    alive_kidneyf_patients_test = alive_kidneyf_patients_test[alive_kidneyf_patients_test['VALUENUM'] < 30] 
    title = 'Distribution of Creatinine Levels among patients with kidney failure that did not die (Values < 30 mg/dL)'
    path = 'Output/kidneyF_alive_creatinine.png'
    plot(alive_kidneyf_patients_test, title, path)



file_path = 'mimic-iii-clinical-database-1.4/DIAGNOSES_ICD.csv.gz'
diagnoses = pd.read_csv(file_path, compression='gzip')
admissions = pd.read_csv('mimic-iii-clinical-database-1.4/ADMISSIONS.csv.gz', compression='gzip')
lab_event = pd.read_csv('mimic-iii-clinical-database-1.4/LABEVENTS.csv.gz', compression='gzip')

icd_codes = ['5849', '5856', '586', 'N17', 'N186', 'N19']
kidneyf_diagnoses = diagnoses[diagnoses['ICD9_CODE'].isin(icd_codes)]

kidneyf_patients = pd.merge(kidneyf_diagnoses, admissions, on=['SUBJECT_ID', 'HADM_ID'], how='left')
kidneyf_patients['ADMITTIME'] = pd.to_datetime(kidneyf_patients['ADMITTIME'])
kidneyf_patients['DISCHTIME'] = pd.to_datetime(kidneyf_patients['DISCHTIME'])
kidneyf_patients['DEATHTIME'] = pd.to_datetime(kidneyf_patients['DEATHTIME'])

creatinine_itemids = [50912]
all_creatinine_tests = lab_event[lab_event['ITEMID'].isin(creatinine_itemids)]

plot_alive_creatinine(kidneyf_patients, all_creatinine_tests)
plot_dead_creatinine(kidneyf_patients, all_creatinine_tests)

