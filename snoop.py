import pandas as pd
import glob
import os

pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 1000)

def read_all():
    folder_path = "mimic-iii-clinical-database-1.4" 
    csv_gz_files = glob.glob(os.path.join(folder_path, '*.csv.gz'))

    if not csv_gz_files:
        print("No .csv.gz files found in the directory.")

    for file in csv_gz_files:
        try:
            df = pd.read_csv(file, compression='gzip')
            print(f"\nContents of file: {os.path.basename(file)}")
            print(df.head())
        except Exception as e:
            print(f"Error reading {file}: {e}")

def find_kidneyF():
    diagnoses = pd.read_csv('mimic-iii-clinical-database-1.4/DIAGNOSES_ICD.csv.gz', compression='gzip')

    kidney_failure_icd_codes = ['5849', '5856', '586']

    kidney_failure_patients = diagnoses[diagnoses['ICD9_CODE'].isin(kidney_failure_icd_codes)]

    print(kidney_failure_patients)

    icd_code_counts = kidney_failure_patients.groupby('ICD9_CODE')['SUBJECT_ID'].nunique()
    print("Number of patients per kidney failure ICD code:")
    print(icd_code_counts)

def kidney_icd():
    icd_descriptions = pd.read_csv('mimic-iii-clinical-database-1.4/D_ICD_DIAGNOSES.csv.gz', compression='gzip')

    keywords = ['renal failure', 'acute kidney failure', 'end-stage renal', 'dialysis', 'kidney failure']
    exclude = ['Iridodialysis', 'retinal dialysis', 'ocular', 'testing']

    pattern = '|'.join(keywords)
    exclude_pattern = '|'.join(exclude)

    renal_failure_codes = icd_descriptions[
        icd_descriptions['LONG_TITLE'].str.contains(pattern, case=False, na=False) &
        ~icd_descriptions['LONG_TITLE'].str.contains(exclude_pattern, case=False, na=False)
    ]

    print(renal_failure_codes)
    output_file = 'filtered_dialysis_terms.csv'
    renal_failure_codes[['ICD9_CODE', 'LONG_TITLE']].to_csv(output_file, index=False)

def compare_icd_patients():
    all_icds = pd.read_csv('filtered_dialysis_terms.csv')
    all_icds = all_icds['ICD9_CODE'].astype(str).unique()

    data = {'ICD9_CODE': ['5849', '5856', '586']}
    lim_icd_df = pd.DataFrame(data)
    lim_icd_df = lim_icd_df['ICD9_CODE'].astype(str).unique()

    diagnoses = pd.read_csv('mimic-iii-clinical-database-1.4/DIAGNOSES_ICD.csv.gz', compression='gzip')
    diagnoses['ICD9_CODE'] = diagnoses['ICD9_CODE'].astype(str)
    diagnoses['SUBJECT_ID'] = diagnoses['SUBJECT_ID'].astype(str)

    filtered_diagnoses = diagnoses[diagnoses['ICD9_CODE'].isin(all_icds)]
    first_occurrence = filtered_diagnoses.sort_values(by=['SUBJECT_ID', 'ICD9_CODE']).drop_duplicates(subset=['SUBJECT_ID'], keep='first')
    patient_counts = first_occurrence['ICD9_CODE'].value_counts().reset_index()
    patient_counts.columns = ['ICD9_CODE', 'unique_patient_count']
    print("In total there are " + str(patient_counts['unique_patient_count'].astype(int).sum()) + " patients for alternative 2")

    filtered_diagnoses = diagnoses[diagnoses['ICD9_CODE'].isin(lim_icd_df)]
    first_occurrence = filtered_diagnoses.sort_values(by=['SUBJECT_ID', 'ICD9_CODE']).drop_duplicates(subset=['SUBJECT_ID'], keep='first')
    patient_counts = first_occurrence['ICD9_CODE'].value_counts().reset_index()
    patient_counts.columns = ['ICD9_CODE', 'unique_patient_count']
    print(patient_counts)
    print("In total there are " + str(patient_counts['unique_patient_count'].astype(int).sum()) + " patients for alternative 1")

def creatinine_code():
    lab_items = pd.read_csv('mimic-iii-clinical-database-1.4/D_LABITEMS.csv.gz', compression='gzip')

    creatinine_tests = lab_items[lab_items['ITEMID'].isin([50912, 1525])]
    print(creatinine_tests)

    creatinine_ids = lab_items[
        lab_items['LABEL'].str.contains('creatinine', case=False, na=False)
    ]
    print(creatinine_ids)

# read_all()
# find_kidneyF()
# kidney_icd()
# compare_icd_patients()
# creatinine_code()