gen:
	PYTHONPATH=internal python3 internal/gen/cfn2pkl.py cfnjson .
	pkl eval -f json internal/gen/test.pkl