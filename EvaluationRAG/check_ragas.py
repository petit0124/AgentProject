try:
    import ragas.metrics
    print("Available metrics in ragas.metrics:")
    for item in dir(ragas.metrics):
        if not item.startswith("_"):
            print(item)
except ImportError as e:
    print(f"Error importing ragas.metrics: {e}")
