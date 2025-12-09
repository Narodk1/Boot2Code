from agent_backend import interpret_json, read_stream_response


if __name__ == "__main__":
    stream_response = interpret_json("./dps_analysis_pi3_exemple.json", "./context.txt")
    read_stream_response(stream_response)
