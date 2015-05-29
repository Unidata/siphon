import os.path
import vcr


def get_recorder(test_file_path):
    return vcr.VCR(cassette_library_dir=os.path.join(os.path.dirname(test_file_path),
                                                     'fixtures'))
