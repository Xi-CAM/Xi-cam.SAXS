import os
import entrypoints
import numpy as np
from databroker.in_memory import BlueskyInMemoryCatalog


def test_ingestor(tmp_path):
    from fabio.edfimage import EdfImage
    # test data
    data = np.random.random((1000, 1000))
    # write data to test edf
    edf_path = os.path.join(tmp_path, "test.edf")
    print("edf_path:", edf_path)
    EdfImage(data).write(edf_path)

    # get edf ingestor
    edf_ingestor = entrypoints.get_single("databroker.ingestors", "application/x-edf").load()

    # load data into catalog
    document = list(edf_ingestor([edf_path]))
    uid = document[0][1]["uid"]
    catalog = BlueskyInMemoryCatalog()
    # TODO -- change upsert signature to put start and stop as kwargs
    # TODO -- ask about more convenient way to get a BlueskyRun from a document generator
    catalog.upsert(document[0][1], document[-1][1], edf_ingestor, ([edf_path],), {})