"""
Test indexer functionality.
"""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.indexer import LogIndexer

OPENSTACK_SAMPLE_LOG = """
2017-05-16 00:00:00.008 25746 INFO nova.osapi_compute.wsgi.server [req-38101a0b-2096-447d-96ea-a692162415ae 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2477829
2017-05-16 00:00:00.272 25746 INFO nova.osapi_compute.wsgi.server [req-9bc36dd9-91c5-4314-898a-47625eb93b09 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2577181
2017-05-16 00:00:01.551 25746 INFO nova.osapi_compute.wsgi.server [req-55db2d8d-cdb7-4b4b-993b-429be84c0c3e 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2731631
2017-05-16 00:00:01.813 25746 INFO nova.osapi_compute.wsgi.server [req-2a3dc421-6604-42a7-9390-a18dc824d5d6 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2580249
2017-05-16 00:00:03.091 25746 INFO nova.osapi_compute.wsgi.server [req-939eb332-c1c1-4e67-99b8-8695f8f1980a 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2727931
2017-05-16 00:00:03.358 25746 INFO nova.osapi_compute.wsgi.server [req-b6a4fa91-7414-432a-b725-52b5613d3ca3 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2642131
2017-05-16 00:00:04.789 25746 INFO nova.osapi_compute.wsgi.server [req-bbfc3fb8-7cb3-4ac8-801e-c893d1082762 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.4256971
2017-05-16 00:00:05.060 25746 INFO nova.osapi_compute.wsgi.server [req-31826992-8435-4e03-bc09-ba9cca2d8ef9 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2661140
2017-05-16 00:00:06.321 25746 INFO nova.osapi_compute.wsgi.server [req-7160b3e7-676b-498f-b147-7759d8eaea76 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2563808
2017-05-16 00:00:06.584 25746 INFO nova.osapi_compute.wsgi.server [req-e46f1fc1-61ce-4673-b3c7-f8bd94554273 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2580891
2017-05-16 00:00:07.864 25746 INFO nova.osapi_compute.wsgi.server [req-546e2e6a-b85e-434a-91dc-53a0a9124a4f 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2733629
2017-05-16 00:00:08.137 25746 INFO nova.osapi_compute.wsgi.server [req-e2c35e53-06d3-4feb-84b9-705c94d40e5b 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2694771
2017-05-16 00:00:09.411 25746 INFO nova.osapi_compute.wsgi.server [req-ce9c8a59-c9ba-43b1-9735-318ceabc9216 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2692339
2017-05-16 00:00:09.692 25746 INFO nova.osapi_compute.wsgi.server [req-e1da47c6-0f46-4ce8-940c-05397a5fab9e 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2777061
2017-05-16 00:00:12.782 25746 INFO nova.osapi_compute.wsgi.server [req-9dac2436-7927-4e4d-9db0-fe35a2bf6ce3 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.5215032
2017-05-16 00:00:13.954 25746 INFO nova.osapi_compute.wsgi.server [req-f456fc92-3d52-4371-b6ce-70e1925cbe54 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.3821654
2017-05-16 00:00:14.227 25746 INFO nova.osapi_compute.wsgi.server [req-7c98c92e-959e-4cac-89d3-1a9b5683be39 113d3a99c3da401fbd62cc2caa5b96d2 54fadb412c4e40cdbaed9335e4c35a9e - - -] 10.11.10.1 "GET /v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.2691371
"""

def test_tokenizer_whitespace():
    """Test simple tokenizer in indexer."""
    indexer = LogIndexer(method="simple", split_method="whitespace")
    tokens = indexer._tokenize(OPENSTACK_SAMPLE_LOG)
    expected_tokens = [
        "2017-05-16", 
        "00:00:00.008", 
        "25746", 
        "info", 
        "nova.osapi_compute.wsgi.server", 
        "req-38101a0b-2096-447d-96ea-a692162415ae", 
        "113d3a99c3da401fbd62cc2caa5b96d2",
        "54fadb412c4e40cdbaed9335e4c35a9e", 
        "get", 
        "/v2/54fadb412c4e40cdbaed9335e4c35a9e/servers/detail", 
        "http/1.1", 
        "status", 
        "200", 
        "1893", 
        "0.2777061"
    ]
    for token in expected_tokens:
        assert token in tokens, f"Expected token '{token}' not found in tokens"

    absent_tokens = [
        "INFO", 
        "time:", 
        "len:", 
    ]

    for token in absent_tokens:
        assert token not in tokens, f"Unexpected token '{token}' found in tokens"

def test_tokenizer_nonalphanumeric():
    """Test advanced tokenizer in indexer."""
    indexer = LogIndexer(method="simple", split_method="nonalphanumeric")
    tokens = indexer._tokenize(OPENSTACK_SAMPLE_LOG)

    expected_tokens = [
        "2017", 
        "05", 
        "16", 
        "00", 
        "00", 
        "00", 
        "008", 
        "25746", 
        "info", 
        "nova", 
        "osapi_compute", 
        "wsgi", 
        "server", 
        "req", 
        "38101a0b", 
        "2096", 
        "447d", 
        "96ea", 
        "a692162415ae", 
        "113d3a99c3da401fbd62cc2caa5b96d2",
        "54fadb412c4e40cdbaed9335e4c35a9e", 
        "get", 
        "v2", 
        "54fadb412c4e40cdbaed9335e4c35a9e", 
        "servers", 
        "detail", 
        "http", 
        "1", 
        "1", 
        "status", 
        "200", 
        "1893", 
        "0", 
        "2777061"
    ]

    for token in expected_tokens:
        assert token in tokens, f"Expected token '{token}' not found in tokens"

    absent_tokens = [
        ":", 
        "-", 
        "[", 
        "]", 
        "\"", 
        "/", 
        ".", 
        ",", 
    ]
    for token in absent_tokens:
        assert token not in tokens, f"Unexpected token '{token}' found in tokens"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])