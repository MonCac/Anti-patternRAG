def load_splitter_by_mode(mode):
    if mode == "java":
        from java_only_splitter import build_chunk
    elif mode == "json":
        from json_only_splitter import build_chunk
    elif mode == "json_java":
        from json_java_splitter import build_chunk
    else:
        raise ValueError(f"Unsupported mode: {mode}")
    return build_chunk
