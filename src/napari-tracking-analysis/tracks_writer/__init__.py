import gzip
import json
from typing import Any, List
import numpy as np
import pandas as pd
import warnings


class NTracksEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.DataFrame):
            return obj.to_json()
        return json.JSONEncoder.default(self, obj)


def track_stats_writer(path: str, data: Any, attributes: dict) -> List[str]:
    """
    DataType = Any  # usually something like a numpy array, but varies by layer
    LayerAttributes = dict
    SingleWriterFunction = Callable[[str, DataType, LayerAttributes], List[str]]
    """
    print(attributes.keys())
    output = {
        "all_tracks": attributes['metadata']['all_tracks'],
        "all_meta": attributes['metadata']['all_meta'],
        "tracking_params": attributes['metadata']["tracking_params"]
    }
    attributes.pop('metadata')
    attributes.pop('features')
    output['napari_tracks_properties'] = attributes
    with gzip.open(path, 'wb') as f:
        f.write(json.dumps(output, cls=NTracksEncoder).encode('utf-8'))

    return [path]


def state_write(path: str, app_state: object) -> str:
    """
        from AppState Save 
        self._data = dict()
    """
    if not hasattr(app_state, '_data'):
        warnings.warn("state object is invalid! nothing to save returning..")
        return None

    data = app_state._data
    with gzip.open(path, 'wb') as f:
        f.write(json.dumps(data, cls=NTracksEncoder).encode('utf-8'))

    return path
