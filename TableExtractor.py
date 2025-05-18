import pdfplumber
import pandas as pd
import regex as re

def parse_pdf_schedule(pdf_path):
    """
    Parse a PDF file to extract schedule details into a DataFrame.

    Parameters:
        pdf_path (str): Path to the PDF file.

    Returns:
        pd.DataFrame: Parsed and processed schedule details.
    """
    pdf = pdfplumber.open(pdf_path)

    terminator = False
    dfs = pd.DataFrame()

    for page in pdf.pages:

        tables = page.find_tables()

        schedule = None
        total_hours = None

        for table in tables:
            rows = table.extract()
            name = rows[0][0]
            if name == "Schedule Details":
                schedule = table
            if name == "Total Hours and Statistics":
                total_hours = table
                terminator = True

        if total_hours is None:
            bottom = page.search(r"Generated on.*Page\s*\d+\s*of\s*\d")[0]["top"]
        else:
            bottom = total_hours.bbox[1]

        bbox = list(schedule.bbox)
        bbox[1] = schedule.cells[0][-1] # bottom of "Schedule Details" cell is the "top" of the crop area
        bbox[-1] = bottom               # either the "top" of "Total Hours" or the page footer

        crop = page.crop(bbox)

        # pick a table to use their vertical lines (+ right edge of table)
        explicit_vertical_lines = [ cell[0] for cell in crop.find_tables()[-1].cells ] + [ bbox[2] ]

        rows = crop.extract_table({"explicit_vertical_lines": explicit_vertical_lines})

        df = pd.DataFrame(rows[1:], columns=rows[0])

        dfs = pd.concat([dfs,df], ignore_index=True)

        if terminator is True:
            break

    dfs['Date'] = dfs['Date'].str.extract(r'(\d{2}/\d{2}/\d{4})')

    dfs = dfs.drop(columns=["Report times","Debrief times", "Block hours", "Duty hours", "Indicators", "Crew"])

    dfs = dfs.rename(columns={'Actual times/Delays': 'Timetable'})

    columns_to_expand = ["Duties", "Details", "Timetable"]

    # Expand columns containing line breaks
    for index, row in dfs.iterrows():
        if "\n" in str(row["Duties"]):  
            for col in columns_to_expand:
                if col in dfs.columns:
                    dfs.at[index, col] = str(row[col]).split("\n")

    # Explode the rows for expanded columns
    dfs = dfs.explode(columns_to_expand, ignore_index=True)

    dfs = dfs.replace(r'\n', ' ', regex=True)

    # Create a flag for next-day arrivals based on superscript ¹
    dfs['NextDayArrival'] = dfs['Timetable'].str.contains(r'\u00B9', regex=True)

    # Clean Timetable: remove 'A', trailing characters after '/', and superscript ¹
    dfs["Timetable"] = dfs["Timetable"].str.replace(r'A', '', regex=True)
    dfs["Timetable"] = dfs["Timetable"].str.replace(r'/.*', '', regex=True)
    dfs["Timetable"] = dfs["Timetable"].str.replace(r'\u00B9', '', regex=True)

    # Add the Position column
    dfs['Position'] = dfs['Details'].apply(lambda x: '*' if '*' in str(x) else '')
    dfs['Details'] = dfs['Details'].str.replace('*', '')  # Remove the * from Details after extracting it
    dfs = dfs[dfs['Details'].str.contains(r'^[A-Za-z]{3} - [A-Za-z]{3}$', regex=True)]

    # Split Details into Origin and Destination
    dfs[['Origin', 'Destination']] = dfs['Details'].str.split(' - ', expand=True)

    # Split Timetable into Departure and Arrival times
    dfs[['DepartureTime', 'ArrivalTime']] = dfs['Timetable'].str.split(' - ', expand=True)

    # Convert Date and time columns into datetime for Departure and Arrival
    dfs['Departure'] = pd.to_datetime(dfs['Date'] + ' ' + dfs['DepartureTime'], format='%d/%m/%Y %H:%M', errors='coerce')
    dfs['Arrival'] = pd.to_datetime(dfs['Date'] + ' ' + dfs['ArrivalTime'], format='%d/%m/%Y %H:%M', errors='coerce')

    # Handle cases where Arrival occurs the next day (either due to time or superscript)
    dfs.loc[dfs['Arrival'] < dfs['Departure'], 'Arrival'] += pd.Timedelta(days=1)
    dfs.loc[dfs['NextDayArrival'], 'Arrival'] += pd.Timedelta(days=1)

    # Drop unnecessary columns
    dfs = dfs.drop(columns=['Date', 'Timetable', 'DepartureTime', 'ArrivalTime', 'Details', 'NextDayArrival'])
    dfs = dfs[['Departure', 'Origin', 'Arrival', 'Destination', 'Duties','Position']]
    dfs = dfs.rename(columns={'Duties': 'Flight number'})

    return dfs
