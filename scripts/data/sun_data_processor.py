IN_FILE_NAME = "Timeseries_42.605_23.482_SA2_3kWp_crystSi_14_17deg_7deg_2020_2020.csv"
FIRST_LINE = 10  # zero-based line index that contains the headers
LOOK_AROUND_DAYS = 7  # 14 for daily drops calculator
OUTPUT_FILE = "avg_power.csv"

import csv

from scipy.interpolate import CubicSpline, interp1d


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

exit(1)

drops = []

for month in range(1, 13):
    diffs = []
    # print("=========== month %s ===========" % month)
    for entry in output_data:
        if entry.get_date().startswith("2020%02d" % month):
            if entry.get_min() > 100 and entry.get_max() > 100:
                diffs.append(100 * entry.get_min() / entry.get_max())

    diffs = sorted(diffs)

    # for p in [1, 2, 5, 10, 20, 50, 80, 90, 95, 98, 99]:
    #     index = int(len(diffs) * p / 100)
    #     print("P%s = %s" % (p, diffs[index]))

    drops.append(int(diffs[int(len(diffs) * 98 / 100)]))

days = [i for i in range(15, 365, 30)]
days.insert(0, 0)
days.append(365)

drops.insert(0, drops[0])
drops.append(drops[len(drops)-1])

# print(days)
print(drops)

# Patched a bit to be smoother
drops = [13, 13, 13, 13, 13, 18, 22, 31, 50, 55, 12, 12, 12, 12]

cs = interp1d(days, drops)
# min_sun_power = max(0, int(cs(target_y)))
daily_drops = [int(cs(i)) for i in range(1, 366)]

print(daily_drops)
