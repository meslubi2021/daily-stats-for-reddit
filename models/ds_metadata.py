import uuid
from datetime import datetime, time, timezone

class DatasetMetadata:
    def __init__(self, date = None, dataset_comments_count = 0):
        self.date = date
        self._dataset_timestamp = int(datetime.combine(date, time.min).replace(tzinfo=timezone.utc).timestamp())
        self._dataset_id = str(uuid.uuid1())
        self._dataset_num_comments = dataset_comments_count

    def add_num_comments(self, num_comments):
        self._dataset_num_comments += num_comments
    
    def asdict(self):
        return {
            '_dataset_id': self._dataset_id, 
            '_dataset_timestamp': self._dataset_timestamp, 
            '_dataset_num_comments': self._dataset_num_comments,
            '_moon_distribution' : self.date.strftime("%Y%m")
        }