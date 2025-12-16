import os
import re
import pandas as pd
import zipfile
import tempfile

from pprint import pprint

class projectData:
    def __init__(self, path):
        self.path = path
        self.files = list()
        self.master = pd.DataFrame()
        self.date_mismatches = list()
        self.RINchecks = list()
        self.operatorChecks = list()

        self.reorgSheets = dict()

        # self.date_mismatches = self.checkDateConsistency()

        self.use_cols = ["COUNT", "EASTING", "NORTHING", "OPER", "DATE", "TIME", "RIN", "CN", "H380", "SNR", "NSAT", "GDATE",
                    "GTIME"]
        self.pattern = r'(?<![0-9])(?:\d{4}|\d{2})-\d{2}-\d{2}(?![0-9])'

    def findShotFiles(self):
        seen_basenames = set()  # Track basenames to avoid duplicates
        csvs = list()
        zips = list()

        for root, dirs, files in os.walk(self.path):
            for file in files:
                # Check for CSV shot files
                if "shots" in file.lower() and ("circuit" not in file.lower()) and file.endswith('.csv'):
                    basename = os.path.basename(file)
                    if basename not in seen_basenames:
                        self.files.append(os.path.join(root, file))
                        seen_basenames.add(basename.strip(".csv"))
                        csvs.append(basename)

                # Check for zip files and walk through them
                elif file.endswith('.zip'):
                    zip_path = os.path.join(root, file)
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            for zip_info in zip_ref.namelist():
                                # Check if the file in the zip is a shot CSV file
                                if "shots" in zip_info.lower() and zip_info.endswith('.csv'):
                                    basename = os.path.basename(zip_info)
                                    if basename not in seen_basenames:
                                        # Store the zip path and the file within it
                                        self.files.append(f"{zip_path}::{zip_info}")
                                        seen_basenames.add(basename)
                    except (zipfile.BadZipFile, PermissionError) as e:
                        print(f"Warning: Could not read zip file {zip_path}: {e}")

        print(f"Found {len(seen_basenames)} files")

    def compileMaster(self):

        master = None

        for idx, sf in enumerate(self.files):
            # Check if the file is from a zip (contains '::')
            if '::' in sf:
                zip_path, file_in_zip = sf.split('::')

                # Extract to temporary file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    with zip_ref.open(file_in_zip) as source:
                        # Create temporary file
                        with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.csv') as temp_file:
                            temp_file.write(source.read())
                            temp_path = temp_file.name

                try:
                    # Read from temporary file
                    df = pd.read_csv(temp_path)
                    file_name = os.path.basename(file_in_zip)
                finally:
                    # Delete temporary file
                    os.unlink(temp_path)
            else:
                # Regular file path
                df = pd.read_csv(sf)
                file_name = os.path.basename(sf)

            # Extract date from filename
            dates = re.findall(self.pattern, file_name)
            df.insert(0, "FILE_DATE", dates[0] if dates else "")

            # Add source file column
            filecol = [file_name] * len(df)
            df.insert(0, "SOURCE_FILE", filecol)

            # Build master dataframe
            if idx == 0:
                master = df
            else:
                master = pd.concat([master, df], ignore_index=True)

        self.master = master.copy(deep=True)
        self.master.insert(0, "DATETIME", pd.to_datetime(self.master["DATE"] + ' ' + self.master["TIME"]))

        # master = pd.read_csv(self.files[0])
        # dates = re.findall(self.pattern, os.path.basename(self.files[0]))
        #
        # if dates:
        #     master.insert(0, "FILE_DATE", dates[0])
        # else:
        #     master.insert(0, "FILE_DATE", "")
        #
        # filecol = [os.path.basename(self.files[0])] * len(master)
        # master.insert(0, "SOURCE_FILE", filecol)
        #
        # for sf in self.files[1:]:
        #     df = pd.read_csv(os.path.join(self.path, sf))
        #     dates = re.findall(self.pattern, sf)
        #
        #     if dates:
        #         df.insert(0, "FILE_DATE", dates[0])
        #     else:
        #         df.insert(0, "FILE_DATE", "")
        #
        #     filecol = [os.path.basename(sf)] * len(df)
        #     df.insert(0, "SOURCE_FILE", filecol)
        #
        #     master = pd.concat([master, df], ignore_index=True)
        #
        # self.master = master.copy(deep=True)
        # self.master.insert(0, "DATETIME", pd.to_datetime(self.master["DATE"] + ' ' + self.master["TIME"]))

    def checkDateConsistency(self):
        self.date_mismatches = list()

        for dt in self.master["FILE_DATE"].unique():

            sub_df = self.master[self.master["FILE_DATE"] == dt]

            # Check if file_date matches any of the dates in the data
            sub_dates = sub_df["DATE"].unique()

            if len(sub_dates) > 1 and dt in sub_dates:
                self.date_mismatches.append({
                    'file': sub_df['SOURCE_FILE'].iloc[0],
                    'file_date': dt,
                    'data_dates': sub_df["DATE"].unique().tolist()
                })

    def checkOperator(self):

        oper_mismatches = []

        for file in self.master["SOURCE_FILE"].unique():

            filedf = self.master[self.master["SOURCE_FILE"] == file]

            if len(filedf["OPER"].unique()) > 1:

                opers = filedf["OPER"].unique()
                opers = [oper[:oper.find("@")] for oper in opers]

                oper_mismatches.append({
                    "file": file,
                    "operators": opers
                })

        if oper_mismatches:
            return oper_mismatches

        return False


    def checkRIN(self):

        rin_mismatches = []

        for file in self.master["SOURCE_FILE"].unique():

            filedf = self.master[self.master["SOURCE_FILE"] == file]

            if len(filedf["RIN"].unique()) > 1:

                rins = filedf["RIN"].unique()

                rin_mismatches.append({
                    "file": file,
                    "RINs": rins
                })

        if rin_mismatches:
            return rin_mismatches

        return False

    def genReport(self):
        pass

    def reorgSheets(self):

        for date in self.master["FILE_DATE"].unique():
            sub_df = self.master[self.master["FILE_DATE"] == date]
            sub_df = sub_df.drop(columns=["SOURCE_FILE", "DATETIME", "FILE_DATE"])

            for oper in sub_df["OPER"].unique():

                oper_df = sub_df[sub_df["OPER"] == oper]
                name = f"shots_{oper}_{date}.csv"

                self.exportReorgSheets[name] = oper_df


    def exportReorgSheets(self, path):

        if not self.exportReorgSheets:

            self.reorgSheets()

        for name, df in self.reorgSheets.items():

            out_path = os.path.join(path, name)
            df.to_csv(out_path, index=False)

        print(f"Reorganized {len(self.files)} into {len(self.reorgSheets)} files.")


def main():
    path = r"Z:\Shared\ActiveProjects\25844 - Woodard and Curran - Jackpile Uranium Mine - New Mexico, USA - 2025\03 - Field Data\0- Original ZIP data from field"

    project = projectData(path)
    project.findShotFiles()
    project.compileMaster()
    project.checkDateConsistency()

    # project.exportReorgSheets(r"E:\JGS\Willowstick\Development\Data Validation\Jackpile Reorg")

    pprint(project.checkOperator())
    pprint(project.checkRIN())
    pprint(project.date_mismatches)


if __name__ == "__main__":

    main()