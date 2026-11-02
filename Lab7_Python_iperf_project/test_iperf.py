from parser import parser


def test_iperf_client(client):
    output, error = client

    assert not error, f"Client error: {error}"

    intervals = parser(output)
    assert intervals, "No measurement intervals found"

    print("Intervals:", len(intervals))

    for item in intervals:
        print(
            f"{item['Interval']}: "
            f"Transfer={item['Transfer']:.2f} MBytes, "
            f"Bitrate={item['Bitrate']:.2f} Mbits/sec"
        )

        assert item["Transfer"] > 2, (
            f"Transfer too low: {item['Transfer']} MBytes"
        )
        assert item["Bitrate"] > 20, (
            f"Bitrate too low: {item['Bitrate']} Mbits/sec"
        )
