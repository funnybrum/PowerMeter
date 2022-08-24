IN_FILE_NAME = "Timeseries_42.605_23.482_SA2_3kWp_crystSi_14_17deg_7deg_2020_2020.csv"
FIRST_LINE = 10  # zero-based line index that contains the headers
LOOK_AROUND_DAYS = 7
OUTPUT_FILE = "avg_power.csv"

import csv

output_data = []


class DataTracker:
    def __init__(self, date):
        self.date = date
        self.power_points = []

    def get_min(self):
        return min(self.power_points)

    def get_max(self):
        return max(self.power_points)

    def get_date(self):
        return self.date

    def add_power_point(self, power_point):
        self.power_points.append(int(float(power_point)))


with open(IN_FILE_NAME, newline='') as csv_file:
    for i in range(0, FIRST_LINE):
        csv_file.readline()

    reader = csv.DictReader(csv_file)
    for row in reader:
        if not row['time'].startswith('2020'):
            continue
        output_data.append(DataTracker(row['time']))


def get_look_around_indexes(pos):
    return [(pos + (i * 24)) % len(output_data) for i in range(-LOOK_AROUND_DAYS, LOOK_AROUND_DAYS+1)]


with open(IN_FILE_NAME, newline='') as csv_file:
    for i in range(0, FIRST_LINE):
        csv_file.readline()

    reader = csv.DictReader(csv_file)
    pos = -1
    for row in reader:
        if not row['time'].startswith('2020'):
            continue

        pos += 1
        power = row['P']
        look_around_indexes = get_look_around_indexes(pos)

        for i in look_around_indexes:
            output_data[i].add_power_point(power)

with open(OUTPUT_FILE, 'w', newline='') as csv_file:
    writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['time', 'min_power', 'max_power'])

    for entry in output_data:
        writer.writerow([entry.get_date(), entry.get_min(), entry.get_max()])