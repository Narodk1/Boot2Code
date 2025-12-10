from agent_backend import interpret_json, read_stream_response


if __name__ == "__main__":
    stream_response = interpret_json("sonalyse_advisor/dps_analysis_pi3_exemple.json", "sonalyse_advisor/context.txt")
    read_stream_response(stream_response)
