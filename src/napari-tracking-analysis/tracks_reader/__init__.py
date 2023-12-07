import gzip
import json
from typing import List, Any
import pandas as pd
from napari_tracking_analysis import utils
import numpy as np


def get_reader(path: str) -> List[str]:
    """
    DataType = Any  # usually something like a numpy array, but varies by layer
    LayerAttributes = dict
    SingleWriterFunction = Callable[[str, DataType, LayerAttributes], List[str]]
    """
    # If we recognize the format, we return the actual reader function
    if isinstance(path, str) and path.endswith(".tracks"):
        return track_stats_reader
    # otherwise we return None.
    return None


def track_stats_reader(path: str):
    with gzip.open(path, 'rb') as f:
        output_gz = f.read()
        output = output_gz.decode('utf-8')
        output = json.loads(output)

    print(output.keys())
    all_tracks = pd.read_json(output["all_tracks"])
    all_meta = pd.read_json(output["all_meta"])
    tracking_params = output["tracking_params"]
    metadata = {
        "all_tracks": all_tracks,
        "all_meta": all_meta,
        "tracking_params": tracking_params
    }
    attributes = output["napari_tracks_properties"]
    if 'features' in attributes:
        attributes.pop('features')
    print(attributes.keys())
    attributes["metadata"] = metadata
    track_header = ['track_id', 'frame', 'y', 'x']
    track_meta_header = ['track_id', 'length',
                         'intensity_max', 'intensity_mean', 'intensity_min']

    tracks, properties, track_meta = utils.pd_to_napari_tracks(all_tracks,
                                                               track_header,
                                                               track_meta_header)
    attributes["properties"] = properties
    # print(type(attributes))
    layer_data = (tracks, attributes, 'tracks')
    if isinstance(layer_data[1], dict):
        print("attribute is dict")
    else:
        print("attribute is not a  dict")
    return [layer_data]


class NTracksDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        _decodec_obj = {}
        for k, v in dct.items():
            if k.strip().endswith("_df"):
                _decodec_obj[k] = pd.read_json(v)
            else:
                _decodec_obj[k] = v
        return _decodec_obj


def state_reader(path: str) -> dict:
    with gzip.open(path, 'rb') as f:
        data = f.read().decode('utf-8')
        data = json.loads(data, cls=NTracksDecoder)
        return data
    return None


def main_test(path):
    return state_reader(path=path)


if __name__ == "__main__":
    path = "D:/Data/tracking_test/DYNC1H1_photobleaching/Tracking/new_state_tracks.tracks"
    data = main_test(path)

    def print_dict_keys(dct, tab=""):
        for k, v in dct.items():
            print(f"{tab}{k}", type(v))
            if isinstance(v, dict):
                print_dict_keys(v, tab=tab+"\t")
    if (data):
        # print(data['tracking']['tracks_df'].head())
        print_dict_keys(data)
