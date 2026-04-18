def timestamp_to_filename_fragment(timestamp_text):
    return (
        str(timestamp_text)
        .replace(":", "")
        .replace("-", "")
        .replace(" ", "_")
    )

