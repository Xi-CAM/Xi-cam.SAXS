import os
import entrypoints
import numpy as np


def test_edf_ingestor(tmp_path):
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

    # TODO: actually do some assertions in here (assert the keys are correct in the descriptor)
    #  (assert data is image) ...