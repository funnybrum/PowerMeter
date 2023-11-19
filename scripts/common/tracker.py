from lib.telemetry import to_data_line

class Tracker(object):
    def __init__(self, value_key, metric_key, tags, track_min=True, track_max=True, track_avg=True, track_last=True, track_point_count=False):
        self.value_key = value_key
        self.metric_key = metric_key
        self.min = 1000000
        self.max = 0
        self.last = 0
        self.avg = []
        self.track_min = track_min
        self.track_max = track_max
        self.track_avg = track_avg
        self.track_last = track_last
        self.track_point_count = track_point_count
        self.tags = tags

    def reset(self):
        self.min = 1000000
        self.max = 0
        self.last = 0
        self.avg = []

    def track(self, data_dict):
        self.last = data_dict[self.value_key]
        self.max = max(self.max, self.last)
        self.min = min(self.min, self.last)
        self.avg.append(self.last)

    def get_data_lines(self, timestamp=None):
        data_lines = []

        if self.track_min:
            data_lines.append(to_data_line(self.metric_key + ".min", self.min, self.tags, timestamp))
        if self.track_max:
            data_lines.append(to_data_line(self.metric_key + ".max", self.max, self.tags, timestamp))
        if self.track_avg:
            data_lines.append(to_data_line(self.metric_key + ".avg", round(sum(self.avg) / len(self.avg), 1), self.tags, timestamp))
        if self.track_last:
            data_lines.append(to_data_line(self.metric_key, self.last, self.tags, timestamp))
        if self.track_point_count:
            data_lines.append(to_data_line(self.metric_key + ".data_points", len(self.avg), self.tags, timestamp))

        return data_lines

    def get_points_count(self):
        return len(self.avg)

    def get_points_count_data_line(self):
        return to_data_line("point_count", self.get_points_count(), self.tags)
